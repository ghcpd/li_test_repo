import json
import tempfile
from pathlib import Path
from unittest import TestCase

from nutrition_system import (
    UserProfile,
    calculate_bmr,
    calculate_daily_targets,
    export_plan_to_excel,
    export_plan_to_pdf,
    generate_macro_charts,
    generate_meal_plans,
    generate_synthetic_user_dataset,
    load_dish_database,
)


class NutritionSystemTests(TestCase):
    def setUp(self) -> None:
        self.profile = UserProfile(
            age=32,
            gender="Female",
            weight_kg=62,
            height_cm=165,
            goal="weight loss",
            activity_level="light",
        )
        self.dishes = load_dish_database()

    def test_calculate_bmr(self) -> None:
        bmr = calculate_bmr(self.profile)
        self.assertAlmostEqual(bmr, 1330.25, places=2)

    def test_daily_targets_structure(self) -> None:
        targets = calculate_daily_targets(self.profile)
        self.assertIn("target_calories", targets)
        macro_targets = targets["macro_targets"]
        self.assertGreater(macro_targets["protein"], 0)
        self.assertGreater(macro_targets["fat"], 0)
        self.assertGreater(macro_targets["carbs"], 0)

    def test_generate_meal_plan(self) -> None:
        plans = generate_meal_plans(
            self.profile,
            self.dishes,
            meals_per_day=[3],
            top_n=2,
            tolerance=0.5,
        )
        self.assertIn(3, plans)
        self.assertTrue(plans[3])
        plan = plans[3][0]
        self.assertIn("details", plan)
        self.assertTrue(all("dish_name" in detail for detail in plan["details"]))

    def test_dietary_preferences(self) -> None:
        vegetarian_profile = UserProfile(
            age=28,
            gender="Male",
            weight_kg=75,
            height_cm=180,
            goal="maintenance",
            activity_level="moderate",
            dietary_preferences=["Vegetarian"],
        )
        plans = generate_meal_plans(
            vegetarian_profile,
            self.dishes,
            meals_per_day=[2],
            top_n=1,
            tolerance=1.0,
        )
        self.assertTrue(plans[2])
        plan = plans[2][0]
        for detail in plan["details"]:
            self.assertIn("Vegetarian", detail["tags"])  # only vegetarian dishes should appear

    def test_export_functions(self) -> None:
        plans = generate_meal_plans(
            self.profile,
            self.dishes,
            meals_per_day=[3],
            top_n=1,
            tolerance=0.5,
        )
        plan = plans[3][0]
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            chart_paths = generate_macro_charts(
                totals=plan["totals"],
                meal_details=plan["details"],
                output_dir=tmp_path,
                prefix="test",
            )
            for path in chart_paths.values():
                self.assertTrue(path.exists())
            excel_file = export_plan_to_excel(plan, tmp_path / "plan.xlsx")
            self.assertTrue(excel_file.exists())
            pdf_file = export_plan_to_pdf(
                self.profile,
                plan,
                output_path=tmp_path / "plan.pdf",
                chart_paths=chart_paths,
            )
            self.assertTrue(pdf_file.exists())

    def test_synthetic_dataset_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / "synthetic_users.json"
            dataset = generate_synthetic_user_dataset(5, output_path=output_file)
            self.assertEqual(len(dataset), 5)
            self.assertTrue(output_file.exists())
            with output_file.open("r", encoding="utf-8") as file:
                loaded = json.load(file)
            self.assertEqual(len(loaded), 5)
            self.assertIn("targets", loaded[0])