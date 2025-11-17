import math
import tempfile
import unittest
import zipfile
from pathlib import Path

from nutrition import (
    DishDatabase,
    NutritionGoals,
    UserProfile,
    calculate_bmr,
    generate_meal_plan_options,
    generate_nutrition_report,
)


class NutritionSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = DishDatabase.load_default()

    def test_calculate_bmr(self) -> None:
        male_profile = UserProfile(age=30, gender="Male", weight=80, height=180, goal=NutritionGoals.MAINTENANCE)
        female_profile = UserProfile(age=28, gender="Female", weight=65, height=170, goal=NutritionGoals.MAINTENANCE)

        male_bmr = calculate_bmr(male_profile)
        female_bmr = calculate_bmr(female_profile)

        self.assertTrue(math.isclose(male_bmr, 1780.0, rel_tol=1e-3))
        self.assertTrue(math.isclose(female_bmr, 1411.5, rel_tol=1e-3))

    def test_generate_meal_plan_respects_preferences(self) -> None:
        profile = UserProfile(age=34, gender="Female", weight=72, height=168, goal=NutritionGoals.WEIGHT_LOSS)
        calories, macros, plans = generate_meal_plan_options(
            profile,
            self.database,
            activity_factor=1.45,
            preferences=["Vegetarian"],
            num_meals=3,
            alternatives=2,
        )

        self.assertEqual(len(plans), 2)
        best_plan = plans[0]
        self.assertLess(best_plan.total_calories, profile.weight * 40)
        for meal in best_plan.meal_breakdown:
            self.assertIn("Vegetarian", meal["tags"])

        # Ensure totals are aligned with calculated macros
        tolerance = 0.45  # 45% tolerance for macro ranges to accommodate available dishes
        for macro_name, target_value in macros.items():
            self.assertTrue(
                math.isclose(best_plan.macro_totals[macro_name], target_value, rel_tol=tolerance),
                msg=f"{macro_name} differs too much",
            )
        self.assertTrue(math.isclose(best_plan.total_calories, calories, rel_tol=0.25))

    def test_report_produces_charts_and_excel(self) -> None:
        profile = UserProfile(age=40, gender="Male", weight=85, height=182, goal=NutritionGoals.MAINTENANCE)
        with tempfile.TemporaryDirectory() as tmp_dir:
            chart_dir = Path(tmp_dir) / "charts"
            report = generate_nutrition_report(
                profile,
                activity_factor=1.3,
                database=self.database,
                preferences=["Low-Salt"],
                num_meals=3,
                alternatives=2,
                chart_dir=chart_dir,
            )
            self.assertTrue(report.charts)
            for path in report.charts.values():
                self.assertTrue(path.exists())

            excel_path = Path(tmp_dir) / "nutrition_report.xlsx"
            created_path = report.export_to_excel(excel_path)
            self.assertEqual(created_path, excel_path)
            self.assertTrue(created_path.exists())
            with zipfile.ZipFile(created_path, "r") as zf:
                self.assertIn("xl/worksheets/sheet1.xml", zf.namelist())

            # Include a basic sanity check for the best plan
            best_plan = report.best_plan
            self.assertGreater(best_plan.total_calories, 0)
            self.assertEqual(len(best_plan.dishes), 3)


if __name__ == "__main__":  # pragma: no cover - test module execution helper
    unittest.main()