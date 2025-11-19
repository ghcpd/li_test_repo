"""Core nutrition analysis and meal planning utilities."""

from .models import UserProfile, Dish, MealPlan
from .analyzer import NutritionAnalyzer
from .planner import MealPlanRecommender
from .report import NutritionReport
from .synthetic import generate_synthetic_user_dataset

__all__ = [
    "UserProfile",
    "Dish",
    "MealPlan",
    "NutritionAnalyzer",
    "MealPlanRecommender",
    "NutritionReport",
    "generate_synthetic_user_dataset",
]
