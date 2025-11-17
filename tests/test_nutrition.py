from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nutrition.analysis import NutritionAnalyzer, UserProfile
from nutrition.data_loader import DishDatabase
from nutrition.meal_planner import MealPlanner
from nutrition.report import ReportGenerator
from nutrition.synthetic import SyntheticDataGenerator


def test_bmr_and_tdee_calculations():
    analyzer = NutritionAnalyzer()
    profile = UserProfile(
        age=30,
        gender="male",
        weight_kg=80,
        height_cm=180,
        goal="maintenance",
        activity_level="moderate",
    )
    bmr = analyzer.calculate_bmr(profile)
    assert math.isclose(bmr, 1780, rel_tol=1e-3)

    tdee = analyzer.calculate_tdee(profile)
    assert math.isclose(tdee, 1780 * 1.55, rel_tol=1e-3)


def test_macro_distribution_matches_targets():
    analyzer = NutritionAnalyzer()
    profile = UserProfile(
        age=28,
        gender="female",
        weight_kg=65,
        height_cm=165,
        goal="weight loss",
        activity_level="light",
    )
    analysis = analyzer.analyze(profile)
    total_calories = (
        analysis["protein_target"] * 4
        + analysis["fat_target"] * 9
        + analysis["carb_target"] * 4
    )
    assert math.isclose(total_calories, analysis["calorie_target"], rel_tol=0.05)


def test_meal_planner_creates_preference_compliant_plans(tmp_path):
    analyzer = NutritionAnalyzer()
    database = DishDatabase.load()
    profile = UserProfile(
        age=35,
        gender="female",
        weight_kg=70,
        height_cm=170,
        goal="maintenance",
        activity_level="moderate",
        preferences=["vegetarian"],
        meals_per_day=3,
    )
    analysis = analyzer.analyze(profile)
    planner = MealPlanner(database, analyzer)
    plans = planner.create_meal_plans(profile, alternatives=2, analysis=analysis)
    assert len(plans) >= 1
    for plan in plans:
        assert len(plan.meals) == profile.normalized_meal_count()
        for meal in plan.meals:
            assert "vegetarian" in meal["tags"].lower()
        # ensure totals are within a reasonable bound of targets
        assert abs(plan.totals["calories"] - analysis["calorie_target"]) < 800

    report_generator = ReportGenerator(profile, analysis)
    excel_path = tmp_path / "plan.xlsx"
    pdf_path = tmp_path / "plan.pdf"
    pie_path = tmp_path / "pie.png"
    bar_path = tmp_path / "bar.png"

    report_generator.export_to_excel(plans[0], excel_path)
    report_generator.export_to_pdf(plans[0], pdf_path)
    report_generator.create_macro_pie_chart(plans[0], pie_path)
    report_generator.create_meal_bar_chart(plans[0], bar_path)

    for path in (excel_path, pdf_path, pie_path, bar_path):
        assert path.exists()
        assert path.stat().st_size > 0


def test_synthetic_dataset_generation(tmp_path):
    output = tmp_path / "synthetic.csv"
    SyntheticDataGenerator.generate_dish_dataset(5, output)
    assert output.exists()
    assert output.stat().st_size > 0