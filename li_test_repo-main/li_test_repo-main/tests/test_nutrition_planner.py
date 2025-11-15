from pathlib import Path
import sys
import zipfile

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from nutrition_planner.analysis import NutritionAnalyzer
from nutrition_planner.data import DishDatabase, SyntheticDatasetGenerator
from nutrition_planner.models import UserProfile
from nutrition_planner.recommendation import MealPlanRecommender
from nutrition_planner.reporting import NutritionReportGenerator


def test_bmr_and_macro_targets():
    analyzer = NutritionAnalyzer()
    profile = UserProfile(
        age=30,
        gender="male",
        weight_kg=80,
        height_cm=180,
        activity_level="moderate",
        goal="Weight Loss",
    )
    bmr = analyzer.calculate_bmr(profile)
    assert pytest.approx(bmr, rel=1e-3) == 1780
    tdee = analyzer.calculate_tdee(profile)
    assert tdee > bmr
    targets = analyzer.macro_targets(profile)
    assert targets.calories < tdee
    assert targets.protein_g > 0


def test_meal_plan_recommendation_and_reporting(tmp_path: Path):
    data_path = Path(__file__).resolve().parents[1] / "nutrition_planner" / "dish_database.csv"
    database = DishDatabase.from_csv(data_path)
    analyzer = NutritionAnalyzer()
    preferences = ["high-protein"]
    profile = UserProfile(
        age=28,
        gender="female",
        weight_kg=65,
        height_cm=168,
        activity_level="light",
        goal="Muscle Gain",
        dietary_preferences=preferences,
    )
    targets = analyzer.macro_targets(profile)
    recommender = MealPlanRecommender(database.dishes)
    plan = recommender.recommend(profile, targets, meal_count=3, dietary_preferences=preferences)
    for meal in plan.meals:
        for component in meal.components:
            assert set(preferences).issubset(set(component.dish.tags))
    summary = NutritionReportGenerator().summarize(plan, targets)
    assert abs(summary["difference"]["calories"]) < 220
    assert abs(summary["difference"]["protein_g"]) < 15
    report_generator = NutritionReportGenerator()
    macro_chart = report_generator.macro_pie_chart_svg(plan, str(tmp_path / "macro.svg"))
    bar_chart = report_generator.meal_barchart_svg(plan, str(tmp_path / "bar.svg"))
    assert Path(macro_chart).read_text(encoding="utf-8").startswith("<svg")
    assert Path(bar_chart).read_text(encoding="utf-8").startswith("<svg")
    excel_path = tmp_path / "report.xlsx"
    pdf_path = tmp_path / "report.pdf"
    report_generator.export_to_excel(summary, str(excel_path))
    report_generator.export_to_pdf(summary, str(pdf_path))
    assert excel_path.exists()
    assert pdf_path.exists()
    with zipfile.ZipFile(excel_path) as zf:
        assert "xl/workbook.xml" in zf.namelist()
        sheet_data = zf.read("xl/worksheets/sheet1.xml").decode("utf-8")
        assert "Target" in sheet_data
        assert "Meal" in sheet_data
    pdf_bytes = pdf_path.read_bytes()
    assert pdf_bytes.startswith(b"%PDF-1.4")


def test_synthetic_dataset_generation(tmp_path: Path):
    generator = SyntheticDatasetGenerator(
        ingredients=["Spinach", "Chicken", "Rice", "Tomato", "Avocado"],
        base_dishes=["Plate", "Bowl"],
    )
    output = tmp_path / "dishes.csv"
    generator.generate_dish_dataset(5, output)
    lines = output.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 6
    header = lines[0].split(",")
    assert header[:3] == ["dish_name", "ingredients", "weight"]