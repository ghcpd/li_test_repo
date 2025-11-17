# Nutrition Analysis & Meal Planning Toolkit

This repository implements a lightweight nutrition analysis and meal planning engine. Users can
provide a personal profile, macronutrient goal, and dietary preferences to create tailored meal plan
recommendations. The engine also generates a nutrition report with charts and an Excel export that
summarises the suggested meals.

## Key Features

- Calculates BMR and TDEE using the Mifflin-St Jeor formula with flexible activity factors.
- Applies goal-specific macro distributions (weight loss, muscle gain, maintenance).
- Filters dishes by dietary tags (vegetarian, low-salt, pescatarian, etc.) and proposes alternative
  meal plan options for 1–5 meals per day.
- Builds a nutrition report that includes a meal-level breakdown, macronutrient totals, pie and bar
  chart visualisations, and an Excel export.

## Running the Example

You can run the logic inside a Python interpreter. The snippet below generates a personalised report
and stores the charts plus Excel export in a directory named `output`.

```python
from pathlib import Path
from nutrition import DishDatabase, NutritionGoals, UserProfile, generate_nutrition_report

database = DishDatabase.load_default()
profile = UserProfile(
    age=32,
    gender="Female",
    weight=68,
    height=170,
    goal=NutritionGoals.WEIGHT_LOSS,
)
report = generate_nutrition_report(
    profile,
    activity_factor=1.3,
    database=database,
    preferences=["Vegetarian"],
    num_meals=3,
    alternatives=2,
    chart_dir=Path("output/charts"),
)
report.export_to_excel(Path("output/nutrition_report.xlsx"))
```

## Running Tests

This project uses the built-in `unittest` framework. Execute the following command from the project
root to run the test suite:

```bash
python -m unittest discover -s tests
```

## Data Source

The `nutrition/dishes.json` file contains a small, curated database of dishes used for the meal plan
recommendations. Each entry provides nutrient information along with dietary tags for preference
filtering.
