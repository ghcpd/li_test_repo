# Personalized Nutrition Analysis & Meal Plan Recommendation System

This repository provides a minimal, scriptable implementation of the nutrition analysis and meal planning requirements. It includes:

- Basal Metabolic Rate (BMR) and Total Daily Energy Expenditure (TDEE) calculations using the Mifflin-St Jeor formula.
- Calorie targets tailored to weight loss, muscle gain, or maintenance goals with goal-specific macronutrient ratios.
- A curated database of dishes enriched with nutritional information and dietary tags.
- A meal planner that generates 1–5 meal combinations matching user goals, dietary preferences, and caloric/macronutrient needs. Multiple alternative plans are produced deterministically.
- Visualization tooling that outputs a macronutrient pie chart and a bar chart summarizing meal-level calories.
- Export utilities to produce Excel and PDF reports for each meal plan.
- Synthetic dataset generation helpers for testing and experimentation.

## Getting Started

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the tests:

```bash
pytest
```

3. Generate a meal plan from the command line:

```bash
python -m nutrition.cli \
  --age 30 \
  --gender male \
  --weight 80 \
  --height 180 \
  --goal "weight loss" \
  --activity-level moderate \
  --preferences vegetarian \
  --meals 3 \
  --alternatives 3 \
  --excel-output output/meal_plan.xlsx \
  --pdf-output output/meal_plan.pdf \
  --charts-dir output/charts
```

The command prints a nutrition summary and meal plan details. Chart images, Excel, and PDF reports are written to the locations provided.

## Synthetic Dataset Generation

Use the `SyntheticDataGenerator` to create custom dish datasets:

```python
from pathlib import Path
from nutrition.synthetic import SyntheticDataGenerator

SyntheticDataGenerator.generate_dish_dataset(25, Path("output/synthetic_dishes.csv"))
```

## Data Source

The default dish database resides in `data/dishes.csv`. Each entry includes: dish name, ingredients, weight, calories, macronutrient breakdown, and dietary tags. Update this file or substitute your own dataset to customize the recommendations.
