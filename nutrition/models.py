"""Data models for the nutrition analysis and meal planning system."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass
class UserProfile:
    """Represents basic user information relevant for nutrition analysis."""

    age: int
    height: float
    weight: float
    gender: str
    goal: str
    activity_factor: float = 1.2
    dietary_preferences: Iterable[str] = field(default_factory=list)

    def normalized_gender(self) -> str:
        return self.gender.strip().lower()

    def normalized_goal(self) -> str:
        return self.goal.strip().lower()

    def normalized_preferences(self) -> List[str]:
        return [pref.strip().lower() for pref in self.dietary_preferences]


@dataclass
class Dish:
    """Represents a dish with nutritional information."""

    dish_name: str
    ingredients: List[str]
    weight: float
    calories: float
    protein: float
    fat: float
    carbs: float
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "Dish":
        return cls(
            dish_name=str(payload["dish_name"]),
            ingredients=list(payload.get("ingredients", [])),
            weight=float(payload.get("weight", 0)),
            calories=float(payload.get("calories", 0)),
            protein=float(payload.get("protein", 0)),
            fat=float(payload.get("fat", 0)),
            carbs=float(payload.get("carbs", 0)),
            tags=[str(tag).lower() for tag in payload.get("tags", [])],
        )


@dataclass
class Meal:
    """Represents a meal composed of an individual dish."""

    dish: Dish

    @property
    def calories(self) -> float:
        return self.dish.calories

    @property
    def protein(self) -> float:
        return self.dish.protein

    @property
    def fat(self) -> float:
        return self.dish.fat

    @property
    def carbs(self) -> float:
        return self.dish.carbs

    @property
    def description(self) -> str:
        return self.dish.dish_name


@dataclass
class MealPlan:
    """Aggregate of meals recommended for a day."""

    meals: List[Meal]

    def total_calories(self) -> float:
        return sum(meal.calories for meal in self.meals)

    def total_protein(self) -> float:
        return sum(meal.protein for meal in self.meals)

    def total_fat(self) -> float:
        return sum(meal.fat for meal in self.meals)

    def total_carbs(self) -> float:
        return sum(meal.carbs for meal in self.meals)

    def to_rows(self) -> List[List[object]]:
        rows = [[
            "Meal",
            "Dish",
            "Calories",
            "Protein (g)",
            "Fat (g)",
            "Carbs (g)",
        ]]
        for idx, meal in enumerate(self.meals, start=1):
            rows.append([
                idx,
                meal.description,
                round(meal.calories, 2),
                round(meal.protein, 2),
                round(meal.fat, 2),
                round(meal.carbs, 2),
            ])
        return rows

    def summary(self) -> Dict[str, float]:
        return {
            "calories": round(self.total_calories(), 2),
            "protein": round(self.total_protein(), 2),
            "fat": round(self.total_fat(), 2),
            "carbs": round(self.total_carbs(), 2),
        }

    def describe(self) -> str:
        output = ["Meal Plan:"]
        for idx, meal in enumerate(self.meals, start=1):
            output.append(f"  {idx}. {meal.description} - {meal.calories:.0f} kcal")
        return "\n".join(output)
