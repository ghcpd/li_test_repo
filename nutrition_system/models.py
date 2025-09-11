"""
Data models for the nutrition analysis system.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"


class Goal(Enum):
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"


class ActivityLevel(Enum):
    SEDENTARY = 1.2
    LIGHTLY_ACTIVE = 1.375
    MODERATELY_ACTIVE = 1.55
    VERY_ACTIVE = 1.725
    EXTRA_ACTIVE = 1.9


@dataclass
class UserProfile:
    """User profile containing personal information and goals."""
    age: int
    gender: Gender
    weight: float  # kg
    height: float  # cm
    goal: Goal
    activity_level: ActivityLevel = ActivityLevel.MODERATELY_ACTIVE
    dietary_preferences: List[str] = None

    def __post_init__(self):
        if self.dietary_preferences is None:
            self.dietary_preferences = []


@dataclass
class NutritionRequirements:
    """Daily nutritional requirements for a user."""
    calories: float
    protein: float  # grams
    fat: float      # grams
    carbs: float    # grams
    bmr: float
    tdee: float


@dataclass
class Dish:
    """Individual dish with nutritional information."""
    dish_name: str
    ingredients: List[str]
    weight: float  # grams
    calories: float
    protein: float  # grams
    fat: float      # grams
    carbs: float    # grams
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def meets_preferences(self, preferences: List[str]) -> bool:
        """Check if dish meets dietary preferences."""
        if not preferences:
            return True
        return any(pref.lower() in [tag.lower() for tag in self.tags] for pref in preferences)


@dataclass
class Meal:
    """A meal consisting of multiple dishes."""
    meal_name: str
    dishes: List[Dish]
    
    @property
    def total_calories(self) -> float:
        return sum(dish.calories for dish in self.dishes)
    
    @property
    def total_protein(self) -> float:
        return sum(dish.protein for dish in self.dishes)
    
    @property
    def total_fat(self) -> float:
        return sum(dish.fat for dish in self.dishes)
    
    @property
    def total_carbs(self) -> float:
        return sum(dish.carbs for dish in self.dishes)


@dataclass
class MealPlan:
    """Complete daily meal plan."""
    meals: List[Meal]
    user_requirements: NutritionRequirements
    
    @property
    def total_calories(self) -> float:
        return sum(meal.total_calories for meal in self.meals)
    
    @property
    def total_protein(self) -> float:
        return sum(meal.total_protein for meal in self.meals)
    
    @property
    def total_fat(self) -> float:
        return sum(meal.total_fat for meal in self.meals)
    
    @property
    def total_carbs(self) -> float:
        return sum(meal.total_carbs for meal in self.meals)
    
    def get_nutrition_summary(self) -> Dict[str, float]:
        """Get complete nutritional summary."""
        return {
            "calories": self.total_calories,
            "protein": self.total_protein,
            "fat": self.total_fat,
            "carbs": self.total_carbs
        }
    
    def get_macro_percentages(self) -> Dict[str, float]:
        """Get macronutrient distribution as percentages."""
        total_cals = self.total_calories
        if total_cals == 0:
            return {"protein": 0, "fat": 0, "carbs": 0}
        
        return {
            "protein": (self.total_protein * 4 / total_cals) * 100,
            "fat": (self.total_fat * 9 / total_cals) * 100,
            "carbs": (self.total_carbs * 4 / total_cals) * 100
        }