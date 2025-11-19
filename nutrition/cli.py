"""Command line interface for the nutrition analysis and meal plan system."""

from __future__ import annotations

import argparse
import json
import os
from typing import Iterable, Sequence

from .analyzer import NutritionAnalyzer
from .dataset import load_dishes
from .models import UserProfile
from .planner import MealPlanRecommender
from .report import NutritionReport
from .synthetic import generate_synthetic_user_dataset


def parse_preferences(values: Iterable[str]) -> list[str]:
    preferences: list[str] = []
    for value in values:
        if not value:
            continue
        fragments = [fragment.strip() for fragment in value.split(",")]
        preferences.extend([fragment for fragment in fragments if fragment])
    return preferences


def build_user_profile(args: argparse.Namespace) -> UserProfile:
    return UserProfile(
        age=args.age,
        height=args.height,
        weight=args.weight,
        gender=args.gender,
        goal=args.goal,
        activity_factor=args.activity_factor,
        dietary_preferences=parse_preferences(args.preference),
    )


def run_analysis_command(args: argparse.Namespace) -> None:
    dishes = load_dishes(args.dataset)
    if not dishes:
        raise SystemExit("Dish dataset could not be loaded. Provide a valid dataset path.")
    profile = build_user_profile(args)
    analyzer = NutritionAnalyzer(profile)
    targets = analyzer.build_targets()
    planner = MealPlanRecommender(dishes)
    plans = planner.recommend(
        profile,
        targets,
        meals_per_day=args.meals_per_day,
        num_options=args.num_options,
    )
    if not plans:
        raise SystemExit("Unable to create a meal plan with the provided parameters.")
    print("Daily Nutrition Targets:")
    print(json.dumps(analyzer.summarize(), indent=2))
    for idx, plan in enumerate(plans, start=1):
        print(f"\nMeal Plan Option {idx}:")
        print(plan.describe())
        summary = planner.summary_for_plan(plan, targets)
        print(json.dumps(summary, indent=2))
        if args.export_dir:
            report = NutritionReport(profile, targets, plan)
            artifacts = report.export_all(
                args.export_dir,
                base_name=args.output_basename,
                include_pdf=not args.no_pdf,
                include_excel=not args.no_excel,
            )
            if args.chart_dir:
                chart_paths = report.save_charts(args.chart_dir, args.output_basename)
            else:
                chart_paths = {
                    "pie_chart": artifacts.pie_chart_path,
                    "bar_chart": artifacts.bar_chart_path,
                }
            print("Exported artifacts:")
            print(json.dumps({
                "summary": artifacts.summary,
                "macro_ratios": artifacts.macro_ratios,
                "pdf": artifacts.pdf_path,
                "excel": artifacts.excel_path,
                "pie_chart": chart_paths.get("pie_chart"),
                "bar_chart": chart_paths.get("bar_chart"),
            }, indent=2))
        if args.only_first_option:
            break


def run_synthetic_command(args: argparse.Namespace) -> None:
    output_path = generate_synthetic_user_dataset(
        args.output,
        count=args.count,
        additional_datasets=args.dataset,
    )
    print(f"Synthetic dataset generated at {output_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Personalized Nutrition Analysis & Meal Plan Recommendation System",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="run nutrition analysis and meal planning")
    analyze.add_argument("--age", type=int, required=True)
    analyze.add_argument("--gender", choices=["male", "female"], required=True)
    analyze.add_argument("--weight", type=float, required=True, help="Weight in kg")
    analyze.add_argument("--height", type=float, required=True, help="Height in cm")
    analyze.add_argument("--goal", choices=["Weight Loss", "Muscle Gain", "Maintenance"], required=True)
    analyze.add_argument("--activity-factor", dest="activity_factor", type=float, default=1.2)
    analyze.add_argument(
        "--preference",
        action="append",
        default=[],
        help="Dietary preference (may be provided multiple times or as comma-separated values)",
    )
    analyze.add_argument(
        "--dataset",
        action="append",
        default=[],
        help="Additional dataset file(s) to load dishes from",
    )
    analyze.add_argument("--meals-per-day", type=int, default=3)
    analyze.add_argument("--num-options", type=int, default=3)
    analyze.add_argument("--export-dir", default="", help="Directory to write reports to")
    analyze.add_argument("--chart-dir", default="", help="Directory to store chart SVGs")
    analyze.add_argument("--output-basename", default="nutrition_report")
    analyze.add_argument("--no-pdf", action="store_true", help="Skip exporting PDF report")
    analyze.add_argument("--no-excel", action="store_true", help="Skip exporting Excel report")
    analyze.add_argument("--only-first-option", action="store_true", help="Stop after first recommendation")

    synthetic = subparsers.add_parser(
        "generate-synthetic",
        help="Generate a synthetic dataset of nutrition analyses",
    )
    synthetic.add_argument("--output", required=True, help="Path to write the synthetic dataset (CSV)")
    synthetic.add_argument("--count", type=int, default=20, help="Number of synthetic entries to generate")
    synthetic.add_argument(
        "--dataset",
        action="append",
        default=[],
        help="Additional dataset file(s) to load dishes from",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "analyze":
        run_analysis_command(args)
    elif args.command == "generate-synthetic":
        run_synthetic_command(args)
    else:
        parser.error("Unknown command")


if __name__ == "__main__":
    main()
