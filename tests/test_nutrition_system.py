import json
import os
import random
import tempfile
import unittest

from nutrition_system import (
    Dish,
    MealPlanGenerator,
    UserProfile,
    calculate_bmr,
    caloric_target,
    create_macro_pie_chart,
    create_meal_bar_chart,
    export_plan_to_excel,
    export_report_pdf,
    generate_meal_plan,
    generate_synthetic_dataset,
    load_dishes,
    macro_targets,
)


DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "dishes.json")


class NutritionSystemTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dishes = load_dishes(DATA_PATH)

    def test_calculate_bmr(self):
        male_profile = UserProfile(age=30, gender="male", weight=80, height=180, goal="maintenance")
        female_profile = UserProfile(age=30, gender="female", weight=65, height=165, goal="maintenance")
        male_bmr = calculate_bmr(male_profile)
        female_bmr = calculate_bmr(female_profile)
        self.assertAlmostEqual(male_bmr, 1780, delta=1)
        self.assertAlmostEqual(female_bmr, 1370.25, delta=1)

    def test_generate_meal_plan(self):
        profile = UserProfile(
            age=28,
            gender="female",
            weight=62,
            height=170,
            goal="weight_loss",
            dietary_preferences=["vegetarian"],
        )
        random.seed(42)
        primary_plan, plans, target_calories, targets = generate_meal_plan(
            profile,
            self.dishes,
            meals_per_day=3,
            num_options=2,
        )
        self.assertGreaterEqual(len(plans), 1)
        self.assertLessEqual(primary_plan.meal_count, 3)
        self.assertAlmostEqual(primary_plan.totals["calories"], target_calories, delta=300)
        self.assertAlmostEqual(primary_plan.totals["protein"], targets["protein"], delta=30)

    def test_visualizations_and_exports(self):
        profile = UserProfile(age=40, gender="male", weight=85, height=185, goal="muscle_gain")
        target_calories = caloric_target(profile)
        targets = macro_targets(target_calories, profile.goal)
        generator = MealPlanGenerator(self.dishes)
        random.seed(24)
        plans = generator.generate_plans(target_calories, targets, meals_per_day=3, num_options=1)
        plan = plans[0]

        with tempfile.TemporaryDirectory() as tmp_dir:
            pie_chart = create_macro_pie_chart(plan, tmp_dir)
            self.assertTrue(os.path.exists(pie_chart))

            bar_charts = create_meal_bar_chart(plan, tmp_dir)
            for path in bar_charts.split(";"):
                self.assertTrue(os.path.exists(path))

            pdf_path = os.path.join(tmp_dir, "report.pdf")
            export_report_pdf(plan, profile, target_calories, targets, pdf_path, pie_chart, bar_charts)
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 0)

            excel_path = os.path.join(tmp_dir, "plan.xls")
            export_plan_to_excel(plan, targets, excel_path)
            self.assertTrue(os.path.exists(excel_path))
            with open(excel_path, "r", encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("Workbook", content)

            dataset_path = os.path.join(tmp_dir, "synthetic.json")
            generate_synthetic_dataset(5, dataset_path)
            self.assertTrue(os.path.exists(dataset_path))
            with open(dataset_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(len(data), 5)
            for entry in data:
                self.assertIn("profile", entry)
                self.assertIn("target_calories", entry)
                self.assertIn("macro_targets", entry)


if __name__ == "__main__":
    unittest.main()