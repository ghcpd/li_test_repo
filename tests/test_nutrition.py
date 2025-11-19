"""Unit tests for the nutrition analysis and meal planning system."""

from __future__ import annotations

import os
import tempfile
import unittest

from nutrition.analyzer import NutritionAnalyzer
from nutrition.dataset import load_dishes
from nutrition.models import MealPlan, UserProfile
from nutrition.planner import MealPlanRecommender
from nutrition.report import NutritionReport
from nutrition.synthetic import generate_synthetic_user_dataset


def build_sample_user(goal: str = "Weight Loss", preferences: list[str] | None = None) -> UserProfile:
    return UserProfile(
        age=30,
        height=175,
        weight=72,
        gender="male",
        goal=goal,
        activity_factor=1.2,
        dietary_preferences=preferences or [],
    )


class NutritionSystemTests(unittest.TestCase):
    def test_bmr_and_macros_calculation(self) -> None:
        male_user = build_sample_user(goal="Maintenance")
        analyzer = NutritionAnalyzer(male_user)
        bmr_male = analyzer.calculate_bmr()
        self.assertAlmostEqual(bmr_male, 10 * 72 + 6.25 * 175 - 5 * 30 + 5)

        female_user = UserProfile(
            age=28,
            height=165,
            weight=60,
            gender="female",
            goal="Weight Loss",
            activity_factor=1.35,
            dietary_preferences=[],
        )
        female_analyzer = NutritionAnalyzer(female_user)
        bmr_female = female_analyzer.calculate_bmr()
        self.assertAlmostEqual(bmr_female, 10 * 60 + 6.25 * 165 - 5 * 28 - 161)

        targets = analyzer.build_targets()
        totals = targets.macro_ratios()
        self.assertAlmostEqual(sum(totals.values()), 1.0, places=6)

    def test_meal_plan_recommender_respects_preferences(self) -> None:
        user = build_sample_user(preferences=["vegetarian"])
        analyzer = NutritionAnalyzer(user)
        targets = analyzer.build_targets()
        dishes = load_dishes()
        recommender = MealPlanRecommender(dishes)
        plans = recommender.recommend(user, targets, meals_per_day=3, num_options=1)
        self.assertTrue(plans, "Expected at least one meal plan")
        plan = plans[0]
        self.assertIsInstance(plan, MealPlan)
        for meal in plan.meals:
            self.assertIn("vegetarian", meal.dish.tags)

    def test_report_exports_files(self) -> None:
        user = build_sample_user(goal="Muscle Gain")
        analyzer = NutritionAnalyzer(user)
        targets = analyzer.build_targets()
        dishes = load_dishes()
        plan = MealPlanRecommender(dishes).recommend(
            user, targets, meals_per_day=3, num_options=1
        )[0]
        report = NutritionReport(user, targets, plan)
        pie_svg = report.create_pie_chart_svg()
        bar_svg = report.create_bar_chart_svg()
        self.assertIn("<svg", pie_svg)
        self.assertIn("<svg", bar_svg)
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = report.export_all(tmpdir, base_name="test_report")
            self.assertTrue(artifacts.pdf_path and os.path.exists(artifacts.pdf_path))
            self.assertTrue(artifacts.excel_path and os.path.exists(artifacts.excel_path))
            with open(artifacts.pdf_path, "rb") as pdf_file:
                self.assertEqual(pdf_file.read(4), b"%PDF")
            with open(artifacts.excel_path, "rb") as excel_file:
                self.assertEqual(excel_file.read(2), b"PK")

    def test_generate_synthetic_dataset(self) -> None:
        directory = tempfile.mkdtemp()
        output = os.path.join(directory, "synthetic.csv")
        path = generate_synthetic_user_dataset(output, count=5)
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as handle:
            header = handle.readline().strip()
            self.assertIn("age", header)
            self.assertIn("meal_1", header)


if __name__ == "__main__":
    unittest.main()