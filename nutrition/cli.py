"""Command-line interface for the nutrition analysis and meal planner."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .analysis import NutritionAnalyzer, UserProfile
from .data_loader import DishDatabase
from .meal_planner import MealPlanner
from .report import ReportGenerator


def parse_arguments(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Personalized Nutrition Analysis and Meal Plan Recommendation",
    )
    parser.add_argument("--age", type=int, required=True, help="Age in years")
    parser.add_argument("--gender", type=str, required=True, choices=["male", "female"], help="Gender")
    parser.add_argument("--weight", type=float, required=True, help="Weight in kilograms")
    parser.add_argument("--height", type=float, required=True, help="Height in centimeters")
    parser.add_argument(
        "--goal",
        type=str,
        required=True,
        choices=["weight loss", "muscle gain", "maintenance"],
        help="Nutrition goal",
    )
    parser.add_argument(
        "--activity-level",
        type=str,
        default="moderate",
        choices=["sedentary", "light", "moderate", "active", "very_active"],
        help="Activity level affecting TDEE",
    )
    parser.add_argument(
        "--preferences",
        type=str,
        default="",
        help="Comma-separated dietary preferences (e.g., vegetarian,low-carb)",
    )
    parser.add_argument("--meals", type=int, default=3, help="Number of meals per day (1-5)")
    parser.add_argument("--alternatives", type=int, default=3, help="Number of alternative plans to generate")
    parser.add_argument(
        "--excel-output",
        type=str,
        default="",
        help="Path to export Excel report (e.g., output/plan.xlsx)",
    )
    parser.add_argument(
        "--pdf-output",
        type=str,
        default="",
        help="Path to export PDF report (e.g., output/plan.pdf)",
    )
    parser.add_argument(
        "--charts-dir",
        type=str,
        default="",
        help="Directory to save visualization charts",
    )
    return parser.parse_args(argv)


def ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def main(argv: List[str] | None = None) -> None:
    args = parse_arguments(argv)

    preferences = [pref.strip() for pref in args.preferences.split(",") if pref.strip()]
    profile = UserProfile(
        age=args.age,
        gender=args.gender,
        weight_kg=args.weight,
        height_cm=args.height,
        goal=args.goal,
        activity_level=args.activity_level,
        preferences=preferences,
        meals_per_day=args.meals,
    )

    analyzer = NutritionAnalyzer()
    analysis = analyzer.analyze(profile)

    database = DishDatabase.load()
    planner = MealPlanner(database, analyzer)
    meal_plans = planner.create_meal_plans(profile, alternatives=args.alternatives, analysis=analysis)
    report_generator = ReportGenerator(profile, analysis)

    print("\n=== Personal Nutrition Analysis ===")
    for key in ("bmr", "tdee", "calorie_target", "protein_target", "fat_target", "carb_target"):
        show_key = key.replace("_", " ").title()
        print(f"{show_key}: {analysis[key]}")

    print("\n=== Meal Plan Recommendations ===")
    for plan in meal_plans:
        print(f"\n--- Plan {plan.plan_id} ---")
        for meal in plan.meals:
            print(
                f"Meal {meal['meal_number']}: {meal['dish_name']} | "
                f"Calories: {meal['calories']}, Protein: {meal['protein']}g, "
                f"Fat: {meal['fat']}g, Carbs: {meal['carbs']}g"
            )
        totals = plan.totals
        print(
            f"Totals - Calories: {totals['calories']} kcal, Protein: {totals['protein']} g, "
            f"Fat: {totals['fat']} g, Carbs: {totals['carbs']} g"
        )

    charts_dir = Path(args.charts_dir) if args.charts_dir else None
    if charts_dir:
        charts_dir.mkdir(parents=True, exist_ok=True)
        primary_plan = meal_plans[0]
        report_generator.create_macro_pie_chart(primary_plan, charts_dir / "macro_distribution.png")
        report_generator.create_meal_bar_chart(primary_plan, charts_dir / "meal_calories.png")
        print(f"Charts saved to {charts_dir}")

    if args.excel_output:
        excel_path = Path(args.excel_output)
        ensure_directory(excel_path)
        report_generator.export_to_excel(meal_plans[0], excel_path)
        print(f"Excel report saved to {excel_path}")

    if args.pdf_output:
        pdf_path = Path(args.pdf_output)
        ensure_directory(pdf_path)
        report_generator.export_to_pdf(meal_plans[0], pdf_path)
        print(f"PDF report saved to {pdf_path}")


if __name__ == "__main__":
    main()
