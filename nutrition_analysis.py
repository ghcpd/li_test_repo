"""
Module 1: Nutrition Requirement Analysis
Calculates BMR, TDEE, and macronutrient distribution based on user information.
"""


class NutritionAnalyzer:
    """Analyzes nutritional requirements based on user profile."""
    
    # Activity factors for TDEE calculation
    ACTIVITY_FACTORS = {
        'sedentary': 1.2,        # Little to no exercise
        'light': 1.375,          # Light exercise 1-3 days/week
        'moderate': 1.55,        # Moderate exercise 3-5 days/week
        'active': 1.725,         # Heavy exercise 6-7 days/week
        'very_active': 1.9       # Very heavy exercise, physical job
    }
    
    # Macronutrient ratios for different goals (protein, fat, carbs)
    MACRO_RATIOS = {
        'weight_loss': {'protein': 0.30, 'fat': 0.30, 'carbs': 0.40},
        'muscle_gain': {'protein': 0.35, 'fat': 0.25, 'carbs': 0.40},
        'maintenance': {'protein': 0.25, 'fat': 0.30, 'carbs': 0.45}
    }
    
    # Calorie adjustment factors based on goal
    CALORIE_ADJUSTMENTS = {
        'weight_loss': -0.15,    # 15% deficit
        'muscle_gain': 0.10,     # 10% surplus
        'maintenance': 0.00      # No adjustment
    }
    
    def __init__(self, age, gender, weight, height, goal='maintenance', activity_level='moderate'):
        """
        Initialize nutrition analyzer with user information.
        
        Args:
            age (int): Age in years
            gender (str): 'male' or 'female'
            weight (float): Weight in kg
            height (float): Height in cm
            goal (str): 'weight_loss', 'muscle_gain', or 'maintenance'
            activity_level (str): Activity level from ACTIVITY_FACTORS
        """
        self.age = age
        self.gender = gender.lower()
        self.weight = weight
        self.height = height
        self.goal = goal
        self.activity_level = activity_level
        
        # Calculate nutritional requirements
        self.bmr = self.calculate_bmr()
        self.tdee = self.calculate_tdee()
        self.target_calories = self.calculate_target_calories()
        self.macros = self.calculate_macros()
    
    def calculate_bmr(self):
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor formula.
        
        Returns:
            float: BMR in calories per day
        """
        if self.gender == 'male':
            # Male: BMR = 10*weight + 6.25*height - 5*age + 5
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        else:  # female
            # Female: BMR = 10*weight + 6.25*height - 5*age - 161
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161
        
        return round(bmr, 2)
    
    def calculate_tdee(self):
        """
        Calculate Total Daily Energy Expenditure.
        
        Returns:
            float: TDEE in calories per day
        """
        activity_factor = self.ACTIVITY_FACTORS.get(self.activity_level, 1.55)
        tdee = self.bmr * activity_factor
        return round(tdee, 2)
    
    def calculate_target_calories(self):
        """
        Calculate target calories based on user goal.
        
        Returns:
            float: Target daily calories
        """
        adjustment = self.CALORIE_ADJUSTMENTS.get(self.goal, 0.00)
        target = self.tdee * (1 + adjustment)
        return round(target, 2)
    
    def calculate_macros(self):
        """
        Calculate macronutrient targets in grams.
        
        Returns:
            dict: Dictionary with protein, fat, and carbs in grams
        """
        ratios = self.MACRO_RATIOS.get(self.goal, self.MACRO_RATIOS['maintenance'])
        
        # Calculate calories for each macro
        protein_calories = self.target_calories * ratios['protein']
        fat_calories = self.target_calories * ratios['fat']
        carbs_calories = self.target_calories * ratios['carbs']
        
        # Convert to grams (protein: 4 cal/g, fat: 9 cal/g, carbs: 4 cal/g)
        macros = {
            'protein': round(protein_calories / 4, 2),
            'fat': round(fat_calories / 9, 2),
            'carbs': round(carbs_calories / 4, 2)
        }
        
        return macros
    
    def get_analysis(self):
        """
        Get complete nutritional analysis.
        
        Returns:
            dict: Complete analysis including BMR, TDEE, target calories, and macros
        """
        return {
            'user_info': {
                'age': self.age,
                'gender': self.gender,
                'weight': self.weight,
                'height': self.height,
                'goal': self.goal,
                'activity_level': self.activity_level
            },
            'bmr': self.bmr,
            'tdee': self.tdee,
            'target_calories': self.target_calories,
            'macros': self.macros
        }
    
    def __str__(self):
        """String representation of the analysis."""
        return (
            f"Nutrition Analysis:\n"
            f"BMR: {self.bmr} calories/day\n"
            f"TDEE: {self.tdee} calories/day\n"
            f"Target Calories: {self.target_calories} calories/day\n"
            f"Macros: {self.macros['protein']}g protein, "
            f"{self.macros['fat']}g fat, {self.macros['carbs']}g carbs"
        )
