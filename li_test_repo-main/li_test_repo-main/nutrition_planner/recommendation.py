"""Meal plan recommendation logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from .models import Dish, Meal, MealComponent, MealPlan, NutritionTargets, UserProfile


@dataclass
class MealPlanRecommender:
    """Recommends meal plans based on nutrition targets and available dishes."""

    dishes: Sequence[Dish]

    def recommend(
        self,
        profile: UserProfile,
        targets: NutritionTargets,
        meal_count: int = 3,
        dietary_preferences: Sequence[str] | None = None,
    ) -> MealPlan:
        if meal_count <= 0:
            raise ValueError("Meal count must be positive")

        filtered_dishes = self._filter_dishes(dietary_preferences)
        if not filtered_dishes:
            raise ValueError("No dishes match the provided dietary preferences")

        caloric_per_meal = targets.calories / meal_count
        protein_per_meal = targets.protein_g / meal_count
        fat_per_meal = targets.fat_g / meal_count
        carbs_per_meal = targets.carbs_g / meal_count

        meals: List[Meal] = []
        remaining_targets = NutritionTargets(
            calories=targets.calories,
            protein_g=targets.protein_g,
            fat_g=targets.fat_g,
            carbs_g=targets.carbs_g,
        )

        for index in range(meal_count):
            desired = NutritionTargets(
                calories=max(caloric_per_meal, 1.0),
                protein_g=max(protein_per_meal, 0.1),
                fat_g=max(fat_per_meal, 0.1),
                carbs_g=max(carbs_per_meal, 0.1),
            )
            component = self._best_component(filtered_dishes, desired)
            remaining_meals = meal_count - index
            remaining_targets = NutritionTargets(
                calories=max(remaining_targets.calories - component.dish.calories * component.portion_factor, 0.0),
                protein_g=max(remaining_targets.protein_g - component.dish.protein_g * component.portion_factor, 0.0),
                fat_g=max(remaining_targets.fat_g - component.dish.fat_g * component.portion_factor, 0.0),
                carbs_g=max(remaining_targets.carbs_g - component.dish.carbs_g * component.portion_factor, 0.0),
            )
            caloric_per_meal = remaining_targets.calories / max(remaining_meals - 1, 1)
            protein_per_meal = remaining_targets.protein_g / max(remaining_meals - 1, 1)
            fat_per_meal = remaining_targets.fat_g / max(remaining_meals - 1, 1)
            carbs_per_meal = remaining_targets.carbs_g / max(remaining_meals - 1, 1)
            meals.append(
                Meal(
                    name=f"Meal {index + 1}",
                    components=[component],
                )
            )

        return MealPlan(meals=meals)

    def _filter_dishes(self, preferences: Sequence[str] | None) -> List[Dish]:
        if not preferences:
            return list(self.dishes)
        normalized = {pref.strip().lower() for pref in preferences}
        return [dish for dish in self.dishes if normalized.issubset({tag.lower() for tag in dish.tags})]

    def _best_component(self, dishes: Sequence[Dish], desired: NutritionTargets) -> MealComponent:
        best_score = float("inf")
        best_dish = dishes[0]
        best_factor = 1.0
        for dish in dishes:
            factor = self._portion_factor(dish, desired)
            score = self._score(dish, desired, factor)
            if score < best_score:
                best_score = score
                best_dish = dish
                best_factor = factor
        return MealComponent(dish=best_dish, portion_factor=best_factor)

    def _portion_factor(self, dish: Dish, desired: NutritionTargets) -> float:
        if dish.calories <= 0:
            return 1.0
        factor = desired.calories / dish.calories
        return max(0.5, min(factor, 2.0))

    def _score(self, dish: Dish, desired: NutritionTargets, factor: float) -> float:
        scaled = dish.scaled(factor)
        calorie_diff = abs(desired.calories - scaled.calories)
        protein_diff = abs(desired.protein_g - scaled.protein_g)
        fat_diff = abs(desired.fat_g - scaled.fat_g)
        carbs_diff = abs(desired.carbs_g - scaled.carbs_g)
        return calorie_diff + protein_diff * 4 + fat_diff * 4 + carbs_diff * 3
