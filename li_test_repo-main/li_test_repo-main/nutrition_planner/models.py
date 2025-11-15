"""Domain models for the nutrition planner."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class UserProfile:
    """Represents the core information about a user."""

    age: int
    gender: str
    weight_kg: float
    height_cm: float
    activity_level: str
    goal: str
    dietary_preferences: Optional[List[str]] = None

    def normalized_gender(self) -> str:
        return self.gender.strip().lower()

    def normalized_goal(self) -> str:
        return self.goal.strip().lower()


@dataclass(frozen=True)
class NutritionTargets:
    """Caloric and macronutrient targets."""

    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "calories": self.calories,
            "protein_g": self.protein_g,
            "fat_g": self.fat_g,
            "carbs_g": self.carbs_g,
        }


@dataclass(frozen=True)
class Dish:
    """A dish and its nutritional information."""

    name: str
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float
    ingredients: List[str]
    weight: float
    tags: List[str] = field(default_factory=list)

    def scaled(self, factor: float) -> "Dish":
        return Dish(
            name=self.name,
            calories=self.calories * factor,
            protein_g=self.protein_g * factor,
            fat_g=self.fat_g * factor,
            carbs_g=self.carbs_g * factor,
            ingredients=self.ingredients,
            weight=self.weight * factor,
            tags=self.tags,
        )


@dataclass(frozen=True)
class MealComponent:
    """A scaled dish that contributes to a meal."""

    dish: Dish
    portion_factor: float

    def as_dict(self) -> Dict[str, float]:
        scaled_dish = self.dish.scaled(self.portion_factor)
        return {
            "dish_name": self.dish.name,
            "portion_factor": self.portion_factor,
            "calories": scaled_dish.calories,
            "protein_g": scaled_dish.protein_g,
            "fat_g": scaled_dish.fat_g,
            "carbs_g": scaled_dish.carbs_g,
        }


@dataclass(frozen=True)
class Meal:
    """Represents a meal composed of multiple components."""

    name: str
    components: List[MealComponent]

    def totals(self) -> NutritionTargets:
        calories = sum(c.dish.calories * c.portion_factor for c in self.components)
        protein = sum(c.dish.protein_g * c.portion_factor for c in self.components)
        fat = sum(c.dish.fat_g * c.portion_factor for c in self.components)
        carbs = sum(c.dish.carbs_g * c.portion_factor for c in self.components)
        return NutritionTargets(calories=calories, protein_g=protein, fat_g=fat, carbs_g=carbs)

    def as_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "components": [component.as_dict() for component in self.components],
            "totals": self.totals().as_dict(),
        }


@dataclass(frozen=True)
class MealPlan:
    """A daily meal plan for the user."""

    meals: List[Meal]

    def totals(self) -> NutritionTargets:
        calories = sum(meal.totals().calories for meal in self.meals)
        protein = sum(meal.totals().protein_g for meal in self.meals)
        fat = sum(meal.totals().fat_g for meal in self.meals)
        carbs = sum(meal.totals().carbs_g for meal in self.meals)
        return NutritionTargets(calories=calories, protein_g=protein, fat_g=fat, carbs_g=carbs)

    def as_dict(self) -> Dict[str, object]:
        return {
            "meals": [meal.as_dict() for meal in self.meals],
            "totals": self.totals().as_dict(),
        }
