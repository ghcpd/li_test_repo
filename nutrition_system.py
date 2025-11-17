"""Personalized nutrition analysis and meal plan recommendation system."""
from __future__ import annotations

import itertools
import json
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


BASE_DIR = Path(__file__).resolve().parent
DISH_DATABASE_PATH = BASE_DIR / "dish_database.json"


GOAL_CALORIE_ADJUSTMENT = {
    "weight loss": 0.85,
    "weight_loss": 0.85,
    "weight-loss": 0.85,
    "muscle gain": 1.15,
    "muscle_gain": 1.15,
    "muscle-gain": 1.15,
    "maintenance": 1.0,
}

MACRO_RATIOS = {
    "weight loss": {"protein": 0.35, "fat": 0.25, "carbs": 0.40},
    "weight_loss": {"protein": 0.35, "fat": 0.25, "carbs": 0.40},
    "weight-loss": {"protein": 0.35, "fat": 0.25, "carbs": 0.40},
    "muscle gain": {"protein": 0.30, "fat": 0.25, "carbs": 0.45},
    "muscle_gain": {"protein": 0.30, "fat": 0.25, "carbs": 0.45},
    "muscle-gain": {"protein": 0.30, "fat": 0.25, "carbs": 0.45},
    "maintenance": {"protein": 0.25, "fat": 0.30, "carbs": 0.45},
}

CALORIES_PER_GRAM = {"protein": 4, "carbs": 4, "fat": 9}

ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


@dataclass
class UserProfile:
    """User profile holding demographic and goal information."""

    age: int
    gender: str
    weight_kg: float
    height_cm: float
    goal: str
    activity_level: str = "sedentary"
    dietary_preferences: List[str] = field(default_factory=list)

    @property
    def normalized_goal(self) -> str:
        return self.goal.replace(" ", "_").lower()

    @property
    def activity_factor(self) -> float:
        return ACTIVITY_FACTORS.get(self.activity_level.lower(), 1.2)


@dataclass
class Dish:
    """Representation of a dish entry from the database."""

    dish_name: str
    ingredients: List[str]
    serving_size: float
    calories: float
    protein: float
    fat: float
    carbs: float
    tags: List[str]

    @staticmethod
    def from_dict(data: Dict[str, object]) -> "Dish":
        return Dish(
            dish_name=str(data["dish_name"]),
            ingredients=list(data.get("ingredients", [])),
            serving_size=float(data.get("serving_size", 0)),
            calories=float(data.get("calories", 0)),
            protein=float(data.get("protein", 0)),
            fat=float(data.get("fat", 0)),
            carbs=float(data.get("carbs", 0)),
            tags=[str(tag) for tag in data.get("tags", [])],
        )


def load_dish_database(path: Optional[Path] = None) -> List[Dish]:
    """Load dish database entries from JSON file."""

    database_path = path or DISH_DATABASE_PATH
    with database_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return [Dish.from_dict(entry) for entry in data]


def calculate_bmr(profile: UserProfile) -> float:
    """Calculate basal metabolic rate using the Mifflin-St Jeor formula."""

    gender = profile.gender.lower()
    if gender == "male":
        return 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age + 5
    if gender == "female":
        return 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age - 161
    raise ValueError("Gender must be 'Male' or 'Female'.")


def calculate_tdee(profile: UserProfile) -> float:
    """Estimate total daily energy expenditure."""

    bmr = calculate_bmr(profile)
    return bmr * profile.activity_factor


def calculate_daily_targets(profile: UserProfile) -> Dict[str, Dict[str, float]]:
    """Return caloric and macronutrient targets based on the user's goal."""

    tdee = calculate_tdee(profile)
    adjustment_factor = GOAL_CALORIE_ADJUSTMENT.get(profile.normalized_goal, 1.0)
    target_calories = tdee * adjustment_factor
    macro_ratio = MACRO_RATIOS.get(profile.normalized_goal, MACRO_RATIOS["maintenance"])

    macro_targets = {
        macro: (target_calories * ratio) / CALORIES_PER_GRAM[macro]
        for macro, ratio in macro_ratio.items()
    }

    return {
        "bmr": calculate_bmr(profile),
        "tdee": tdee,
        "target_calories": target_calories,
        "macro_targets": macro_targets,
        "macro_ratio": macro_ratio,
    }


def filter_dishes_by_preferences(dishes: Iterable[Dish], preferences: Sequence[str]) -> List[Dish]:
    """Filter dishes that satisfy all dietary preferences."""

    preferences_normalized = {pref.lower() for pref in preferences}
    if not preferences_normalized:
        return list(dishes)
    filtered = [
        dish
        for dish in dishes
        if preferences_normalized.issubset({tag.lower() for tag in dish.tags})
    ]
    return filtered


def _plan_score(aggregated: Dict[str, float], targets: Dict[str, float]) -> float:
    """Calculate a score representing closeness to targets."""

    calorie_diff = abs(aggregated["calories"] - targets["calories"]) / targets["calories"]
    protein_diff = abs(aggregated["protein"] - targets["protein"]) / targets["protein"]
    fat_diff = abs(aggregated["fat"] - targets["fat"]) / targets["fat"]
    carbs_diff = abs(aggregated["carbs"] - targets["carbs"]) / targets["carbs"]
    return calorie_diff + protein_diff + fat_diff + carbs_diff


def _aggregate_dishes(dishes: Sequence[Dish]) -> Dict[str, float]:
    return {
        "calories": sum(dish.calories for dish in dishes),
        "protein": sum(dish.protein for dish in dishes),
        "fat": sum(dish.fat for dish in dishes),
        "carbs": sum(dish.carbs for dish in dishes),
    }


def generate_meal_plans(
    profile: UserProfile,
    dishes: Sequence[Dish],
    meals_per_day: Sequence[int] = (3,),
    tolerance: float = 0.4,
    top_n: int = 3,
) -> Dict[int, List[Dict[str, object]]]:
    """Generate suitable meal plans based on targets and preferences."""

    targets_info = calculate_daily_targets(profile)
    targets = {
        "calories": targets_info["target_calories"],
        "protein": targets_info["macro_targets"]["protein"],
        "fat": targets_info["macro_targets"]["fat"],
        "carbs": targets_info["macro_targets"]["carbs"],
    }

    filtered_dishes = filter_dishes_by_preferences(dishes, profile.dietary_preferences)
    if not filtered_dishes:
        raise ValueError("No dishes available that match the provided dietary preferences.")

    results: Dict[int, List[Dict[str, object]]] = {}
    for meal_count in meals_per_day:
        combinations = itertools.combinations(filtered_dishes, meal_count)
        scored_plans: List[Tuple[float, Dict[str, object]]] = []
        for combo in combinations:
            aggregated = _aggregate_dishes(combo)
            if not _within_tolerance(aggregated, targets, tolerance):
                continue
            score = _plan_score(aggregated, targets)
            scored_plans.append(
                (
                    score,
                    {
                        "meals": [dish.dish_name for dish in combo],
                        "totals": aggregated,
                        "details": [
                            {
                                "dish_name": dish.dish_name,
                                "calories": dish.calories,
                                "protein": dish.protein,
                                "fat": dish.fat,
                                "carbs": dish.carbs,
                                "tags": dish.tags,
                            }
                            for dish in combo
                        ],
                    },
                )
            )
        scored_plans.sort(key=lambda item: item[0])
        results[meal_count] = [plan for _, plan in scored_plans[:top_n]]
    return results


def _within_tolerance(
    aggregated: Dict[str, float], targets: Dict[str, float], tolerance: float
) -> bool:
    return all(
        math.isclose(aggregated[key], targets[key], rel_tol=tolerance)
        for key in ("calories", "protein", "fat", "carbs")
    )


def generate_macro_charts(
    totals: Dict[str, float],
    meal_details: Sequence[Dict[str, float]],
    output_dir: Path,
    prefix: str,
) -> Dict[str, Path]:
    """Create pie and bar charts for macro distribution using matplotlib."""

    output_dir.mkdir(parents=True, exist_ok=True)

    import matplotlib.pyplot as plt  # imported lazily to avoid hard dependency elsewhere

    pie_path = output_dir / f"{prefix}_macros_pie.png"
    bar_path = output_dir / f"{prefix}_meals_bar.png"

    macros = ["protein", "fat", "carbs"]
    values = [totals[macro] for macro in macros]

    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=macros, autopct="%1.1f%%")
    plt.title("Macronutrient Distribution")
    plt.savefig(pie_path)
    plt.close()

    plt.figure(figsize=(8, 6))
    meal_names = [meal["dish_name"] for meal in meal_details]
    calories = [meal["calories"] for meal in meal_details]
    protein = [meal["protein"] for meal in meal_details]
    fat = [meal["fat"] for meal in meal_details]
    carbs = [meal["carbs"] for meal in meal_details]

    indices = range(len(meal_names))
    plt.bar([i - 0.2 for i in indices], protein, width=0.2, label="Protein (g)")
    plt.bar(indices, fat, width=0.2, label="Fat (g)")
    plt.bar([i + 0.2 for i in indices], carbs, width=0.2, label="Carbs (g)")
    plt.xticks(list(indices), meal_names, rotation=45, ha="right")
    plt.ylabel("Grams")
    plt.title("Meal-Level Macronutrients")
    plt.legend()
    plt.tight_layout()
    plt.savefig(bar_path)
    plt.close()

    return {"pie_chart": pie_path, "bar_chart": bar_path}


def export_plan_to_excel(plan: Dict[str, object], output_path: Path) -> Path:
    """Export meal plan to an Excel file using openpyxl."""

    from openpyxl import Workbook

    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Meal Plan"

    sheet.append(["Dish Name", "Calories", "Protein (g)", "Fat (g)", "Carbs (g)"])
    for detail in plan["details"]:
        sheet.append(
            [
                detail["dish_name"],
                detail["calories"],
                detail["protein"],
                detail["fat"],
                detail["carbs"],
            ]
        )

    totals = plan["totals"]
    sheet.append([])
    sheet.append(["Totals", totals["calories"], totals["protein"], totals["fat"], totals["carbs"]])

    workbook.save(output_path)
    return output_path


def export_plan_to_pdf(
    profile: UserProfile,
    plan: Dict[str, object],
    output_path: Path,
    chart_paths: Optional[Dict[str, Path]] = None,
) -> Path:
    """Export a nutrition analysis report to a PDF file."""

    from matplotlib import pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(output_path) as pdf:
        plt.figure(figsize=(8.5, 11))
        plt.axis("off")
        totals = plan["totals"]
        text_lines = [
            "Personalized Nutrition Analysis",
            "",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "",
            f"User Profile:",
            f"  Age: {profile.age}",
            f"  Gender: {profile.gender}",
            f"  Weight: {profile.weight_kg} kg",
            f"  Height: {profile.height_cm} cm",
            f"  Goal: {profile.goal}",
            f"  Activity Level: {profile.activity_level}",
            "",
            "Daily Targets (approx.):",
            f"  Calories: {totals['calories']:.0f} kcal",
            f"  Protein: {totals['protein']:.1f} g",
            f"  Fat: {totals['fat']:.1f} g",
            f"  Carbs: {totals['carbs']:.1f} g",
            "",
            "Meal Plan:" if plan["details"] else "No meals found",
        ]
        for detail in plan["details"]:
            text_lines.append(
                f"  - {detail['dish_name']}: {detail['calories']} kcal, {detail['protein']}g protein, {detail['fat']}g fat, {detail['carbs']}g carbs"
            )

        plt.text(0.05, 0.95, "\n".join(text_lines), va="top", fontsize=12)
        pdf.savefig()
        plt.close()

        if chart_paths:
            for chart in chart_paths.values():
                if chart.exists():
                    image = plt.imread(chart)
                    plt.figure(figsize=(8.5, 11))
                    plt.imshow(image)
                    plt.axis("off")
                    pdf.savefig()
                    plt.close()
    return output_path


def generate_synthetic_user_dataset(
    num_entries: int, output_path: Optional[Path] = None
) -> List[Dict[str, object]]:
    """Generate a synthetic dataset of user profiles for testing."""

    profiles = []
    possible_goals = list(GOAL_CALORIE_ADJUSTMENT.keys())
    genders = ["Male", "Female"]
    activity_levels = list(ACTIVITY_FACTORS.keys())

    dishes = load_dish_database()
    for _ in range(num_entries):
        profile = UserProfile(
            age=random.randint(18, 70),
            gender=random.choice(genders),
            weight_kg=random.uniform(50, 110),
            height_cm=random.uniform(150, 200),
            goal=random.choice(possible_goals),
            activity_level=random.choice(activity_levels),
        )
        targets = calculate_daily_targets(profile)
        preferences = []
        if random.random() < 0.4:
            preference_pool = {
                tag.lower() for dish in dishes for tag in dish.tags
            }
            if preference_pool:
                preferences.append(random.choice(sorted(preference_pool)))
        profiles.append(
            {
                "age": profile.age,
                "gender": profile.gender,
                "weight_kg": round(profile.weight_kg, 1),
                "height_cm": round(profile.height_cm, 1),
                "goal": profile.goal,
                "activity_level": profile.activity_level,
                "dietary_preferences": preferences,
                "targets": {
                    "bmr": round(targets["bmr"], 1),
                    "tdee": round(targets["tdee"], 1),
                    "calories": round(targets["target_calories"], 1),
                    "protein_g": round(targets["macro_targets"]["protein"], 1),
                    "fat_g": round(targets["macro_targets"]["fat"], 1),
                    "carbs_g": round(targets["macro_targets"]["carbs"], 1),
                },
            }
        )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(profiles, file, indent=2)

    return profiles
