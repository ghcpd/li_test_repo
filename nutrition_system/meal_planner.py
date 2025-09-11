"""
Meal planning algorithm for generating personalized meal plans.
"""

import pandas as pd
import random
from typing import List, Optional, Dict
from .models import Dish, Meal, MealPlan, NutritionRequirements, UserProfile
from pathlib import Path


class MealPlanner:
    """Generate meal plans based on user requirements and dish database."""
    
    def __init__(self, dish_database_path: Optional[str] = None):
        """Initialize with dish database."""
        if dish_database_path is None:
            # Use default database
            current_dir = Path(__file__).parent
            dish_database_path = current_dir / "data" / "dishes.csv"
        
        self.dishes = self._load_dishes(dish_database_path)
    
    def _load_dishes(self, path: str) -> List[Dish]:
        """Load dishes from CSV file."""
        df = pd.read_csv(path)
        dishes = []
        
        for _, row in df.iterrows():
            ingredients = [ing.strip() for ing in row['ingredients'].split(',')]
            tags = [tag.strip() for tag in row['tags'].split(',')]
            
            dish = Dish(
                dish_name=row['dish_name'],
                ingredients=ingredients,
                weight=row['weight'],
                calories=row['calories'],
                protein=row['protein'],
                fat=row['fat'],
                carbs=row['carbs'],
                tags=tags
            )
            dishes.append(dish)
        
        return dishes
    
    def filter_dishes_by_preferences(self, preferences: List[str]) -> List[Dish]:
        """Filter dishes based on dietary preferences."""
        if not preferences:
            return self.dishes
        
        return [dish for dish in self.dishes if dish.meets_preferences(preferences)]
    
    def generate_meal_plan(self, 
                          user: UserProfile, 
                          requirements: NutritionRequirements,
                          num_meals: int = 3) -> MealPlan:
        """
        Generate a meal plan that meets nutritional requirements.
        
        Args:
            user: User profile
            requirements: Nutritional requirements
            num_meals: Number of meals per day (1-5)
        
        Returns:
            Generated meal plan
        """
        # Filter dishes based on preferences
        available_dishes = self.filter_dishes_by_preferences(user.dietary_preferences)
        
        if not available_dishes:
            raise ValueError("No dishes available for the given preferences")
        
        # Target calories per meal
        calories_per_meal = requirements.calories / num_meals
        
        meals = []
        for i in range(num_meals):
            meal_name = self._get_meal_name(i, num_meals)
            meal_dishes = self._select_dishes_for_meal(
                available_dishes, 
                calories_per_meal,
                requirements
            )
            meals.append(Meal(meal_name=meal_name, dishes=meal_dishes))
        
        return MealPlan(meals=meals, user_requirements=requirements)
    
    def _get_meal_name(self, meal_index: int, total_meals: int) -> str:
        """Get appropriate meal name based on index and total meals."""
        if total_meals == 1:
            return "Main Meal"
        elif total_meals == 2:
            return ["Breakfast", "Dinner"][meal_index]
        elif total_meals == 3:
            return ["Breakfast", "Lunch", "Dinner"][meal_index]
        elif total_meals == 4:
            return ["Breakfast", "Lunch", "Snack", "Dinner"][meal_index]
        else:  # 5 meals
            return ["Breakfast", "Mid-Morning Snack", "Lunch", "Afternoon Snack", "Dinner"][meal_index]
    
    def _select_dishes_for_meal(self, 
                               available_dishes: List[Dish], 
                               target_calories: float,
                               requirements: NutritionRequirements) -> List[Dish]:
        """Select dishes for a single meal to approximate target calories."""
        # Simple greedy algorithm to select dishes
        selected_dishes = []
        current_calories = 0
        
        # Shuffle dishes for variety
        dishes_copy = available_dishes.copy()
        random.shuffle(dishes_copy)
        
        # Try to get close to target calories (within 20% tolerance)
        tolerance = target_calories * 0.2
        
        for dish in dishes_copy:
            # Check if adding this dish would exceed our target too much
            if current_calories + dish.calories <= target_calories + tolerance:
                selected_dishes.append(dish)
                current_calories += dish.calories
                
                # If we're close enough to target, stop
                if current_calories >= target_calories - tolerance:
                    break
        
        # Ensure we have at least one dish
        if not selected_dishes and available_dishes:
            selected_dishes.append(random.choice(available_dishes))
        
        return selected_dishes
    
    def generate_multiple_options(self, 
                                 user: UserProfile,
                                 requirements: NutritionRequirements,
                                 num_meals: int = 3,
                                 num_options: int = 3) -> List[MealPlan]:
        """Generate multiple meal plan options for variety."""
        options = []
        
        for _ in range(num_options):
            try:
                meal_plan = self.generate_meal_plan(user, requirements, num_meals)
                options.append(meal_plan)
            except ValueError:
                continue
        
        return options
    
    def get_dish_recommendations(self, 
                               user: UserProfile,
                               meal_type: str = "any") -> List[Dish]:
        """Get dish recommendations based on user preferences and meal type."""
        available_dishes = self.filter_dishes_by_preferences(user.dietary_preferences)
        
        # Simple recommendation based on tags and meal type
        if meal_type.lower() == "breakfast":
            # Prefer dishes with breakfast-friendly tags
            breakfast_dishes = [d for d in available_dishes 
                              if any(tag in ["oatmeal", "smoothie", "toast", "egg"] 
                                   for tag in [tag.lower() for tag in d.tags])]
            if breakfast_dishes:
                return breakfast_dishes[:5]
        
        # Return top dishes based on user goal
        if user.goal.value == "muscle_gain":
            # Prioritize high-protein dishes
            return sorted(available_dishes, key=lambda x: x.protein, reverse=True)[:5]
        elif user.goal.value == "weight_loss":
            # Prioritize low-calorie, high-protein dishes
            return sorted(available_dishes, 
                         key=lambda x: (x.protein / max(x.calories, 1)), 
                         reverse=True)[:5]
        
        # Default: return random selection
        random.shuffle(available_dishes)
        return available_dishes[:5]