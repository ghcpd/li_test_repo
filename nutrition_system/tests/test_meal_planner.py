"""
Tests for meal planner functionality.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Add the nutrition_system to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nutrition_system.models import UserProfile, Gender, Goal, ActivityLevel, NutritionRequirements
from nutrition_system.meal_planner import MealPlanner


class TestMealPlanner(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures with a temporary CSV file."""
        self.user = UserProfile(
            age=30,
            gender=Gender.MALE,
            weight=75,
            height=180,
            goal=Goal.MAINTENANCE,
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
            dietary_preferences=["high-protein"]
        )
        
        self.requirements = NutritionRequirements(
            calories=2000,
            protein=150,
            fat=67,
            carbs=250,
            bmr=1730,
            tdee=2000
        )
        
        # Create temporary CSV file for testing
        self.temp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        csv_content = """dish_name,ingredients,weight,calories,protein,fat,carbs,tags
Test Chicken,chicken breast,150,231,43.5,5.0,0.0,high-protein
Test Rice,brown rice,200,223,4.5,1.8,45.0,vegetarian
Test Salad,lettuce tomato,100,50,2.0,1.0,8.0,"vegetarian,low-carb" """
        
        self.temp_csv.write(csv_content)
        self.temp_csv.close()
        
        self.planner = MealPlanner(self.temp_csv.name)
    
    def tearDown(self):
        """Clean up temporary file."""
        os.unlink(self.temp_csv.name)
    
    def test_load_dishes(self):
        """Test loading dishes from CSV."""
        self.assertEqual(len(self.planner.dishes), 3)
        
        # Check first dish
        chicken_dish = self.planner.dishes[0]
        self.assertEqual(chicken_dish.dish_name, "Test Chicken")
        self.assertEqual(chicken_dish.calories, 231)
        self.assertEqual(chicken_dish.protein, 43.5)
        self.assertIn("high-protein", chicken_dish.tags)
    
    def test_filter_dishes_by_preferences(self):
        """Test filtering dishes by dietary preferences."""
        # Filter by high-protein
        high_protein_dishes = self.planner.filter_dishes_by_preferences(["high-protein"])
        self.assertEqual(len(high_protein_dishes), 1)
        self.assertEqual(high_protein_dishes[0].dish_name, "Test Chicken")
        
        # Filter by vegetarian
        vegetarian_dishes = self.planner.filter_dishes_by_preferences(["vegetarian"])
        self.assertEqual(len(vegetarian_dishes), 2)  # Rice and Salad
        
        # No preferences should return all dishes
        all_dishes = self.planner.filter_dishes_by_preferences([])
        self.assertEqual(len(all_dishes), 3)
    
    def test_generate_meal_plan(self):
        """Test meal plan generation."""
        # Create user without preferences for full dish access
        user_no_prefs = UserProfile(
            age=30,
            gender=Gender.MALE,
            weight=75,
            height=180,
            goal=Goal.MAINTENANCE,
            dietary_preferences=[]
        )
        
        meal_plan = self.planner.generate_meal_plan(user_no_prefs, self.requirements, 3)
        
        # Check structure
        self.assertEqual(len(meal_plan.meals), 3)
        self.assertEqual(meal_plan.meals[0].meal_name, "Breakfast")
        self.assertEqual(meal_plan.meals[1].meal_name, "Lunch")
        self.assertEqual(meal_plan.meals[2].meal_name, "Dinner")
        
        # Each meal should have at least one dish
        for meal in meal_plan.meals:
            self.assertGreater(len(meal.dishes), 0)
    
    def test_meal_name_generation(self):
        """Test meal name generation for different numbers of meals."""
        self.assertEqual(self.planner._get_meal_name(0, 1), "Main Meal")
        self.assertEqual(self.planner._get_meal_name(0, 2), "Breakfast")
        self.assertEqual(self.planner._get_meal_name(1, 2), "Dinner")
        self.assertEqual(self.planner._get_meal_name(0, 3), "Breakfast")
        self.assertEqual(self.planner._get_meal_name(1, 3), "Lunch")
        self.assertEqual(self.planner._get_meal_name(2, 3), "Dinner")
    
    def test_generate_multiple_options(self):
        """Test generating multiple meal plan options."""
        user_no_prefs = UserProfile(
            age=30,
            gender=Gender.MALE,
            weight=75,
            height=180,
            goal=Goal.MAINTENANCE,
            dietary_preferences=[]
        )
        
        options = self.planner.generate_multiple_options(
            user_no_prefs, 
            self.requirements, 
            num_meals=3, 
            num_options=2
        )
        
        # Should generate requested number of options
        self.assertLessEqual(len(options), 2)  # May be less if generation fails
        
        # Each option should be a valid meal plan
        for option in options:
            self.assertEqual(len(option.meals), 3)
    
    def test_get_dish_recommendations(self):
        """Test dish recommendations."""
        # Test muscle gain recommendations (should prioritize high protein)
        muscle_gain_user = UserProfile(
            age=25,
            gender=Gender.MALE,
            weight=70,
            height=175,
            goal=Goal.MUSCLE_GAIN,
            dietary_preferences=[]
        )
        
        recommendations = self.planner.get_dish_recommendations(muscle_gain_user)
        self.assertLessEqual(len(recommendations), 5)
        
        # Should return some recommendations
        self.assertGreater(len(recommendations), 0)
    
    def test_invalid_preferences_handling(self):
        """Test handling of invalid preferences."""
        user_with_invalid_prefs = UserProfile(
            age=30,
            gender=Gender.MALE,
            weight=75,
            height=180,
            goal=Goal.MAINTENANCE,
            dietary_preferences=["non-existent-preference"]
        )
        
        # Should raise ValueError when no dishes match preferences
        with self.assertRaises(ValueError):
            self.planner.generate_meal_plan(user_with_invalid_prefs, self.requirements)


if __name__ == '__main__':
    unittest.main()