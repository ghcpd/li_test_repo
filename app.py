from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from flask import Flask, abort, jsonify, render_template, request


@dataclass(frozen=True)
class ZodiacSign:
    name: str
    slug: str
    date_range: str
    symbol: str
    element: str
    origin: str
    traits: List[str]
    color: str


def _load_zodiac_data(path: Path) -> List[ZodiacSign]:
    with path.open("r", encoding="utf-8") as handle:
        raw_items = json.load(handle)
    return [ZodiacSign(**entry) for entry in raw_items]


def create_app(test_config: Dict | None = None) -> Flask:
    base_dir = Path(__file__).resolve().parent
    data_path = base_dir / "data" / "zodiacs.json"

    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["JSON_SORT_KEYS"] = False

    zodiacs: List[ZodiacSign] = _load_zodiac_data(data_path)
    zodiac_index: Dict[str, ZodiacSign] = {item.slug: item for item in zodiacs}

    if test_config:
        app.config.update(test_config)

    def _matching_signs(query: str | None, element: str | None) -> List[ZodiacSign]:
        filtered = zodiacs
        if element:
            normalized = element.strip().lower()
            filtered = [sign for sign in filtered if sign.element.lower() == normalized]
        if query:
            normalized_query = query.strip().lower()
            filtered = [
                sign
                for sign in filtered
                if normalized_query in sign.name.lower()
                or normalized_query in sign.symbol.lower()
            ]
        return filtered

    @app.route("/")
    def home() -> str:
        elements = sorted({sign.element for sign in zodiacs})
        return render_template("index.html", elements=elements)

    @app.route("/zodiacs", methods=["GET"])
    def list_zodiacs():
        query = request.args.get("q")
        element = request.args.get("element")
        matches = _matching_signs(query, element)
        response = {
            "count": len(matches),
            "zodiacs": [sign.__dict__ for sign in matches],
        }
        return jsonify(response)

    @app.route("/zodiacs/random", methods=["GET"])
    def random_zodiac():
        sign = random.choice(zodiacs)
        return jsonify(sign.__dict__)

    @app.route("/zodiacs/<slug>", methods=["GET"])
    def zodiac_detail(slug: str):
        sign = zodiac_index.get(slug.lower())
        if not sign:
            abort(404, description=f"Zodiac sign '{slug}' was not found.")
        return jsonify(sign.__dict__)

    @app.errorhandler(404)
    def handle_not_found(error):  # type: ignore[override]
        response = {"error": "Not Found", "message": getattr(error, "description", str(error))}
        return jsonify(response), 404

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)
