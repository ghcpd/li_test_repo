#!/usr/bin/env python3
"""
Personalized Nutrition Analysis & Meal Plan Recommendation System
Main CLI application for user interaction.
"""

import argparse
import json
import os
import sys
from nutrition_analysis import NutritionAnalyzer
from meal_planner import MealPlanner
from report_generator import ReportGenerator


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(text):
    """Print a formatted section header."""
    print(f"\n--- {text} ---")


def get_user_input_interactive():
    """Get user input interactively."""
    print_header("Personalized Nutrition Analysis & Meal Plan System")
    print("Please provide your information:")
    
    # Basic information
    while True:
        try:
            age = int(input("\nAge (years): "))
            if age < 1 or age > 120:
                print("Please enter a valid age between 1 and 120.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
    
    while True:
        gender = input("Gender (male/female): ").lower()
        if gender in ['male', 'female']:
            break
        print("Please enter 'male' or 'female'.")
    
    while True:
        try:
            weight = float(input("Weight (kg): "))
            if weight < 20 or weight > 300:
                print("Please enter a valid weight between 20 and 300 kg.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
    
    while True:
        try:
            height = float(input("Height (cm): "))
            if height < 100 or height > 250:
                print("Please enter a valid height between 100 and 250 cm.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
    
    # Health goal
    print("\nHealth Goals:")
    print("1. Weight Loss")
    print("2. Muscle Gain")
    print("3. Maintenance")
    
    while True:
        goal_choice = input("Select your goal (1-3): ")
        if goal_choice == '1':
            goal = 'weight_loss'
            break
        elif goal_choice == '2':
            goal = 'muscle_gain'
            break
        elif goal_choice == '3':
            goal = 'maintenance'
            break
        else:
            print("Please enter 1, 2, or 3.")
    
    # Activity level
    print("\nActivity Levels:")
    print("1. Sedentary (little or no exercise)")
    print("2. Light (light exercise 1-3 days/week)")
    print("3. Moderate (moderate exercise 3-5 days/week)")
    print("4. Active (heavy exercise 6-7 days/week)")
    print("5. Very Active (very heavy exercise, physical job)")
    
    while True:
        activity_choice = input("Select your activity level (1-5): ")
        if activity_choice == '1':
            activity_level = 'sedentary'
            break
        elif activity_choice == '2':
            activity_level = 'light'
            break
        elif activity_choice == '3':
            activity_level = 'moderate'
            break
        elif activity_choice == '4':
            activity_level = 'active'
            break
        elif activity_choice == '5':
            activity_level = 'very_active'
            break
        else:
            print("Please enter 1, 2, 3, 4, or 5.")
    
    # Dietary preferences
    print("\nDietary Preferences (optional):")
    print("Available tags: Vegetarian, Low-salt, Low-sugar, Low-fat, Low-carb, High-protein, High-fiber")
    preferences_input = input("Enter preferences separated by commas (or press Enter to skip): ").strip()
    
    preferences = []
    if preferences_input:
        preferences = [p.strip() for p in preferences_input.split(',')]
    
    # Number of meals
    while True:
        try:
            num_meals = int(input("\nNumber of meals per day (1-5): "))
            if num_meals < 1 or num_meals > 5:
                print("Please enter a number between 1 and 5.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
    
    return {
        'age': age,
        'gender': gender,
        'weight': weight,
        'height': height,
        'goal': goal,
        'activity_level': activity_level,
        'preferences': preferences,
        'num_meals': num_meals
    }


def display_analysis(analyzer):
    """Display nutrition analysis results."""
    print_section("Nutritional Requirements Analysis")
    analysis = analyzer.get_analysis()
    
    print(f"\nBasal Metabolic Rate (BMR): {analysis['bmr']} calories/day")
    print(f"Total Daily Energy Expenditure (TDEE): {analysis['tdee']} calories/day")
    print(f"Target Daily Calories: {analysis['target_calories']} calories/day")
    print(f"\nMacronutrient Targets:")
    print(f"  Protein: {analysis['macros']['protein']} g")
    print(f"  Fat: {analysis['macros']['fat']} g")
    print(f"  Carbohydrates: {analysis['macros']['carbs']} g")


def display_meal_plans(meal_plans):
    """Display meal plan options."""
    print_section("Recommended Meal Plans")
    
    for plan in meal_plans:
        print(f"\n{'='*70}")
        print(f"OPTION {plan['option_number']}")
        print(f"{'='*70}")
        
        for i, meal in enumerate(plan['meals'], 1):
            print(f"\nMeal {i}: {meal['dish_name']}")
            print(f"  Calories: {meal['calories']} | Protein: {meal['protein']}g | "
                  f"Fat: {meal['fat']}g | Carbs: {meal['carbs']}g")
            print(f"  Weight: {meal['weight']}g")
            print(f"  Tags: {', '.join(meal['tags'])}")
        
        totals = plan['total_nutrition']
        print(f"\n{'─'*70}")
        print(f"TOTAL: Calories: {totals['calories']} | Protein: {totals['protein']}g | "
              f"Fat: {totals['fat']}g | Carbs: {totals['carbs']}g")
        
        accuracy = plan['accuracy']
        print(f"\nDifference from Target:")
        print(f"  Calories: {accuracy['calories_diff']:+.0f} | "
              f"Protein: {accuracy['protein_diff']:+.1f}g | "
              f"Fat: {accuracy['fat_diff']:+.1f}g | "
              f"Carbs: {accuracy['carbs_diff']:+.1f}g")


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description='Personalized Nutrition Analysis & Meal Plan Recommendation System'
    )
    parser.add_argument('--interactive', '-i', action='store_true',
                      help='Run in interactive mode')
    parser.add_argument('--age', type=int, help='Age in years')
    parser.add_argument('--gender', choices=['male', 'female'], help='Gender')
    parser.add_argument('--weight', type=float, help='Weight in kg')
    parser.add_argument('--height', type=float, help='Height in cm')
    parser.add_argument('--goal', choices=['weight_loss', 'muscle_gain', 'maintenance'],
                      help='Health goal')
    parser.add_argument('--activity', choices=['sedentary', 'light', 'moderate', 'active', 'very_active'],
                      default='moderate', help='Activity level')
    parser.add_argument('--preferences', help='Dietary preferences (comma-separated)')
    parser.add_argument('--meals', type=int, default=3, help='Number of meals per day (1-5)')
    parser.add_argument('--export-pdf', help='Export report to PDF file')
    parser.add_argument('--export-excel', help='Export report to Excel file')
    parser.add_argument('--database', default='dish_database.json',
                      help='Path to dish database JSON file')
    
    args = parser.parse_args()
    
    # Get user input
    if args.interactive:
        user_data = get_user_input_interactive()
    else:
        if not all([args.age, args.gender, args.weight, args.height, args.goal]):
            print("Error: When not in interactive mode, you must provide: age, gender, weight, height, and goal")
            parser.print_help()
            sys.exit(1)
        
        user_data = {
            'age': args.age,
            'gender': args.gender,
            'weight': args.weight,
            'height': args.height,
            'goal': args.goal,
            'activity_level': args.activity,
            'preferences': args.preferences.split(',') if args.preferences else [],
            'num_meals': args.meals
        }
    
    # Check if database exists
    database_path = os.path.join(os.path.dirname(__file__), args.database)
    if not os.path.exists(database_path):
        print(f"Error: Dish database not found at {database_path}")
        sys.exit(1)
    
    # Perform nutrition analysis
    analyzer = NutritionAnalyzer(
        age=user_data['age'],
        gender=user_data['gender'],
        weight=user_data['weight'],
        height=user_data['height'],
        goal=user_data['goal'],
        activity_level=user_data['activity_level']
    )
    
    # Display analysis
    display_analysis(analyzer)
    
    # Generate meal plans
    print("\nGenerating meal plans...")
    planner = MealPlanner(database_path)
    
    try:
        meal_plans = planner.generate_meal_plan(
            target_calories=analyzer.target_calories,
            target_protein=analyzer.macros['protein'],
            target_fat=analyzer.macros['fat'],
            target_carbs=analyzer.macros['carbs'],
            num_meals=user_data['num_meals'],
            preferences=user_data['preferences'] if user_data['preferences'] else None,
            num_options=5
        )
    except ValueError as e:
        print(f"\nError: {e}")
        print("Try adjusting your preferences or increasing the number of meals.")
        sys.exit(1)
    
    # Display meal plans
    display_meal_plans(meal_plans)
    
    # Select a meal plan for export
    selected_plan = meal_plans[0]  # Use the best option
    
    # Export if requested
    if args.export_pdf or args.export_excel:
        print_section("Generating Reports")
        
        report_gen = ReportGenerator(
            nutrition_analysis=analyzer.get_analysis(),
            meal_plan=selected_plan
        )
        
        if args.export_pdf:
            pdf_path = report_gen.export_to_pdf(args.export_pdf)
            print(f"✓ PDF report saved to: {pdf_path}")
        
        if args.export_excel:
            excel_path = report_gen.export_to_excel(args.export_excel)
            print(f"✓ Excel report saved to: {excel_path}")
    
    print_header("Analysis Complete")
    print("Thank you for using the Nutrition Analysis System!")


if __name__ == '__main__':
    main()
