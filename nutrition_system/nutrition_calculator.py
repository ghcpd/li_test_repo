"""
Nutrition requirements calculator using Mifflin-St Jeor equation.
"""

from .models import UserProfile, NutritionRequirements, Gender, Goal


class NutritionCalculator:
    """Calculator for BMR, TDEE, and macronutrient requirements."""
    
    @staticmethod
    def calculate_bmr(user: UserProfile) -> float:
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.
        
        Male: BMR = 10*weight + 6.25*height - 5*age + 5
        Female: BMR = 10*weight + 6.25*height - 5*age - 161
        """
        base_calculation = 10 * user.weight + 6.25 * user.height - 5 * user.age
        
        if user.gender == Gender.MALE:
            return base_calculation + 5
        else:
            return base_calculation - 161
    
    @staticmethod
    def calculate_tdee(bmr: float, activity_level_multiplier: float) -> float:
        """Calculate Total Daily Energy Expenditure."""
        return bmr * activity_level_multiplier
    
    @staticmethod
    def adjust_calories_for_goal(tdee: float, goal: Goal) -> float:
        """Adjust TDEE based on user's goal."""
        adjustments = {
            Goal.WEIGHT_LOSS: -500,  # 500 calorie deficit for ~1lb/week loss
            Goal.MUSCLE_GAIN: +300,  # 300 calorie surplus for lean gains
            Goal.MAINTENANCE: 0      # No adjustment
        }
        return tdee + adjustments[goal]
    
    @staticmethod
    def calculate_macronutrient_distribution(calories: float, goal: Goal) -> dict:
        """
        Calculate macronutrient distribution based on goal.
        Returns grams of protein, fat, and carbs.
        """
        distributions = {
            Goal.WEIGHT_LOSS: {"protein": 0.30, "fat": 0.25, "carbs": 0.45},
            Goal.MUSCLE_GAIN: {"protein": 0.25, "fat": 0.25, "carbs": 0.50},
            Goal.MAINTENANCE: {"protein": 0.20, "fat": 0.30, "carbs": 0.50}
        }
        
        dist = distributions[goal]
        
        # Calculate grams (protein: 4 cal/g, fat: 9 cal/g, carbs: 4 cal/g)
        return {
            "protein": (calories * dist["protein"]) / 4,
            "fat": (calories * dist["fat"]) / 9,
            "carbs": (calories * dist["carbs"]) / 4
        }
    
    @classmethod
    def calculate_requirements(cls, user: UserProfile) -> NutritionRequirements:
        """Calculate complete nutritional requirements for a user."""
        bmr = cls.calculate_bmr(user)
        tdee = cls.calculate_tdee(bmr, user.activity_level.value)
        target_calories = cls.adjust_calories_for_goal(tdee, user.goal)
        macros = cls.calculate_macronutrient_distribution(target_calories, user.goal)
        
        return NutritionRequirements(
            calories=target_calories,
            protein=macros["protein"],
            fat=macros["fat"],
            carbs=macros["carbs"],
            bmr=bmr,
            tdee=tdee
        )