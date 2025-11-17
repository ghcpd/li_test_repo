"""Synthetic data generation utilities for testing."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Iterable

import pandas as pd


TAGS = [
    "vegetarian",
    "vegan",
    "low-carb",
    "gluten-free",
    "high-protein",
    "low-salt",
    "low-sugar",
    "heart-healthy",
]


class SyntheticDataGenerator:
    """Utility methods to generate synthetic dish datasets."""

    @staticmethod
    def generate_dish_dataset(record_count: int, output_path: Path) -> Path:
        if record_count <= 0:
            raise ValueError("record_count must be greater than zero")
        dishes = []
        for index in range(record_count):
            protein = random.uniform(10, 45)
            fat = random.uniform(5, 25)
            carbs = random.uniform(15, 70)
            calories = round(protein * 4 + fat * 9 + carbs * 4)
            dish_tags = ";".join(sorted(random.sample(TAGS, k=random.randint(1, 3))))
            dishes.append(
                {
                    "dish_name": f"Synthetic Dish {index + 1}",
                    "ingredients": ";".join(
                        [
                            f"Ingredient {index + 1}-A",
                            f"Ingredient {index + 1}-B",
                            f"Ingredient {index + 1}-C",
                        ]
                    ),
                    "weight": round(random.uniform(250, 450), 2),
                    "calories": calories,
                    "protein": round(protein, 2),
                    "fat": round(fat, 2),
                    "carbs": round(carbs, 2),
                    "tags": dish_tags,
                }
            )
        df = pd.DataFrame(dishes)
        df.to_csv(output_path, index=False)
        return output_path

    @staticmethod
    def expand_with_preferences(existing_tags: Iterable[str], desired_count: int) -> list[str]:
        available_tags = {tag.strip().lower() for tag in existing_tags}
        needed = desired_count - len(available_tags)
        if needed <= 0:
            return sorted(available_tags)
        additional = [tag for tag in TAGS if tag not in available_tags][:needed]
        return sorted(available_tags.union(additional))
