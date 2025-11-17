"""Command line interface for the nutrition analysis system."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from nutrition_system import (
    UserProfile,
    export_plan_to_excel,
    export_plan_to_pdf,
    generate_macro_charts,
    generate_meal_plans,
    load_dish_database,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Personalized Nutrition Analysis")
    parser.add_argument("--age", type=int, required=True, help="Age in years")
    parser.add_argument("--gender", choices=["Male", "Female"], required=True)
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
        default="sedentary",
        choices=["sedentary", "light", "moderate", "active", "very_active"],
    )
    parser.add_argument(
        "--preferences",
        type=str,
        default="",
        help="Comma separated dietary preferences (e.g. Vegetarian,Low-Carb)",
    )
    parser.add_argument(
        "--meals",
        type=int,
        default=3,
        help="Primary number of meals to generate a plan for",
    )
    parser.add_argument(
        "--alt-meals",
        type=str,
        default="",
        help="Additional meal counts separated by commas (e.g. 2,4,5)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="Number of alternative meal plans to display per meal count",
    )
    parser.add_argument(
        "--export-dir",
        type=str,
        default="reports",
        help="Directory where reports should be exported",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export best plan to Excel and PDF with charts",
    )
    parser.add_argument(
        "--show-json",
        action="store_true",
        help="Output the plan data as JSON for automation",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    preferences: List[str] = [
        pref.strip()
        for pref in args.preferences.split(",")
        if pref.strip()
    ]
    meal_counts = {args.meals}
    if args.alt_meals:
        meal_counts.update(int(val.strip()) for val in args.alt_meals.split(",") if val.strip())

    profile = UserProfile(
        age=args.age,
        gender=args.gender,
        weight_kg=args.weight,
        height_cm=args.height,
        goal=args.goal,
        activity_level=args.activity_level,
        dietary_preferences=preferences,
    )

    dishes = load_dish_database()
    plans = generate_meal_plans(
        profile,
        dishes,
        meals_per_day=sorted(meal_counts),
        top_n=args.top,
    )

    output_dir = Path(args.export_dir)
    results_to_display = {}
    for meal_count, plan_options in plans.items():
        print(f"\nMeal Count: {meal_count}")
        if not plan_options:
            print("  No matching meal plans generated within tolerance.")
            continue
        for index, plan in enumerate(plan_options, start=1):
            totals = plan["totals"]
            print(
                f"  Option {index}: {totals['calories']:.0f} kcal | Protein: {totals['protein']:.1f}g | "
                f"Fat: {totals['fat']:.1f}g | Carbs: {totals['carbs']:.1f}g"
            )
            for detail in plan["details"]:
                print(
                    f"    - {detail['dish_name']} ({detail['calories']} kcal, "
                    f"{detail['protein']}g P, {detail['fat']}g F, {detail['carbs']}g C)"
                )
        results_to_display[meal_count] = plan_options

    if args.export and results_to_display:
        best_plans = [plans for meal, plans in results_to_display.items() if plans]
        if best_plans:
            best_plan = best_plans[0][0]
            chart_paths = generate_macro_charts(
                totals=best_plan["totals"],
                meal_details=best_plan["details"],
                output_dir=output_dir,
                prefix="best_plan",
            )
            excel_path = export_plan_to_excel(best_plan, output_dir / "meal_plan.xlsx")
            pdf_path = export_plan_to_pdf(
                profile,
                best_plan,
                output_path=output_dir / "nutrition_report.pdf",
                chart_paths=chart_paths,
            )
            print(f"\nExported Excel report to: {excel_path}")
            print(f"Exported PDF report to: {pdf_path}")

    if args.show_json:
        json_output = json.dumps(results_to_display, indent=2)
        print("\nJSON Output:\n" + json_output)


if __name__ == "__main__":
    main()
