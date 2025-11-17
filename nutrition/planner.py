"""Nutrition analysis and meal plan recommendation utilities.

This module implements a lightweight nutrition planning toolkit that satisfies
requirements outlined in the project description.  It provides:

* Basal metabolic rate (BMR) and total daily energy expenditure (TDEE)
  calculations using the Mifflin-St Jeor formula.
* Goal-based calorie adjustments and macronutrient targets.
* Meal plan recommendation from a dish database while respecting dietary
  preferences.
* Report generation with chart visualisations and Excel export support.
* Synthetic dataset generation utilities for testing.

The module is intentionally self-contained and minimises external
dependencies so that it can run in a constrained evaluation environment.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import csv
import json
import random
import statistics
import zipfile

import matplotlib

# Matplotlib needs to operate in headless environments during automated tests.
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Acceptable ranges for macronutrient calculations.
CALORIES_PER_GRAM = {"protein": 4, "fat": 9, "carbs": 4}

# Activity factors modelled on widely used defaults.
ACTIVITY_FACTORS: Dict[str, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_CALORIE_ADJUSTMENTS: Dict[str, float] = {
    "weight loss": -0.15,
    "muscle gain": 0.12,
    "maintenance": 0.0,
}

GOAL_MACRO_RATIOS: Dict[str, Dict[str, float]] = {
    "weight loss": {"protein": 0.3, "fat": 0.25, "carbs": 0.45},
    "muscle gain": {"protein": 0.35, "fat": 0.2, "carbs": 0.45},
    "maintenance": {"protein": 0.25, "fat": 0.25, "carbs": 0.5},
}

# ---------------------------------------------------------------------------
# Data structures


@dataclass
class UserProfile:
    """Basic user information required for diet analysis."""

    age: int
    gender: str
    weight_kg: float
    height_cm: float
    goal: str
    activity_level: str = "moderate"
    dietary_preferences: Sequence[str] = field(default_factory=tuple)
    meals_per_day: int = 3

    def normalised_goal(self) -> str:
        return self.goal.strip().lower()

    def normalised_gender(self) -> str:
        return self.gender.strip().lower()

    def normalised_preferences(self) -> Tuple[str, ...]:
        return tuple(sorted({pref.strip().lower() for pref in self.dietary_preferences}))


@dataclass
class NutritionTargets:
    """Calorie and macronutrient targets for a user."""

    target_calories: float
    macros_grams: Dict[str, float]
    tdee: float
    bmr: float

    def to_dict(self) -> Dict[str, float]:
        output = {
            "target_calories": round(self.target_calories, 2),
            "tdee": round(self.tdee, 2),
            "bmr": round(self.bmr, 2),
        }
        output.update({f"target_{macro}": round(value, 2) for macro, value in self.macros_grams.items()})
        return output


@dataclass
class Dish:
    """Single dish entry from the dish database."""

    dish_name: str
    ingredients: Sequence[str]
    weight: float
    calories: float
    protein: float
    fat: float
    carbs: float
    tags: Sequence[str] = field(default_factory=tuple)

    def matches_preferences(self, requested: Sequence[str]) -> bool:
        if not requested:
            return True
        requested_lower = {pref.lower() for pref in requested}
        dish_tags = {tag.lower() for tag in self.tags}
        return requested_lower.issubset(dish_tags)

    def to_dict(self) -> Dict[str, object]:
        return {
            "dish_name": self.dish_name,
            "ingredients": list(self.ingredients),
            "weight": self.weight,
            "calories": self.calories,
            "protein": self.protein,
            "fat": self.fat,
            "carbs": self.carbs,
            "tags": list(self.tags),
        }


@dataclass
class MealPlanOption:
    """Represents a potential meal plan recommendation."""

    meals: Sequence[Dish]
    totals: Dict[str, float]
    score: float

    def to_dict(self) -> Dict[str, object]:
        return {
            "score": self.score,
            "totals": {k: round(v, 2) for k, v in self.totals.items()},
            "meals": [dish.to_dict() for dish in self.meals],
        }


# ---------------------------------------------------------------------------
# Meal and nutrition calculations


def calculate_bmr(user: UserProfile) -> float:
    """Calculate basal metabolic rate using the Mifflin-St Jeor formula."""

    gender = user.normalised_gender()
    bmr = 10 * user.weight_kg + 6.25 * user.height_cm - 5 * user.age
    if gender == "male":
        bmr += 5
    elif gender == "female":
        bmr -= 161
    else:
        raise ValueError(f"Unsupported gender: {user.gender}")
    return bmr


def calculate_tdee(bmr: float, activity_level: str) -> float:
    activity_key = activity_level.strip().lower()
    if activity_key not in ACTIVITY_FACTORS:
        raise ValueError(f"Unsupported activity level: {activity_level}")
    return bmr * ACTIVITY_FACTORS[activity_key]


def _calorie_adjustment(goal: str) -> float:
    goal_key = goal.strip().lower()
    if goal_key not in GOAL_CALORIE_ADJUSTMENTS:
        raise ValueError(f"Unsupported goal: {goal}")
    return GOAL_CALORIE_ADJUSTMENTS[goal_key]


def _macro_ratios(goal: str) -> Dict[str, float]:
    goal_key = goal.strip().lower()
    if goal_key not in GOAL_MACRO_RATIOS:
        raise ValueError(f"Unsupported goal: {goal}")
    return GOAL_MACRO_RATIOS[goal_key]


def determine_macro_targets(calories: float, ratios: Dict[str, float]) -> Dict[str, float]:
    macros = {}
    for macro, ratio in ratios.items():
        calorie_share = calories * ratio
        grams = calorie_share / CALORIES_PER_GRAM[macro]
        macros[macro] = grams
    return macros


def analyze_user_nutrition(user: UserProfile) -> NutritionTargets:
    bmr = calculate_bmr(user)
    tdee = calculate_tdee(bmr, user.activity_level)
    adjustment = _calorie_adjustment(user.goal)
    target_calories = tdee * (1 + adjustment)
    ratios = _macro_ratios(user.goal)
    macros = determine_macro_targets(target_calories, ratios)
    return NutritionTargets(
        target_calories=target_calories,
        macros_grams=macros,
        tdee=tdee,
        bmr=bmr,
    )


# ---------------------------------------------------------------------------
# Dish utilities


def load_dish_database(path: Path) -> List[Dish]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    dishes = []
    for entry in data:
        dishes.append(
            Dish(
                dish_name=entry["dish_name"],
                ingredients=entry.get("ingredients", []),
                weight=float(entry.get("weight", 0)),
                calories=float(entry.get("calories", 0)),
                protein=float(entry.get("protein", 0)),
                fat=float(entry.get("fat", 0)),
                carbs=float(entry.get("carbs", 0)),
                tags=entry.get("tags", []),
            )
        )
    return dishes


def filter_dishes_by_preferences(dishes: Sequence[Dish], preferences: Sequence[str]) -> List[Dish]:
    return [dish for dish in dishes if dish.matches_preferences(preferences)]


def aggregate_nutrients(dishes: Sequence[Dish]) -> Dict[str, float]:
    totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    for dish in dishes:
        totals["calories"] += dish.calories
        totals["protein"] += dish.protein
        totals["fat"] += dish.fat
        totals["carbs"] += dish.carbs
    return totals


def _score_plan(totals: Dict[str, float], targets: NutritionTargets) -> float:
    calorie_diff = abs(totals["calories"] - targets.target_calories) / max(targets.target_calories, 1)
    macro_diffs = []
    for macro, target_value in targets.macros_grams.items():
        actual = totals.get(macro, 0)
        macro_diffs.append(abs(actual - target_value) / max(target_value, 1))
    return calorie_diff + statistics.fmean(macro_diffs)


def _unique_combo_key(dishes: Sequence[Dish]) -> Tuple[str, ...]:
    return tuple(sorted(dish.dish_name for dish in dishes))


def generate_meal_plan_options(
    dishes: Sequence[Dish],
    targets: NutritionTargets,
    *,
    meals_per_day: int = 3,
    alternatives: int = 3,
    random_seed: Optional[int] = None,
) -> List[MealPlanOption]:
    if meals_per_day < 1 or meals_per_day > 5:
        raise ValueError("Meals per day must be between 1 and 5")

    if random_seed is not None:
        random.seed(random_seed)

    best_plans: Dict[Tuple[str, ...], MealPlanOption] = {}

    if not dishes:
        return []

    # Limit search iterations to keep performance manageable.
    search_iterations = max(300, alternatives * 150)
    for _ in range(search_iterations):
        selected_meals = random.choices(dishes, k=meals_per_day)
        totals = aggregate_nutrients(selected_meals)
        score = _score_plan(totals, targets)
        key = _unique_combo_key(selected_meals)
        if key not in best_plans or score < best_plans[key].score:
            best_plans[key] = MealPlanOption(meals=tuple(selected_meals), totals=totals, score=round(score, 4))

    sorted_plans = sorted(best_plans.values(), key=lambda option: option.score)
    return sorted_plans[:alternatives]


def build_meal_plan_report(
    user: UserProfile,
    targets: NutritionTargets,
    meal_plan: Sequence[MealPlanOption],
) -> Dict[str, object]:
    report = {
        "user": {
            "age": user.age,
            "gender": user.gender,
            "weight_kg": user.weight_kg,
            "height_cm": user.height_cm,
            "goal": user.goal,
            "activity_level": user.activity_level,
            "dietary_preferences": list(user.normalised_preferences()),
            "meals_per_day": user.meals_per_day,
        },
        "targets": targets.to_dict(),
        "meal_plan_options": [option.to_dict() for option in meal_plan],
    }
    return report


# ---------------------------------------------------------------------------
# Report generation utilities


def export_report_to_excel(report: Dict[str, object], output_path: Path) -> None:
    """Export a nutrition report to a simple Excel workbook.

    The export implementation writes a minimal XLSX file without third-party
    dependencies by emitting the required OpenXML components.  The resulting
    file contains summary information alongside meal details for the first
    recommended option.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Compose rows for the spreadsheet.
    header_rows = [
        ("Metric", "Value"),
        ("Age", report["user"]["age"]),
        ("Gender", report["user"]["gender"]),
        ("Weight (kg)", report["user"]["weight_kg"]),
        ("Height (cm)", report["user"]["height_cm"]),
        ("Goal", report["user"]["goal"]),
        ("Activity Level", report["user"]["activity_level"]),
        ("Target Calories", report["targets"]["target_calories"]),
        ("Target Protein (g)", report["targets"]["target_protein"]),
        ("Target Fat (g)", report["targets"]["target_fat"]),
        ("Target Carbs (g)", report["targets"]["target_carbs"]),
    ]

    meal_rows = [("Meal Plan Option", "Calories", "Protein", "Fat", "Carbs")]
    for option in report.get("meal_plan_options", [])[:3]:
        totals = option["totals"]
        meal_rows.append(
            (
                ", ".join(dish["dish_name"] for dish in option["meals"]),
                totals["calories"],
                totals["protein"],
                totals["fat"],
                totals["carbs"],
            )
        )

    # The workbook contains a single sheet placing summary rows first followed
    # by meal plan details after an empty row.
    rows: List[Tuple[str, ...]] = [tuple(str(col) for col in row) for row in header_rows]
    rows.append(("", ""))
    rows.extend(tuple(str(col) for col in row) for row in meal_rows)

    sheet_rows = "".join(
        f'<row r="{idx}">' + "".join(
            f'<c r="{chr(65 + ci)}{idx}" t="inlineStr"><is><t>{value}</t></is></c>'
            for ci, value in enumerate(row)
        ) + "</row>"
        for idx, row in enumerate(rows, start=1)
    )

    sheet_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
        "<sheetData>" + sheet_rows + "</sheetData>"
        "</worksheet>"
    )

    workbook_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
        "<sheets><sheet name=\"MealPlan\" sheetId=\"1\" r:id=\"rId1\"/></sheets>"
        "</workbook>"
    )

    content_types_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
        "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
        "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
        "<Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
        "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
        "</Types>"
    )

    rels_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>"
        "</Relationships>"
    )

    workbook_rels_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/>"
        "</Relationships>"
    )

    with zipfile.ZipFile(output_path, "w") as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", rels_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def export_meal_plan_to_csv(report: Dict[str, object], output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Dish", "Calories", "Protein", "Fat", "Carbs", "Tags"])
        for option in report.get("meal_plan_options", [])[:1]:
            for dish in option["meals"]:
                writer.writerow(
                    [
                        dish["dish_name"],
                        dish["calories"],
                        dish["protein"],
                        dish["fat"],
                        dish["carbs"],
                        ", ".join(dish.get("tags", [])),
                    ]
                )


# ---------------------------------------------------------------------------
# Visualisation utilities


def generate_visualisations(report: Dict[str, object], output_dir: Path) -> Dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    targets = report["targets"]
    macros = {
        "Protein": targets["target_protein"],
        "Fat": targets["target_fat"],
        "Carbs": targets["target_carbs"],
    }

    pie_path = output_dir / "macro_distribution.png"
    fig, ax = plt.subplots()
    ax.pie(macros.values(), labels=macros.keys(), autopct="%1.1f%%")
    ax.set_title("Macronutrient Target Distribution")
    fig.savefig(pie_path, bbox_inches="tight")
    plt.close(fig)

    bar_path = output_dir / "meal_calories.png"
    option = next(iter(report.get("meal_plan_options", [])), None)
    if option:
        meal_labels = [dish["dish_name"] for dish in option["meals"]]
        calories = [dish["calories"] for dish in option["meals"]]
    else:
        meal_labels = []
        calories = []

    fig, ax = plt.subplots()
    ax.bar(meal_labels, calories, color="skyblue")
    ax.set_ylabel("Calories")
    ax.set_title("Calories per Meal")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(bar_path, bbox_inches="tight")
    plt.close(fig)

    return {"pie": pie_path, "bar": bar_path}


# ---------------------------------------------------------------------------
# Synthetic dataset generation


def generate_synthetic_history(
    dishes: Sequence[Dish],
    *,
    num_records: int,
    output_path: Path,
    random_seed: Optional[int] = None,
) -> Path:
    """Generate a synthetic dataset of historical meal choices."""

    if random_seed is not None:
        random.seed(random_seed)

    fieldnames = ["user_id", "dish_name", "calories", "protein", "fat", "carbs", "tags"]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row_idx in range(num_records):
            dish = random.choice(dishes)
            writer.writerow(
                {
                    "user_id": row_idx % 10,
                    "dish_name": dish.dish_name,
                    "calories": dish.calories,
                    "protein": dish.protein,
                    "fat": dish.fat,
                    "carbs": dish.carbs,
                    "tags": ", ".join(dish.tags),
                }
            )
    return output_path


# ---------------------------------------------------------------------------
# Public orchestration helpers


def create_nutrition_analysis(
    *,
    user: UserProfile,
    dishes: Sequence[Dish],
    alternatives: int = 3,
    random_seed: Optional[int] = None,
) -> Dict[str, object]:
    """Convenience wrapper that orchestrates the full analysis pipeline."""

    filtered_dishes = filter_dishes_by_preferences(dishes, user.dietary_preferences)
    if not filtered_dishes:
        raise ValueError("No dishes available that match the provided dietary preferences.")

    targets = analyze_user_nutrition(user)
    options = generate_meal_plan_options(
        filtered_dishes,
        targets,
        meals_per_day=user.meals_per_day,
        alternatives=alternatives,
        random_seed=random_seed,
    )
    report = build_meal_plan_report(user, targets, options)
    return report


# ---------------------------------------------------------------------------
# Command line interface


def _prompt_list(prompt: str) -> List[str]:
    raw = input(prompt).strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Personalised nutrition analysis tool")
    parser.add_argument("dish_db", type=Path, help="Path to dish database JSON file")
    parser.add_argument("--age", type=int, required=True)
    parser.add_argument("--gender", choices=["Male", "Female"], required=True)
    parser.add_argument("--weight", type=float, required=True, help="Weight in kilograms")
    parser.add_argument("--height", type=float, required=True, help="Height in centimetres")
    parser.add_argument(
        "--goal",
        choices=["Weight Loss", "Muscle Gain", "Maintenance"],
        required=True,
        help="Primary health goal",
    )
    parser.add_argument(
        "--activity",
        choices=list(ACTIVITY_FACTORS.keys()),
        default="moderate",
        help="Activity factor for TDEE calculation",
    )
    parser.add_argument(
        "--meals",
        type=int,
        default=3,
        help="Meals per day (1-5)",
    )
    parser.add_argument(
        "--preferences",
        nargs="*",
        default=[],
        help="Dietary preference tags that must be present on dishes",
    )
    parser.add_argument(
        "--alternatives",
        type=int,
        default=3,
        help="Number of alternative meal plan options to generate",
    )
    parser.add_argument(
        "--export-dir",
        type=Path,
        default=Path("exports"),
        help="Directory to store exported reports",
    )
    parser.add_argument(
        "--generate-synthetic",
        type=int,
        default=0,
        help="Generate an additional synthetic meal history dataset with the given number of records",
    )

    args = parser.parse_args(argv)

    dishes = load_dish_database(args.dish_db)
    profile = UserProfile(
        age=args.age,
        gender=args.gender,
        weight_kg=args.weight,
        height_cm=args.height,
        goal=args.goal,
        activity_level=args.activity,
        dietary_preferences=args.preferences,
        meals_per_day=args.meals,
    )

    report = create_nutrition_analysis(user=profile, dishes=dishes, alternatives=args.alternatives)

    export_dir = args.export_dir
    export_dir.mkdir(parents=True, exist_ok=True)

    excel_path = export_dir / "nutrition_report.xlsx"
    csv_path = export_dir / "meal_plan.csv"
    export_report_to_excel(report, excel_path)
    export_meal_plan_to_csv(report, csv_path)

    charts = generate_visualisations(report, export_dir)

    print("Nutrition analysis complete!")
    print(f"Report exported to: {excel_path}")
    print(f"Meal plan exported to: {csv_path}")
    print(f"Charts saved to: {charts['pie']} and {charts['bar']}")

    if args.generate_synthetic > 0:
        synthetic_path = export_dir / "synthetic_history.csv"
        generate_synthetic_history(dishes, num_records=args.generate_synthetic, output_path=synthetic_path)
        print(f"Synthetic dataset generated at: {synthetic_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
