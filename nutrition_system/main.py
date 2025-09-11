#!/usr/bin/env python3
"""
Main CLI application for the Personalized Nutrition Analysis & Meal Plan Recommendation System.
"""

import click
from typing import List
from pathlib import Path

from .models import UserProfile, Gender, Goal, ActivityLevel
from .nutrition_calculator import NutritionCalculator
from .meal_planner import MealPlanner
from .report_generator import ReportGenerator


def get_user_input() -> UserProfile:
    """Interactive user input collection."""
    print("\n=== Personalized Nutrition Analysis System ===\n")
    
    # Basic information
    age = click.prompt("Enter your age", type=int)
    
    gender_choice = click.prompt(
        "Enter your gender (1: Male, 2: Female)", 
        type=click.Choice(['1', '2'])
    )
    gender = Gender.MALE if gender_choice == '1' else Gender.FEMALE
    
    weight = click.prompt("Enter your weight (kg)", type=float)
    height = click.prompt("Enter your height (cm)", type=float)
    
    # Goal selection
    print("\nGoals:")
    print("1. Weight Loss")
    print("2. Muscle Gain")
    print("3. Maintenance")
    
    goal_choice = click.prompt(
        "Select your goal (1-3)", 
        type=click.Choice(['1', '2', '3'])
    )
    goals = {
        '1': Goal.WEIGHT_LOSS,
        '2': Goal.MUSCLE_GAIN,
        '3': Goal.MAINTENANCE
    }
    goal = goals[goal_choice]
    
    # Activity level
    print("\nActivity Levels:")
    print("1. Sedentary (little/no exercise)")
    print("2. Lightly Active (light exercise/sports 1-3 days/week)")
    print("3. Moderately Active (moderate exercise/sports 3-5 days/week)")
    print("4. Very Active (hard exercise/sports 6-7 days a week)")
    print("5. Extra Active (very hard exercise/sports & physical job)")
    
    activity_choice = click.prompt(
        "Select your activity level (1-5)", 
        type=click.Choice(['1', '2', '3', '4', '5'])
    )
    
    activity_levels = {
        '1': ActivityLevel.SEDENTARY,
        '2': ActivityLevel.LIGHTLY_ACTIVE,
        '3': ActivityLevel.MODERATELY_ACTIVE,
        '4': ActivityLevel.VERY_ACTIVE,
        '5': ActivityLevel.EXTRA_ACTIVE
    }
    activity_level = activity_levels[activity_choice]
    
    # Dietary preferences
    preferences_input = click.prompt(
        "Enter dietary preferences (comma-separated, or press Enter for none)",
        default="",
        show_default=False
    )
    
    dietary_preferences = []
    if preferences_input.strip():
        dietary_preferences = [pref.strip() for pref in preferences_input.split(',')]
    
    return UserProfile(
        age=age,
        gender=gender,
        weight=weight,
        height=height,
        goal=goal,
        activity_level=activity_level,
        dietary_preferences=dietary_preferences
    )


def display_nutrition_requirements(requirements):
    """Display calculated nutrition requirements."""
    print(f"\n=== Your Nutrition Requirements ===")
    print(f"Basal Metabolic Rate (BMR): {requirements.bmr:.0f} calories")
    print(f"Total Daily Energy Expenditure (TDEE): {requirements.tdee:.0f} calories")
    print(f"Target Daily Calories: {requirements.calories:.0f} calories")
    print(f"Protein: {requirements.protein:.1f}g")
    print(f"Fat: {requirements.fat:.1f}g")
    print(f"Carbohydrates: {requirements.carbs:.1f}g")


def display_meal_plan(meal_plan):
    """Display the generated meal plan."""
    print(f"\n=== Your Personalized Meal Plan ===")
    
    for meal in meal_plan.meals:
        print(f"\n{meal.meal_name}:")
        print("-" * len(meal.meal_name))
        
        for dish in meal.dishes:
            print(f"  • {dish.dish_name}")
            print(f"    Calories: {dish.calories}, Protein: {dish.protein}g, "
                  f"Fat: {dish.fat}g, Carbs: {dish.carbs}g")
        
        print(f"  Meal Total: {meal.total_calories:.0f} calories, "
              f"{meal.total_protein:.1f}g protein, "
              f"{meal.total_fat:.1f}g fat, "
              f"{meal.total_carbs:.1f}g carbs")
    
    # Daily totals
    summary = meal_plan.get_nutrition_summary()
    print(f"\n=== Daily Totals ===")
    print(f"Calories: {summary['calories']:.0f}")
    print(f"Protein: {summary['protein']:.1f}g")
    print(f"Fat: {summary['fat']:.1f}g")
    print(f"Carbohydrates: {summary['carbs']:.1f}g")
    
    # Macro percentages
    macros = meal_plan.get_macro_percentages()
    print(f"\n=== Macronutrient Distribution ===")
    print(f"Protein: {macros['protein']:.1f}%")
    print(f"Fat: {macros['fat']:.1f}%")
    print(f"Carbohydrates: {macros['carbs']:.1f}%")


@click.command()
@click.option('--meals', '-m', default=3, help='Number of meals per day (1-5)')
@click.option('--options', '-o', default=1, help='Number of meal plan options to generate')
@click.option('--export', '-e', is_flag=True, help='Export results to PDF and Excel')
@click.option('--output-dir', '-d', default='reports', help='Output directory for exports')
@click.option('--sample', '-s', is_flag=True, help='Use sample user profile')
def main(meals: int, options: int, export: bool, output_dir: str, sample: bool):
    """
    Personalized Nutrition Analysis & Meal Plan Recommendation System
    
    Generate personalized meal plans based on your nutritional requirements.
    """
    try:
        # Validate inputs
        if not 1 <= meals <= 5:
            click.echo("Number of meals must be between 1 and 5")
            return
        
        if not 1 <= options <= 10:
            click.echo("Number of options must be between 1 and 10")
            return
        
        # Get user profile
        if sample:
            # Use sample profile for testing
            user = UserProfile(
                age=30,
                gender=Gender.MALE,
                weight=75,
                height=180,
                goal=Goal.MUSCLE_GAIN,
                activity_level=ActivityLevel.MODERATELY_ACTIVE,
                dietary_preferences=["high-protein"]
            )
            print("Using sample user profile:")
            print(f"Age: {user.age}, Gender: {user.gender.value}, Weight: {user.weight}kg, "
                  f"Height: {user.height}cm, Goal: {user.goal.value}")
        else:
            user = get_user_input()
        
        # Calculate nutrition requirements
        calculator = NutritionCalculator()
        requirements = calculator.calculate_requirements(user)
        display_nutrition_requirements(requirements)
        
        # Generate meal plan(s)
        planner = MealPlanner()
        
        if options == 1:
            meal_plan = planner.generate_meal_plan(user, requirements, meals)
            display_meal_plan(meal_plan)
            
            if export:
                print(f"\n=== Generating Reports ===")
                generator = ReportGenerator()
                reports = generator.generate_complete_report(meal_plan, user, output_dir)
                
                print(f"Reports generated in '{output_dir}' directory:")
                print(f"  • Excel file: {reports['excel_file']}")
                print(f"  • PDF file: {reports['pdf_file']}")
                print(f"  • Macro distribution chart: {output_dir}/macro_distribution.png")
                print(f"  • Meal nutrition chart: {output_dir}/meal_nutrition.png")
        
        else:
            meal_plans = planner.generate_multiple_options(user, requirements, meals, options)
            
            for i, meal_plan in enumerate(meal_plans, 1):
                print(f"\n{'='*50}")
                print(f"MEAL PLAN OPTION {i}")
                print(f"{'='*50}")
                display_meal_plan(meal_plan)
            
            if export and meal_plans:
                # Export the first option
                print(f"\n=== Generating Reports (Option 1) ===")
                generator = ReportGenerator()
                reports = generator.generate_complete_report(meal_plans[0], user, output_dir)
                
                print(f"Reports generated in '{output_dir}' directory:")
                print(f"  • Excel file: {reports['excel_file']}")
                print(f"  • PDF file: {reports['pdf_file']}")
                print(f"  • Macro distribution chart: {output_dir}/macro_distribution.png")
                print(f"  • Meal nutrition chart: {output_dir}/meal_nutrition.png")
    
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()