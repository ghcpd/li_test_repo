import json
import zipfile
from pathlib import Path

import pytest

from nutrition import planner


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "dishes.json"


@pytest.fixture(scope="module")
def dishes():
    return planner.load_dish_database(DATA_PATH)


def test_calculate_bmr_gender_specific():
    male_user = planner.UserProfile(
        age=30,
        gender="Male",
        weight_kg=80,
        height_cm=180,
        goal="Maintenance",
    )
    female_user = planner.UserProfile(
        age=30,
        gender="Female",
        weight_kg=80,
        height_cm=180,
        goal="Maintenance",
    )

    male_bmr = planner.calculate_bmr(male_user)
    female_bmr = planner.calculate_bmr(female_user)

    assert pytest.approx(male_bmr, rel=1e-3) == 1780
    assert pytest.approx(female_bmr, rel=1e-3) == 1614


def test_analyze_user_nutrition_targets():
    user = planner.UserProfile(
        age=28,
        gender="Female",
        weight_kg=65,
        height_cm=165,
        goal="Weight Loss",
        activity_level="light",
    )

    targets = planner.analyze_user_nutrition(user)

    # Ensure calories are adjusted below TDEE for weight loss.
    assert targets.target_calories < targets.tdee

    ratios = planner._macro_ratios(user.goal)
    total_macro_cals = sum(targets.macros_grams[m] * planner.CALORIES_PER_GRAM[m] for m in ratios)
    assert pytest.approx(total_macro_cals, rel=1e-3) == pytest.approx(targets.target_calories, rel=1e-3)


def test_filter_dishes_by_preferences(dishes):
    vegetarian_dishes = planner.filter_dishes_by_preferences(dishes, ["vegetarian"])
    assert vegetarian_dishes
    assert all("vegetarian" in {tag.lower() for tag in dish.tags} for dish in vegetarian_dishes)


def test_create_nutrition_analysis_produces_meal_options(dishes, tmp_path):
    user = planner.UserProfile(
        age=32,
        gender="Male",
        weight_kg=72,
        height_cm=178,
        goal="Muscle Gain",
        dietary_preferences=["low-sugar"],
        meals_per_day=3,
        activity_level="moderate",
    )

    report = planner.create_nutrition_analysis(user=user, dishes=dishes, alternatives=2, random_seed=1)

    options = report["meal_plan_options"]
    assert len(options) == 2
    for option in options:
        assert len(option["meals"]) == user.meals_per_day
        assert option["score"] >= 0
        totals = option["totals"]
        assert totals["calories"] > 0
    best_option = options[0]
    totals = best_option["totals"]
    target_calories = report["targets"]["target_calories"]
    assert abs(totals["calories"] - target_calories) / target_calories < 0.45


def test_excel_export_contains_dishes(dishes, tmp_path):
    user = planner.UserProfile(
        age=35,
        gender="Male",
        weight_kg=85,
        height_cm=185,
        goal="Maintenance",
    )
    report = planner.create_nutrition_analysis(user=user, dishes=dishes, alternatives=1, random_seed=2)
    excel_path = tmp_path / "report.xlsx"
    planner.export_report_to_excel(report, excel_path)
    assert excel_path.exists()

    with zipfile.ZipFile(excel_path, "r") as archive:
        sheet_xml = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
    first_option = report["meal_plan_options"][0]
    for meal in first_option["meals"]:
        assert meal["dish_name"] in sheet_xml


def test_generate_visualisations_creates_images(dishes, tmp_path):
    user = planner.UserProfile(
        age=40,
        gender="Female",
        weight_kg=70,
        height_cm=170,
        goal="Weight Loss",
    )
    report = planner.create_nutrition_analysis(user=user, dishes=dishes, alternatives=1, random_seed=3)
    paths = planner.generate_visualisations(report, tmp_path)
    for path in paths.values():
        assert path.exists()
        assert path.stat().st_size > 0


def test_generate_synthetic_history(dishes, tmp_path):
    output = planner.generate_synthetic_history(dishes, num_records=5, output_path=tmp_path / "history.csv", random_seed=4)
    assert output.exists()
    rows = output.read_text().strip().splitlines()
    assert len(rows) == 6  # header + 5 records