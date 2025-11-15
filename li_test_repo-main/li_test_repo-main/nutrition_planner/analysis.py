"""Nutrition analysis calculations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .models import NutritionTargets, UserProfile


_ACTIVITY_FACTORS: Dict[str, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very active": 1.9,
}

_GOAL_CALORIC_ADJUSTMENT: Dict[str, float] = {
    "weight loss": 0.85,
    "muscle gain": 1.15,
    "maintenance": 1.0,
}

_GOAL_MACRO_RATIOS: Dict[str, Tuple[float, float, float]] = {
    # protein, fat, carbs ratios (of total calories)
    "weight loss": (0.3, 0.25, 0.45),
    "muscle gain": (0.3, 0.25, 0.45),
    "maintenance": (0.25, 0.25, 0.5),
}


@dataclass
class NutritionAnalyzer:
    """Calculates nutrition targets for a user profile."""

    def calculate_bmr(self, profile: UserProfile) -> float:
        weight = profile.weight_kg
        height = profile.height_cm
        age = profile.age
        gender = profile.normalized_gender()
        if gender == "male":
            return 10 * weight + 6.25 * height - 5 * age + 5
        if gender == "female":
            return 10 * weight + 6.25 * height - 5 * age - 161
        raise ValueError("Unsupported gender")

    def activity_factor(self, profile: UserProfile) -> float:
        level = profile.activity_level.strip().lower()
        if level not in _ACTIVITY_FACTORS:
            raise ValueError(f"Unknown activity level: {profile.activity_level}")
        return _ACTIVITY_FACTORS[level]

    def calculate_tdee(self, profile: UserProfile) -> float:
        return self.calculate_bmr(profile) * self.activity_factor(profile)

    def caloric_goal(self, profile: UserProfile) -> float:
        goal = profile.normalized_goal()
        if goal not in _GOAL_CALORIC_ADJUSTMENT:
            raise ValueError(f"Unsupported goal: {profile.goal}")
        return self.calculate_tdee(profile) * _GOAL_CALORIC_ADJUSTMENT[goal]

    def macro_targets(self, profile: UserProfile) -> NutritionTargets:
        calories = self.caloric_goal(profile)
        goal = profile.normalized_goal()
        if goal not in _GOAL_MACRO_RATIOS:
            raise ValueError(f"Unsupported goal: {profile.goal}")
        protein_ratio, fat_ratio, carb_ratio = _GOAL_MACRO_RATIOS[goal]
        protein_g = (calories * protein_ratio) / 4.0
        fat_g = (calories * fat_ratio) / 9.0
        carbs_g = (calories * carb_ratio) / 4.0
        return NutritionTargets(
            calories=round(calories, 2),
            protein_g=round(protein_g, 2),
            fat_g=round(fat_g, 2),
            carbs_g=round(carbs_g, 2),
        )
