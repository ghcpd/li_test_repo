"""Meal plan recommendation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .models import Dish, Meal, MealPlan, UserProfile
from .analyzer import NutritionTargets


@dataclass
class Recommendation:
    plan: MealPlan
    score: float


class MealPlanRecommender:
    """Select meal combinations meeting caloric and macronutrient targets."""

    def __init__(self, dishes: Sequence[Dish]) -> None:
        self.dishes = list(dishes)

    @staticmethod
    def _matches_preferences(dish: Dish, preferences: Iterable[str]) -> bool:
        lowered = [pref.lower() for pref in preferences]
        for pref in lowered:
            if pref and pref not in dish.tags:
                return False
        return True

    def filter_by_preferences(self, preferences: Iterable[str]) -> List[Dish]:
        prefs = [pref for pref in preferences if pref]
        if not prefs:
            return self.dishes
        filtered = [dish for dish in self.dishes if self._matches_preferences(dish, prefs)]
        return filtered or self.dishes

    @staticmethod
    def score_dish(
        dish: Dish,
        target_calories: float,
        target_protein: float,
        target_fat: float,
        target_carbs: float,
    ) -> float:
        calorie_diff = abs(dish.calories - target_calories)
        protein_diff = abs(dish.protein - target_protein) * 4
        fat_diff = abs(dish.fat - target_fat) * 9
        carb_diff = abs(dish.carbs - target_carbs) * 4
        return calorie_diff + protein_diff + fat_diff + carb_diff

    def recommend(
        self,
        user: UserProfile,
        targets: NutritionTargets,
        meals_per_day: int = 3,
        num_options: int = 3,
    ) -> List[MealPlan]:
        if meals_per_day <= 0:
            raise ValueError("meals_per_day must be positive")
        dishes = self.filter_by_preferences(user.normalized_preferences())
        if not dishes:
            raise ValueError("Dish dataset is empty")
        per_meal_calories = targets.calories / meals_per_day
        per_meal_protein = targets.protein_grams / meals_per_day
        per_meal_fat = targets.fat_grams / meals_per_day
        per_meal_carbs = targets.carb_grams / meals_per_day
        scored_dishes = [
            (
                dish,
                self.score_dish(
                    dish,
                    per_meal_calories,
                    per_meal_protein,
                    per_meal_fat,
                    per_meal_carbs,
                ),
            )
            for dish in dishes
        ]
        scored_dishes.sort(key=lambda item: item[1])
        options: List[MealPlan] = []
        if not scored_dishes:
            return options
        for offset in range(min(num_options, len(scored_dishes))):
            meals: List[Meal] = []
            for idx in range(meals_per_day):
                dish = scored_dishes[(offset + idx) % len(scored_dishes)][0]
                meals.append(Meal(dish=dish))
            options.append(MealPlan(meals=meals))
        return options

    @staticmethod
    def summary_for_plan(plan: MealPlan, targets: NutritionTargets) -> dict:
        return {
            "calories_target": round(targets.calories, 2),
            "calories_actual": round(plan.total_calories(), 2),
            "protein_target": round(targets.protein_grams, 2),
            "protein_actual": round(plan.total_protein(), 2),
            "fat_target": round(targets.fat_grams, 2),
            "fat_actual": round(plan.total_fat(), 2),
            "carb_target": round(targets.carb_grams, 2),
            "carb_actual": round(plan.total_carbs(), 2),
        }
