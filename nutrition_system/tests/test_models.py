"""
Tests for data models.
"""

import unittest
import sys
from pathlib import Path

# Add the nutrition_system to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nutrition_system.models import UserProfile, Dish, Meal, MealPlan, Gender, Goal, ActivityLevel, NutritionRequirements


class TestModels(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.dish1 = Dish(
            dish_name="Grilled Chicken",
            ingredients=["chicken", "herbs"],
            weight=150,
            calories=231,
            protein=43.5,
            fat=5.0,
            carbs=0.0,
            tags=["high-protein", "low-carb"]
        )
        
        self.dish2 = Dish(
            dish_name="Brown Rice",
            ingredients=["brown rice"],
            weight=200,
            calories=223,
            protein=4.5,
            fat=1.8,
            carbs=45.0,
            tags=["vegetarian", "whole-grain"]
        )
        
        self.meal = Meal(
            meal_name="Lunch",
            dishes=[self.dish1, self.dish2]
        )
        
        self.requirements = NutritionRequirements(
            calories=2000,
            protein=150,
            fat=67,
            carbs=250,
            bmr=1730,
            tdee=2000
        )
        
        self.meal_plan = MealPlan(
            meals=[self.meal],
            user_requirements=self.requirements
        )
    
    def test_user_profile_creation(self):
        """Test UserProfile creation."""
        user = UserProfile(
            age=30,
            gender=Gender.MALE,
            weight=75,
            height=180,
            goal=Goal.MAINTENANCE
        )
        
        self.assertEqual(user.age, 30)
        self.assertEqual(user.gender, Gender.MALE)
        self.assertEqual(user.weight, 75)
        self.assertEqual(user.height, 180)
        self.assertEqual(user.goal, Goal.MAINTENANCE)
        self.assertEqual(user.dietary_preferences, [])  # Default empty list
    
    def test_dish_meets_preferences(self):
        """Test dish preference matching."""
        # Test matching preferences
        self.assertTrue(self.dish1.meets_preferences(["high-protein"]))
        self.assertTrue(self.dish1.meets_preferences(["HIGH-PROTEIN"]))  # Case insensitive
        self.assertTrue(self.dish2.meets_preferences(["vegetarian"]))
        
        # Test non-matching preferences
        self.assertFalse(self.dish1.meets_preferences(["vegetarian"]))
        self.assertFalse(self.dish2.meets_preferences(["high-protein"]))
        
        # Test empty preferences (should return True)
        self.assertTrue(self.dish1.meets_preferences([]))
        self.assertTrue(self.dish1.meets_preferences(None))
    
    def test_meal_totals(self):
        """Test meal nutritional totals."""
        expected_calories = self.dish1.calories + self.dish2.calories  # 231 + 223 = 454
        expected_protein = self.dish1.protein + self.dish2.protein    # 43.5 + 4.5 = 48.0
        expected_fat = self.dish1.fat + self.dish2.fat                # 5.0 + 1.8 = 6.8
        expected_carbs = self.dish1.carbs + self.dish2.carbs          # 0.0 + 45.0 = 45.0
        
        self.assertEqual(self.meal.total_calories, expected_calories)
        self.assertEqual(self.meal.total_protein, expected_protein)
        self.assertEqual(self.meal.total_fat, expected_fat)
        self.assertEqual(self.meal.total_carbs, expected_carbs)
    
    def test_meal_plan_totals(self):
        """Test meal plan nutritional totals."""
        # Since meal plan has only one meal
        self.assertEqual(self.meal_plan.total_calories, self.meal.total_calories)
        self.assertEqual(self.meal_plan.total_protein, self.meal.total_protein)
        self.assertEqual(self.meal_plan.total_fat, self.meal.total_fat)
        self.assertEqual(self.meal_plan.total_carbs, self.meal.total_carbs)
    
    def test_nutrition_summary(self):
        """Test nutrition summary generation."""
        summary = self.meal_plan.get_nutrition_summary()
        
        expected_summary = {
            "calories": 454.0,
            "protein": 48.0,
            "fat": 6.8,
            "carbs": 45.0
        }
        
        self.assertEqual(summary, expected_summary)
    
    def test_macro_percentages(self):
        """Test macronutrient percentage calculation."""
        percentages = self.meal_plan.get_macro_percentages()
        
        total_calories = 454.0
        expected_protein_pct = (48.0 * 4 / total_calories) * 100  # ~42.3%
        expected_fat_pct = (6.8 * 9 / total_calories) * 100       # ~13.5%
        expected_carbs_pct = (45.0 * 4 / total_calories) * 100    # ~39.6%
        
        self.assertAlmostEqual(percentages["protein"], expected_protein_pct, places=1)
        self.assertAlmostEqual(percentages["fat"], expected_fat_pct, places=1)
        self.assertAlmostEqual(percentages["carbs"], expected_carbs_pct, places=1)
    
    def test_macro_percentages_zero_calories(self):
        """Test macro percentage calculation with zero calories."""
        empty_meal = Meal("Empty", [])
        empty_plan = MealPlan([empty_meal], self.requirements)
        
        percentages = empty_plan.get_macro_percentages()
        
        self.assertEqual(percentages["protein"], 0)
        self.assertEqual(percentages["fat"], 0)
        self.assertEqual(percentages["carbs"], 0)


if __name__ == '__main__':
    unittest.main()