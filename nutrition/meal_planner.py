"""Meal planning logic that satisfies user nutrition goals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from .analysis import NutritionAnalyzer, UserProfile
from .data_loader import Dish, DishDatabase


@dataclass(frozen=True)
class MealPlan:
    plan_id: int
    meals: List[dict]
    totals: Dict[str, float]


class MealPlanner:
    """Generate meal plan recommendations that align with nutrition targets."""

    def __init__(self, database: DishDatabase, analyzer: NutritionAnalyzer | None = None):
        self.database = database
        self.analyzer = analyzer or NutritionAnalyzer()

    def create_meal_plans(
        self,
        profile: UserProfile,
        alternatives: int = 3,
        analysis: Dict[str, float] | None = None,
    ) -> List[MealPlan]:
        """Create multiple alternative meal plans for the given profile."""

        analysis = analysis or self.analyzer.analyze(profile)
        preferences = profile.normalized_preferences()
        available_dishes = self.database.filter_by_preferences(preferences)
        if not available_dishes:
            raise ValueError(
                "No dishes match the provided dietary preferences. Please update preferences or data set."
            )

        meals_per_day = profile.normalized_meal_count()
        alternatives = max(1, min(alternatives, len(available_dishes)))

        plans: List[MealPlan] = []
        for offset in range(alternatives):
            plan_meals = self._build_plan(
                available_dishes,
                analysis,
                meals_per_day,
                offset,
            )
            totals = self._calculate_totals(plan_meals)
            plans.append(
                MealPlan(
                    plan_id=offset + 1,
                    meals=plan_meals,
                    totals=totals,
                )
            )
        return plans

    def _build_plan(
        self,
        dishes: Iterable[Dish],
        targets: Dict[str, float],
        meals_per_day: int,
        offset: int,
    ) -> List[dict]:
        ordered = list(dishes)
        if ordered:
            offset = offset % len(ordered)
            ordered = ordered[offset:] + ordered[:offset]

        plan: List[dict] = []
        totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
        usage_counts: Dict[str, int] = {dish.name: 0 for dish in ordered}
        for index in range(meals_per_day):
            best_dish = min(
                ordered,
                key=lambda dish: self._score_dish(
                    totals,
                    dish,
                    targets,
                    usage_counts.get(dish.name, 0),
                ),
            )
            totals = self._updated_totals(totals, best_dish)
            plan.append(
                {
                    "meal_number": index + 1,
                    "dish_name": best_dish.name,
                    "ingredients": ", ".join(best_dish.ingredients),
                    "calories": round(best_dish.calories, 2),
                    "protein": round(best_dish.protein, 2),
                    "fat": round(best_dish.fat, 2),
                    "carbs": round(best_dish.carbs, 2),
                    "tags": ", ".join(best_dish.tags),
                }
            )
            usage_counts[best_dish.name] = usage_counts.get(best_dish.name, 0) + 1
        return plan

    def _calculate_totals(self, plan_meals: List[dict]) -> Dict[str, float]:
        totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
        for meal in plan_meals:
            totals["calories"] += meal["calories"]
            totals["protein"] += meal["protein"]
            totals["fat"] += meal["fat"]
            totals["carbs"] += meal["carbs"]
        return {key: round(value, 2) for key, value in totals.items()}

    def _updated_totals(self, totals: Dict[str, float], dish: Dish) -> Dict[str, float]:
        return {
            "calories": totals["calories"] + dish.calories,
            "protein": totals["protein"] + dish.protein,
            "fat": totals["fat"] + dish.fat,
            "carbs": totals["carbs"] + dish.carbs,
        }

    def _score_dish(
        self,
        totals: Dict[str, float],
        dish: Dish,
        targets: Dict[str, float],
        repeat_count: int = 0,
    ) -> float:
        updated = self._updated_totals(totals, dish)
        score = 0.0
        for key in ("calorie_target", "protein_target", "fat_target", "carb_target"):
            target_value = targets[key]
            macro_key = self._macro_key_from_target(key)
            score += abs(updated[macro_key] - target_value)
        # apply a small penalty when repeating dishes to encourage variety
        score += repeat_count * 150
        return score

    @staticmethod
    def _macro_key_from_target(target_key: str) -> str:
        mapping = {
            "calorie_target": "calories",
            "protein_target": "protein",
            "fat_target": "fat",
            "carb_target": "carbs",
        }
        return mapping[target_key]
