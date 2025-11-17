# Personalized Nutrition Analysis & Meal Plan Recommendation System

This repository contains a lightweight reference implementation of a nutrition planning system. It allows you to:

- Analyse a user's basal metabolic rate (BMR) and total daily energy expenditure (TDEE) using the Mifflin-St Jeor formula
- Adjust caloric intake for common health goals (weight loss, muscle gain, maintenance)
- Generate macronutrient distribution targets and meal plan suggestions from a structured dish database
- Respect dietary preferences when composing meals, with support for one to five meals per day
- Produce macronutrient and meal-level visualisations (PNG when Matplotlib is available or SVG fallbacks otherwise)
- Export a nutrition report to PDF and the meal plan to an Excel-compatible XML spreadsheet
- Create synthetic datasets to support testing and data science workflows

## Repository Structure

```
nutrition_system.py   # Main module exposing nutrition and planning utilities
data/dishes.json     # Sample dish database with nutritional information
tests/               # Automated test suite covering key functionality
```

## Getting Started

1. **Install Optional Dependencies** (only required for PNG charts and rich PDF reports):
   ```bash
   pip install matplotlib
   ```
   The system falls back to SVG charts and a text-based PDF writer when Matplotlib is not available.

2. **Run the Automated Tests**:
   ```bash
   python -m unittest discover -s tests
   ```

3. **Generate a Meal Plan**:
   ```python
   from nutrition_system import (
       UserProfile,
       load_dishes,
       generate_meal_plan,
       create_macro_pie_chart,
       create_meal_bar_chart,
       export_plan_to_excel,
       export_report_pdf,
   )

   dishes = load_dishes("data/dishes.json")
   profile = UserProfile(age=32, gender="female", weight=70, height=168, goal="weight_loss", dietary_preferences=["vegetarian"])
   plan, alternatives, target_calories, macro_targets = generate_meal_plan(profile, dishes, meals_per_day=3)

   print("Suggested meals:")
   for dish in plan.dishes:
       print(f"- {dish.dish_name} ({dish.calories} kcal)")

   pie_chart = create_macro_pie_chart(plan, "output")
   bar_charts = create_meal_bar_chart(plan, "output")
   export_plan_to_excel(plan, macro_targets, "output/meal_plan.xls")
   export_report_pdf(plan, profile, target_calories, macro_targets, "output/nutrition_report.pdf", pie_chart, bar_charts)
   ```

4. **Generate Synthetic Data**:
   ```python
   from nutrition_system import generate_synthetic_dataset

   generate_synthetic_dataset(10, "output/synthetic_users.json")
   ```

The generated charts and reports will be stored in the directories you provide. If Matplotlib is available, charts are rendered as PNG files and the PDF embeds the images; otherwise, SVG charts are produced and the PDF summarizes the results with file references.
