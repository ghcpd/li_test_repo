"""
Unit tests for the Nutrition Analysis & Meal Plan Recommendation System
"""

import unittest
import json
import os
from nutrition_analysis import NutritionAnalyzer
from meal_planner import MealPlanner
from report_generator import ReportGenerator


class TestNutritionAnalyzer(unittest.TestCase):
    """Test cases for NutritionAnalyzer class."""
    
    def test_bmr_calculation_male(self):
        """Test BMR calculation for males."""
        analyzer = NutritionAnalyzer(
            age=30,
            gender='male',
            weight=75,
            height=175,
            goal='maintenance'
        )
        # Expected: 10*75 + 6.25*175 - 5*30 + 5 = 750 + 1093.75 - 150 + 5 = 1698.75
        self.assertAlmostEqual(analyzer.bmr, 1698.75, places=2)
    
    def test_bmr_calculation_female(self):
        """Test BMR calculation for females."""
        analyzer = NutritionAnalyzer(
            age=25,
            gender='female',
            weight=60,
            height=165,
            goal='maintenance'
        )
        # Expected: 10*60 + 6.25*165 - 5*25 - 161 = 600 + 1031.25 - 125 - 161 = 1345.25
        self.assertAlmostEqual(analyzer.bmr, 1345.25, places=2)
    
    def test_tdee_calculation(self):
        """Test TDEE calculation."""
        analyzer = NutritionAnalyzer(
            age=30,
            gender='male',
            weight=75,
            height=175,
            goal='maintenance',
            activity_level='moderate'
        )
        expected_tdee = analyzer.bmr * 1.55
        self.assertAlmostEqual(analyzer.tdee, expected_tdee, places=2)
    
    def test_weight_loss_target(self):
        """Test calorie target for weight loss."""
        analyzer = NutritionAnalyzer(
            age=30,
            gender='male',
            weight=75,
            height=175,
            goal='weight_loss',
            activity_level='moderate'
        )
        # Should be 15% below TDEE
        expected_target = analyzer.tdee * 0.85
        self.assertAlmostEqual(analyzer.target_calories, expected_target, places=2)
    
    def test_muscle_gain_target(self):
        """Test calorie target for muscle gain."""
        analyzer = NutritionAnalyzer(
            age=30,
            gender='male',
            weight=75,
            height=175,
            goal='muscle_gain',
            activity_level='moderate'
        )
        # Should be 10% above TDEE
        expected_target = analyzer.tdee * 1.10
        self.assertAlmostEqual(analyzer.target_calories, expected_target, places=2)
    
    def test_maintenance_target(self):
        """Test calorie target for maintenance."""
        analyzer = NutritionAnalyzer(
            age=30,
            gender='male',
            weight=75,
            height=175,
            goal='maintenance',
            activity_level='moderate'
        )
        # Should be equal to TDEE
        self.assertAlmostEqual(analyzer.target_calories, analyzer.tdee, places=2)
    
    def test_macro_calculation(self):
        """Test macronutrient calculation."""
        analyzer = NutritionAnalyzer(
            age=30,
            gender='male',
            weight=75,
            height=175,
            goal='maintenance',
            activity_level='moderate'
        )
        macros = analyzer.macros
        
        # Check that all macros are present
        self.assertIn('protein', macros)
        self.assertIn('fat', macros)
        self.assertIn('carbs', macros)
        
        # Check that macros are positive
        self.assertGreater(macros['protein'], 0)
        self.assertGreater(macros['fat'], 0)
        self.assertGreater(macros['carbs'], 0)
        
        # Check that total calories from macros approximately equals target
        total_cals = macros['protein'] * 4 + macros['fat'] * 9 + macros['carbs'] * 4
        self.assertAlmostEqual(total_cals, analyzer.target_calories, delta=10)


class TestMealPlanner(unittest.TestCase):
    """Test cases for MealPlanner class."""
    
    @classmethod
    def setUpClass(cls):
        """Create a temporary dish database for testing."""
        cls.test_db_path = '/tmp/test_dishes.json'
        test_dishes = [
            {
                "dish_name": "Test Chicken",
                "ingredients": ["Chicken"],
                "weight": 150,
                "calories": 165,
                "protein": 31,
                "fat": 3.6,
                "carbs": 0,
                "tags": ["High-protein"]
            },
            {
                "dish_name": "Test Rice",
                "ingredients": ["Rice"],
                "weight": 195,
                "calories": 216,
                "protein": 5,
                "fat": 1.8,
                "carbs": 45,
                "tags": ["Vegetarian"]
            },
            {
                "dish_name": "Test Salad",
                "ingredients": ["Vegetables"],
                "weight": 100,
                "calories": 50,
                "protein": 3,
                "fat": 2,
                "carbs": 7,
                "tags": ["Vegetarian", "Low-calorie"]
            }
        ]
        with open(cls.test_db_path, 'w') as f:
            json.dump(test_dishes, f)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up temporary database."""
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
    
    def test_load_database(self):
        """Test loading dish database."""
        planner = MealPlanner(self.test_db_path)
        self.assertEqual(len(planner.dishes), 3)
    
    def test_filter_dishes_no_preferences(self):
        """Test filtering with no preferences."""
        planner = MealPlanner(self.test_db_path)
        filtered = planner.filter_dishes(None)
        self.assertEqual(len(filtered), 3)
    
    def test_filter_dishes_with_preferences(self):
        """Test filtering with preferences."""
        planner = MealPlanner(self.test_db_path)
        filtered = planner.filter_dishes(['Vegetarian'])
        self.assertEqual(len(filtered), 2)
    
    def test_calculate_meal_nutrition(self):
        """Test nutrition calculation for meals."""
        planner = MealPlanner(self.test_db_path)
        meals = [planner.dishes[0], planner.dishes[1]]
        totals = planner.calculate_meal_nutrition(meals)
        
        self.assertEqual(totals['calories'], 381)
        self.assertEqual(totals['protein'], 36)
        self.assertAlmostEqual(totals['fat'], 5.4, places=1)
        self.assertEqual(totals['carbs'], 45)
    
    def test_generate_meal_plan(self):
        """Test meal plan generation."""
        planner = MealPlanner(self.test_db_path)
        plans = planner.generate_meal_plan(
            target_calories=500,
            target_protein=40,
            target_fat=10,
            target_carbs=50,
            num_meals=2,
            preferences=None,
            num_options=2
        )
        
        self.assertEqual(len(plans), 2)
        self.assertIn('meals', plans[0])
        self.assertIn('total_nutrition', plans[0])
        self.assertEqual(len(plans[0]['meals']), 2)
    
    def test_get_dish_by_name(self):
        """Test retrieving dish by name."""
        planner = MealPlanner(self.test_db_path)
        dish = planner.get_dish_by_name('Test Chicken')
        self.assertIsNotNone(dish)
        self.assertEqual(dish['dish_name'], 'Test Chicken')
        
        not_found = planner.get_dish_by_name('Non-existent Dish')
        self.assertIsNone(not_found)


class TestReportGenerator(unittest.TestCase):
    """Test cases for ReportGenerator class."""
    
    def setUp(self):
        """Set up test data."""
        self.nutrition_analysis = {
            'user_info': {
                'age': 30,
                'gender': 'male',
                'weight': 75,
                'height': 175,
                'goal': 'maintenance',
                'activity_level': 'moderate'
            },
            'bmr': 1698.75,
            'tdee': 2633.06,
            'target_calories': 2633.06,
            'macros': {
                'protein': 164.57,
                'fat': 87.77,
                'carbs': 296.22
            }
        }
        
        self.meal_plan = {
            'option_number': 1,
            'meals': [
                {
                    'dish_name': 'Test Meal 1',
                    'weight': 150,
                    'calories': 200,
                    'protein': 25,
                    'fat': 8,
                    'carbs': 15,
                    'ingredients': ['Ingredient 1'],
                    'tags': ['High-protein']
                },
                {
                    'dish_name': 'Test Meal 2',
                    'weight': 200,
                    'calories': 300,
                    'protein': 10,
                    'fat': 15,
                    'carbs': 35,
                    'ingredients': ['Ingredient 2'],
                    'tags': ['Vegetarian']
                }
            ],
            'total_nutrition': {
                'calories': 500,
                'protein': 35,
                'fat': 23,
                'carbs': 50
            },
            'target_nutrition': {
                'calories': 2633.06,
                'protein': 164.57,
                'fat': 87.77,
                'carbs': 296.22
            },
            'accuracy': {
                'calories_diff': -2133.06,
                'protein_diff': -129.57,
                'fat_diff': -64.77,
                'carbs_diff': -246.22
            }
        }
    
    def test_report_generator_initialization(self):
        """Test ReportGenerator initialization."""
        report_gen = ReportGenerator(self.nutrition_analysis, self.meal_plan)
        self.assertIsNotNone(report_gen.nutrition_analysis)
        self.assertIsNotNone(report_gen.meal_plan)
    
    def test_create_pie_chart(self):
        """Test pie chart creation."""
        report_gen = ReportGenerator(self.nutrition_analysis, self.meal_plan)
        chart_path = '/tmp/test_pie_chart.png'
        result = report_gen.create_pie_chart(chart_path)
        
        self.assertEqual(result, chart_path)
        self.assertTrue(os.path.exists(chart_path))
        
        # Clean up
        if os.path.exists(chart_path):
            os.remove(chart_path)
    
    def test_create_bar_chart(self):
        """Test bar chart creation."""
        report_gen = ReportGenerator(self.nutrition_analysis, self.meal_plan)
        chart_path = '/tmp/test_bar_chart.png'
        result = report_gen.create_bar_chart(chart_path)
        
        self.assertEqual(result, chart_path)
        self.assertTrue(os.path.exists(chart_path))
        
        # Clean up
        if os.path.exists(chart_path):
            os.remove(chart_path)
    
    def test_export_to_pdf(self):
        """Test PDF export."""
        report_gen = ReportGenerator(self.nutrition_analysis, self.meal_plan)
        pdf_path = '/tmp/test_report.pdf'
        result = report_gen.export_to_pdf(pdf_path)
        
        self.assertEqual(result, pdf_path)
        self.assertTrue(os.path.exists(pdf_path))
        
        # Clean up
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    
    def test_export_to_excel(self):
        """Test Excel export."""
        report_gen = ReportGenerator(self.nutrition_analysis, self.meal_plan)
        excel_path = '/tmp/test_report.xlsx'
        result = report_gen.export_to_excel(excel_path)
        
        self.assertEqual(result, excel_path)
        self.assertTrue(os.path.exists(excel_path))
        
        # Clean up
        if os.path.exists(excel_path):
            os.remove(excel_path)


if __name__ == '__main__':
    unittest.main()
