"""Nutrition requirement analysis utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .models import UserProfile


@dataclass
class NutritionTargets:
    calories: float
    protein_grams: float
    fat_grams: float
    carb_grams: float

    def macro_ratios(self) -> Dict[str, float]:
        total = self.protein_grams * 4 + self.fat_grams * 9 + self.carb_grams * 4
        return {
            "protein": (self.protein_grams * 4) / total if total else 0.0,
            "fat": (self.fat_grams * 9) / total if total else 0.0,
            "carbs": (self.carb_grams * 4) / total if total else 0.0,
        }


class NutritionAnalyzer:
    """Analyze caloric needs and macronutrient distribution."""

    GOAL_CALORIE_FACTORS = {
        "weight loss": 0.85,
        "muscle gain": 1.1,
        "maintenance": 1.0,
    }

    GOAL_MACRO_RATIOS = {
        "weight loss": (0.30, 0.30, 0.40),
        "muscle gain": (0.30, 0.25, 0.45),
        "maintenance": (0.25, 0.30, 0.45),
    }

    def __init__(self, user_profile: UserProfile) -> None:
        self.user_profile = user_profile

    def calculate_bmr(self) -> float:
        gender = self.user_profile.normalized_gender()
        if gender not in {"male", "female"}:
            raise ValueError("Gender must be 'male' or 'female'.")
        weight = self.user_profile.weight
        height = self.user_profile.height
        age = self.user_profile.age
        if gender == "male":
            return 10 * weight + 6.25 * height - 5 * age + 5
        return 10 * weight + 6.25 * height - 5 * age - 161

    def calculate_tdee(self) -> float:
        return self.calculate_bmr() * self.user_profile.activity_factor

    def adjusted_calories(self) -> float:
        goal = self.user_profile.normalized_goal()
        factor = self.GOAL_CALORIE_FACTORS.get(goal)
        if factor is None:
            raise ValueError(f"Unsupported goal: {self.user_profile.goal}")
        return self.calculate_tdee() * factor

    def macro_distribution(self) -> Tuple[float, float, float]:
        goal = self.user_profile.normalized_goal()
        ratios = self.GOAL_MACRO_RATIOS.get(goal)
        if ratios is None:
            raise ValueError(f"Unsupported goal: {self.user_profile.goal}")
        return ratios

    def build_targets(self) -> NutritionTargets:
        total_calories = self.adjusted_calories()
        protein_ratio, fat_ratio, carb_ratio = self.macro_distribution()
        protein_calories = total_calories * protein_ratio
        fat_calories = total_calories * fat_ratio
        carb_calories = total_calories * carb_ratio
        protein_grams = protein_calories / 4
        fat_grams = fat_calories / 9
        carb_grams = carb_calories / 4
        return NutritionTargets(
            calories=round(total_calories, 2),
            protein_grams=round(protein_grams, 2),
            fat_grams=round(fat_grams, 2),
            carb_grams=round(carb_grams, 2),
        )

    def summarize(self) -> Dict[str, float]:
        targets = self.build_targets()
        return {
            "calories": targets.calories,
            "protein_grams": targets.protein_grams,
            "fat_grams": targets.fat_grams,
            "carb_grams": targets.carb_grams,
        }
