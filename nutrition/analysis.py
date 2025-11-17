"""Core nutrition analysis utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


ACTIVITY_FACTORS: Dict[str, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

MACRO_RATIOS: Dict[str, Dict[str, float]] = {
    "weight loss": {"protein": 0.4, "fat": 0.3, "carbs": 0.3},
    "muscle gain": {"protein": 0.3, "fat": 0.25, "carbs": 0.45},
    "maintenance": {"protein": 0.25, "fat": 0.3, "carbs": 0.45},
}

SUPPORTED_GOALS: Iterable[str] = tuple(MACRO_RATIOS)
SUPPORTED_GENDERS: Iterable[str] = ("male", "female")


@dataclass(frozen=True)
class UserProfile:
    """Capture key user inputs for personalized planning."""

    age: int
    gender: str
    weight_kg: float
    height_cm: float
    goal: str
    activity_level: str = "moderate"
    preferences: Optional[List[str]] = None
    meals_per_day: int = 3

    def normalized_gender(self) -> str:
        gender = self.gender.strip().lower()
        if gender not in SUPPORTED_GENDERS:
            raise ValueError(f"Unsupported gender '{self.gender}'. Expected one of {SUPPORTED_GENDERS}.")
        return gender

    def normalized_goal(self) -> str:
        goal = self.goal.strip().lower()
        if goal not in MACRO_RATIOS:
            raise ValueError(f"Unsupported goal '{self.goal}'. Expected one of {list(MACRO_RATIOS)}.")
        return goal

    def normalized_activity(self) -> str:
        activity = self.activity_level.strip().lower()
        if activity not in ACTIVITY_FACTORS:
            raise ValueError(
                f"Unsupported activity level '{self.activity_level}'. Expected one of {list(ACTIVITY_FACTORS)}."
            )
        return activity

    def normalized_preferences(self) -> List[str]:
        if not self.preferences:
            return []
        return [pref.strip().lower() for pref in self.preferences if pref.strip()]

    def normalized_meal_count(self) -> int:
        return max(1, min(5, int(self.meals_per_day)))


class NutritionAnalyzer:
    """Provide nutrition requirement analysis based on user profile."""

    def calculate_bmr(self, profile: UserProfile) -> float:
        gender = profile.normalized_gender()
        if gender == "male":
            return 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age + 5
        return 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age - 161

    def calculate_tdee(self, profile: UserProfile) -> float:
        bmr = self.calculate_bmr(profile)
        activity = profile.normalized_activity()
        factor = ACTIVITY_FACTORS[activity]
        return bmr * factor

    def calorie_target(self, profile: UserProfile) -> float:
        goal = profile.normalized_goal()
        tdee = self.calculate_tdee(profile)
        if goal == "weight loss":
            return tdee * 0.85
        if goal == "muscle gain":
            return tdee * 1.15
        return tdee

    def macronutrient_targets(self, calorie_target: float, goal: str) -> Dict[str, float]:
        goal_key = goal.strip().lower()
        if goal_key not in MACRO_RATIOS:
            raise ValueError(f"Unsupported goal '{goal}'. Expected one of {list(MACRO_RATIOS)}.")
        ratios = MACRO_RATIOS[goal_key]
        protein = calorie_target * ratios["protein"] / 4
        fat = calorie_target * ratios["fat"] / 9
        carbs = calorie_target * ratios["carbs"] / 4
        return {
            "calories": round(calorie_target, 2),
            "protein": round(protein, 2),
            "fat": round(fat, 2),
            "carbs": round(carbs, 2),
        }

    def analyze(self, profile: UserProfile) -> Dict[str, float]:
        bmr = self.calculate_bmr(profile)
        tdee = self.calculate_tdee(profile)
        calorie_target = self.calorie_target(profile)
        macros = self.macronutrient_targets(calorie_target, profile.goal)
        analysis = {
            "bmr": round(bmr, 2),
            "tdee": round(tdee, 2),
            "calorie_target": macros["calories"],
            "protein_target": macros["protein"],
            "fat_target": macros["fat"],
            "carb_target": macros["carbs"],
        }
        return analysis
