"""Synthetic dataset generation helpers."""

from __future__ import annotations

import csv
import os
import random
from typing import Iterable, List

from .analyzer import NutritionAnalyzer
from .dataset import load_dishes
from .models import UserProfile
from .planner import MealPlanRecommender

GOALS = ["Weight Loss", "Muscle Gain", "Maintenance"]
GENDERS = ["male", "female"]
PREFERENCES = ["vegetarian", "low-salt", "low-sugar", ""]


def random_user_profile() -> UserProfile:
    age = random.randint(18, 65)
    gender = random.choice(GENDERS)
    weight = round(random.uniform(50, 110), 1)
    height = round(random.uniform(150, 200), 1)
    goal = random.choice(GOALS)
    activity_factor = random.choice([1.2, 1.35, 1.5])
    preferences = random.sample(PREFERENCES, k=random.randint(0, 2))
    preferences = [pref for pref in preferences if pref]
    return UserProfile(
        age=age,
        height=height,
        weight=weight,
        gender=gender,
        goal=goal,
        activity_factor=activity_factor,
        dietary_preferences=preferences,
    )


def generate_synthetic_user_dataset(
    output_path: str,
    count: int = 20,
    additional_datasets: Iterable[str] | None = None,
) -> str:
    dishes = load_dishes(additional_datasets)
    if not dishes:
        raise ValueError("Dish dataset is empty; cannot generate synthetic data.")
    recommender = MealPlanRecommender(dishes)
    rows: List[List[object]] = [[
        "age",
        "gender",
        "weight",
        "height",
        "goal",
        "activity_factor",
        "preferences",
        "target_calories",
        "target_protein",
        "target_fat",
        "target_carbs",
        "meal_1",
        "meal_2",
        "meal_3",
        "total_calories",
    ]]
    for _ in range(count):
        user = random_user_profile()
        analyzer = NutritionAnalyzer(user)
        targets = analyzer.build_targets()
        plans = recommender.recommend(user, targets, meals_per_day=3, num_options=1)
        if not plans:
            continue
        plan = plans[0]
        meal_descriptions = [meal.description for meal in plan.meals]
        rows.append([
            user.age,
            user.gender,
            user.weight,
            user.height,
            user.goal,
            user.activity_factor,
            ", ".join(user.normalized_preferences()),
            targets.calories,
            targets.protein_grams,
            targets.fat_grams,
            targets.carb_grams,
            meal_descriptions[0] if len(meal_descriptions) > 0 else "",
            meal_descriptions[1] if len(meal_descriptions) > 1 else "",
            meal_descriptions[2] if len(meal_descriptions) > 2 else "",
            plan.total_calories(),
        ])
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)
    return output_path
