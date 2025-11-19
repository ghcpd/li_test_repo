"""Utilities for loading the dish dataset."""

from __future__ import annotations

import json
import os
from typing import Iterable, List

from .models import Dish


def dataset_path() -> str:
    return os.path.join(os.path.dirname(__file__), "data", "dishes.json")


def load_dishes(additional_sources: Iterable[str] | None = None) -> List[Dish]:
    dishes: List[Dish] = []
    sources = [dataset_path()]
    if additional_sources:
        sources.extend(additional_sources)
    for path in sources:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        for entry in payload:
            dishes.append(Dish.from_dict(entry))
    return dishes
