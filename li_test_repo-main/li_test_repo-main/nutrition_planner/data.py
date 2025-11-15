"""Data helpers for the nutrition planner."""

from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from .models import Dish


@dataclass
class DishDatabase:
    """Loads dishes from CSV or JSON files."""

    dishes: List[Dish]

    @classmethod
    def from_csv(cls, path: Path) -> "DishDatabase":
        dishes: List[Dish] = []
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                dishes.append(
                    Dish(
                        name=row["dish_name"],
                        calories=float(row["calories"]),
                        protein_g=float(row["protein"]),
                        fat_g=float(row["fat"]),
                        carbs_g=float(row["carbs"]),
                        ingredients=[ingredient.strip() for ingredient in row["ingredients"].split(";") if ingredient.strip()],
                        weight=float(row.get("weight", 100)),
                        tags=[tag.strip().lower() for tag in row.get("tags", "").split(";") if tag.strip()],
                    )
                )
        return cls(dishes=dishes)

    @classmethod
    def from_json(cls, path: Path) -> "DishDatabase":
        data = json.loads(path.read_text(encoding="utf-8"))
        dishes = [
            Dish(
                name=item["dish_name"],
                calories=float(item["calories"]),
                protein_g=float(item["protein"]),
                fat_g=float(item["fat"]),
                carbs_g=float(item["carbs"]),
                ingredients=item.get("ingredients", []),
                weight=float(item.get("weight", 100)),
                tags=[tag.strip().lower() for tag in item.get("tags", [])],
            )
            for item in data
        ]
        return cls(dishes=dishes)

    def filter_by_tags(self, required: Optional[Iterable[str]] = None) -> List[Dish]:
        if not required:
            return list(self.dishes)
        normalized = {tag.strip().lower() for tag in required}
        return [dish for dish in self.dishes if normalized.issubset({tag.lower() for tag in dish.tags})]


@dataclass
class SyntheticDatasetGenerator:
    """Generates synthetic datasets for testing meal plans."""

    ingredients: List[str]
    base_dishes: List[str]

    def generate_dish_dataset(self, count: int, output_path: Path) -> None:
        """Generate a dish dataset with random macro distributions."""

        fieldnames = ["dish_name", "ingredients", "weight", "calories", "protein", "fat", "carbs", "tags"]
        random.seed(42)
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for index in range(count):
                name = f"{random.choice(self.base_dishes)} {index + 1}"
                ingredients = random.sample(self.ingredients, 3)
                calories = random.randint(250, 600)
                protein = round(calories * random.uniform(0.15, 0.35) / 4.0, 2)
                fat = round(calories * random.uniform(0.20, 0.40) / 9.0, 2)
                carbs = round(calories * random.uniform(0.30, 0.50) / 4.0, 2)
                tags = random.sample(["vegetarian", "low-salt", "low-sugar", "high-fiber"], 2)
                writer.writerow(
                    {
                        "dish_name": name,
                        "ingredients": ";".join(ingredients),
                        "weight": random.randint(150, 320),
                        "calories": calories,
                        "protein": protein,
                        "fat": fat,
                        "carbs": carbs,
                        "tags": ";".join(tags),
                    }
                )
