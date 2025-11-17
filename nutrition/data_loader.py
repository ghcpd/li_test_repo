"""Load and manage dish data for meal planning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

import pandas as pd

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = PACKAGE_ROOT / "data" / "dishes.csv"


@dataclass(frozen=True)
class Dish:
    name: str
    ingredients: List[str]
    weight: float
    calories: float
    protein: float
    fat: float
    carbs: float
    tags: List[str]

    def matches_preferences(self, preferences: Sequence[str]) -> bool:
        if not preferences:
            return True
        normalized = {tag.strip().lower() for tag in self.tags}
        return all(pref in normalized for pref in preferences)

    def as_dict(self) -> dict:
        return {
            "dish_name": self.name,
            "ingredients": ", ".join(self.ingredients),
            "weight": self.weight,
            "calories": self.calories,
            "protein": self.protein,
            "fat": self.fat,
            "carbs": self.carbs,
            "tags": ", ".join(self.tags),
        }


class DishDatabase:
    """Provide convenient access to the dish dataset."""

    def __init__(self, dishes: Iterable[Dish]):
        self._dishes = list(dishes)

    @classmethod
    def load(cls, path: Path | None = None) -> "DishDatabase":
        resolved = Path(path) if path else DEFAULT_DATA_PATH
        if not resolved.exists():
            raise FileNotFoundError(f"Dish dataset not found at {resolved}")
        df = pd.read_csv(resolved)
        dishes = []
        for _, row in df.iterrows():
            ingredients = [part.strip() for part in str(row["ingredients"]).split(";")]
            tags = [part.strip().lower() for part in str(row["tags"]).split(";") if part]
            dishes.append(
                Dish(
                    name=str(row["dish_name"]),
                    ingredients=ingredients,
                    weight=float(row["weight"]),
                    calories=float(row["calories"]),
                    protein=float(row["protein"]),
                    fat=float(row["fat"]),
                    carbs=float(row["carbs"]),
                    tags=tags,
                )
            )
        return cls(dishes)

    def all(self) -> List[Dish]:
        return list(self._dishes)

    def filter_by_preferences(self, preferences: Sequence[str]) -> List[Dish]:
        normalized = [pref.strip().lower() for pref in preferences if pref.strip()]
        return [dish for dish in self._dishes if dish.matches_preferences(normalized)]

    def as_dataframe(self):
        return pd.DataFrame([dish.as_dict() for dish in self._dishes])
