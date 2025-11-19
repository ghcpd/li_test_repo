"""
Module 2: Meal Plan Recommendation
Recommends meal combinations from the dish database to meet nutritional targets.
"""

import json
import random
from itertools import combinations
from typing import List, Dict, Optional


class MealPlanner:
    """Generates meal plans based on nutritional targets and preferences."""
    
    def __init__(self, dish_database_path='dish_database.json'):
        """
        Initialize meal planner with dish database.
        
        Args:
            dish_database_path (str): Path to JSON file containing dish data
        """
        with open(dish_database_path, 'r') as f:
            self.dishes = json.load(f)
    
    def filter_dishes(self, preferences: Optional[List[str]] = None):
        """
        Filter dishes based on dietary preferences.
        
        Args:
            preferences (list): List of required tags (e.g., ['Vegetarian', 'Low-salt'])
        
        Returns:
            list: Filtered list of dishes
        """
        if not preferences:
            return self.dishes
        
        filtered = []
        for dish in self.dishes:
            # Check if all preferences are in the dish's tags
            if all(pref in dish['tags'] for pref in preferences):
                filtered.append(dish)
        
        return filtered
    
    def calculate_meal_nutrition(self, meals: List[Dict]) -> Dict:
        """
        Calculate total nutrition for a list of meals.
        
        Args:
            meals (list): List of dish dictionaries
        
        Returns:
            dict: Total nutrition values
        """
        total = {
            'calories': sum(meal['calories'] for meal in meals),
            'protein': sum(meal['protein'] for meal in meals),
            'fat': sum(meal['fat'] for meal in meals),
            'carbs': sum(meal['carbs'] for meal in meals)
        }
        return total
    
    def score_meal_plan(self, meals: List[Dict], target_nutrition: Dict) -> float:
        """
        Score how well a meal plan matches target nutrition.
        Lower score is better (closer to target).
        
        Args:
            meals (list): List of dish dictionaries
            target_nutrition (dict): Target values for calories, protein, fat, carbs
        
        Returns:
            float: Score (sum of squared differences)
        """
        totals = self.calculate_meal_nutrition(meals)
        
        # Calculate weighted differences
        calorie_diff = abs(totals['calories'] - target_nutrition['calories']) / target_nutrition['calories']
        protein_diff = abs(totals['protein'] - target_nutrition['protein']) / target_nutrition['protein']
        fat_diff = abs(totals['fat'] - target_nutrition['fat']) / target_nutrition['fat']
        carbs_diff = abs(totals['carbs'] - target_nutrition['carbs']) / target_nutrition['carbs']
        
        # Total score (lower is better)
        score = calorie_diff + protein_diff + fat_diff + carbs_diff
        return score
    
    def generate_meal_plan(self, 
                          target_calories: float,
                          target_protein: float,
                          target_fat: float,
                          target_carbs: float,
                          num_meals: int = 3,
                          preferences: Optional[List[str]] = None,
                          num_options: int = 5) -> List[Dict]:
        """
        Generate meal plan options that meet nutritional targets.
        
        Args:
            target_calories (float): Target daily calories
            target_protein (float): Target protein in grams
            target_fat (float): Target fat in grams
            target_carbs (float): Target carbs in grams
            num_meals (int): Number of meals per day (1-5)
            preferences (list): Dietary preferences/tags
            num_options (int): Number of alternative meal plans to generate
        
        Returns:
            list: List of meal plan options, each containing dishes and nutritional info
        """
        # Filter dishes based on preferences
        available_dishes = self.filter_dishes(preferences)
        
        if not available_dishes:
            raise ValueError("No dishes available matching the given preferences")
        
        target_nutrition = {
            'calories': target_calories,
            'protein': target_protein,
            'fat': target_fat,
            'carbs': target_carbs
        }
        
        # Try to find good meal combinations
        best_plans = []
        max_attempts = 500
        
        for _ in range(max_attempts):
            # Randomly select dishes for the meal plan
            if len(available_dishes) >= num_meals:
                selected_meals = random.sample(available_dishes, num_meals)
                score = self.score_meal_plan(selected_meals, target_nutrition)
                
                # Store plan with its score
                best_plans.append({
                    'meals': selected_meals,
                    'score': score
                })
        
        # Sort by score and return top options
        best_plans.sort(key=lambda x: x['score'])
        top_plans = best_plans[:num_options]
        
        # Format results
        formatted_plans = []
        for i, plan in enumerate(top_plans):
            totals = self.calculate_meal_nutrition(plan['meals'])
            formatted_plans.append({
                'option_number': i + 1,
                'meals': [
                    {
                        'dish_name': meal['dish_name'],
                        'calories': meal['calories'],
                        'protein': meal['protein'],
                        'fat': meal['fat'],
                        'carbs': meal['carbs'],
                        'weight': meal['weight'],
                        'ingredients': meal['ingredients'],
                        'tags': meal['tags']
                    }
                    for meal in plan['meals']
                ],
                'total_nutrition': totals,
                'target_nutrition': target_nutrition,
                'accuracy': {
                    'calories_diff': round(totals['calories'] - target_calories, 2),
                    'protein_diff': round(totals['protein'] - target_protein, 2),
                    'fat_diff': round(totals['fat'] - target_fat, 2),
                    'carbs_diff': round(totals['carbs'] - target_carbs, 2)
                }
            })
        
        return formatted_plans
    
    def get_dish_by_name(self, dish_name: str) -> Optional[Dict]:
        """
        Get a specific dish by name.
        
        Args:
            dish_name (str): Name of the dish
        
        Returns:
            dict: Dish information or None if not found
        """
        for dish in self.dishes:
            if dish['dish_name'].lower() == dish_name.lower():
                return dish
        return None
    
    def list_all_dishes(self) -> List[Dict]:
        """
        Get list of all available dishes.
        
        Returns:
            list: All dishes in the database
        """
        return self.dishes
