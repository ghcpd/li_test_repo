"""
Tests for nutrition calculator functionality.
"""

import unittest
import sys
from pathlib import Path

# Add the nutrition_system to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nutrition_system.models import UserProfile, Gender, Goal, ActivityLevel
from nutrition_system.nutrition_calculator import NutritionCalculator


class TestNutritionCalculator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.male_user = UserProfile(
            age=30,
            gender=Gender.MALE,
            weight=75,
            height=180,
            goal=Goal.MAINTENANCE,
            activity_level=ActivityLevel.MODERATELY_ACTIVE
        )
        
        self.female_user = UserProfile(
            age=25,
            gender=Gender.FEMALE,
            weight=60,
            height=165,
            goal=Goal.WEIGHT_LOSS,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE
        )
    
    def test_calculate_bmr_male(self):
        """Test BMR calculation for male user."""
        bmr = NutritionCalculator.calculate_bmr(self.male_user)
        # Expected: 10*75 + 6.25*180 - 5*30 + 5 = 750 + 1125 - 150 + 5 = 1730
        self.assertEqual(bmr, 1730.0)
    
    def test_calculate_bmr_female(self):
        """Test BMR calculation for female user."""
        bmr = NutritionCalculator.calculate_bmr(self.female_user)
        # Expected: 10*60 + 6.25*165 - 5*25 - 161 = 600 + 1031.25 - 125 - 161 = 1345.25
        self.assertEqual(bmr, 1345.25)
    
    def test_calculate_tdee(self):
        """Test TDEE calculation."""
        bmr = 1730.0
        activity_multiplier = ActivityLevel.MODERATELY_ACTIVE.value  # 1.55
        tdee = NutritionCalculator.calculate_tdee(bmr, activity_multiplier)
        expected_tdee = 1730.0 * 1.55
        self.assertEqual(tdee, expected_tdee)
    
    def test_adjust_calories_for_weight_loss(self):
        """Test calorie adjustment for weight loss goal."""
        tdee = 2000.0
        adjusted = NutritionCalculator.adjust_calories_for_goal(tdee, Goal.WEIGHT_LOSS)
        self.assertEqual(adjusted, 1500.0)  # 2000 - 500
    
    def test_adjust_calories_for_muscle_gain(self):
        """Test calorie adjustment for muscle gain goal."""
        tdee = 2000.0
        adjusted = NutritionCalculator.adjust_calories_for_goal(tdee, Goal.MUSCLE_GAIN)
        self.assertEqual(adjusted, 2300.0)  # 2000 + 300
    
    def test_adjust_calories_for_maintenance(self):
        """Test calorie adjustment for maintenance goal."""
        tdee = 2000.0
        adjusted = NutritionCalculator.adjust_calories_for_goal(tdee, Goal.MAINTENANCE)
        self.assertEqual(adjusted, 2000.0)  # No change
    
    def test_macronutrient_distribution_weight_loss(self):
        """Test macronutrient distribution for weight loss."""
        calories = 1500.0
        macros = NutritionCalculator.calculate_macronutrient_distribution(calories, Goal.WEIGHT_LOSS)
        
        # Weight loss: 30% protein, 25% fat, 45% carbs
        expected_protein = (1500 * 0.30) / 4  # 112.5g
        expected_fat = (1500 * 0.25) / 9      # ~41.67g
        expected_carbs = (1500 * 0.45) / 4    # 168.75g
        
        self.assertAlmostEqual(macros['protein'], expected_protein, places=2)
        self.assertAlmostEqual(macros['fat'], expected_fat, places=2)
        self.assertAlmostEqual(macros['carbs'], expected_carbs, places=2)
    
    def test_calculate_complete_requirements(self):
        """Test complete requirements calculation."""
        requirements = NutritionCalculator.calculate_requirements(self.male_user)
        
        # Verify all fields are populated
        self.assertIsNotNone(requirements.bmr)
        self.assertIsNotNone(requirements.tdee)
        self.assertIsNotNone(requirements.calories)
        self.assertIsNotNone(requirements.protein)
        self.assertIsNotNone(requirements.fat)
        self.assertIsNotNone(requirements.carbs)
        
        # Verify BMR calculation
        self.assertEqual(requirements.bmr, 1730.0)
        
        # Verify TDEE calculation
        expected_tdee = 1730.0 * 1.55
        self.assertEqual(requirements.tdee, expected_tdee)


if __name__ == '__main__':
    unittest.main()