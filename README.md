# Personalized Nutrition Analysis & Meal Planning

This repository contains a lightweight nutrition analysis toolkit that can
calculate personalised macronutrient targets, recommend meal plan options, and
export the results for sharing.  The implementation is intentionally simple so
that it can be executed in constrained environments such as the evaluation
sandbox used for this task.

## Features

- Basal metabolic rate (BMR) and total daily energy expenditure (TDEE)
  calculations using the Mifflin-St Jeor formula.
- Goal-aware calorie adjustments and macronutrient targets for weight loss,
  muscle gain, and maintenance.
- Meal plan generation that respects dietary preference tags and supports 1–5
  meals per day (with multiple alternatives).
- Report creation with Excel and CSV export support, including pie and bar
  charts of nutritional distribution.
- Synthetic dataset generation to create mock historical meal records.

## Directory Structure

```
.
├── data/dishes.json      # Example dish database used in tests and CLI demos
├── nutrition/planner.py  # Core implementation and command-line interface
└── tests/test_planner.py # Automated tests covering key behaviours
```

## Getting Started

1. (Optional) Create and activate a virtual environment.
2. Install the dependencies required for testing and plotting:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install pytest matplotlib
   ```

3. Run the automated test suite:

   ```bash
   pytest
   ```

## Command-Line Usage

The toolkit exposes a command-line entry point for performing an end-to-end
analysis:

```bash
python -m nutrition.planner data/dishes.json \
  --age 30 \
  --gender Male \
  --weight 75 \
  --height 180 \
  --goal "Muscle Gain" \
  --activity moderate \
  --meals 4 \
  --preferences low-sugar \
  --alternatives 3 \
  --export-dir exports \
  --generate-synthetic 20
```

The command above loads the included dish database, performs nutrition
analysis, generates meal plan options, exports results to the `exports`
directory, and produces an additional synthetic dataset containing 20 records.

Generated assets include:

- `nutrition_report.xlsx` – Excel summary of the nutrition analysis
- `meal_plan.csv` – CSV file containing meal details for the best recommendation
- `macro_distribution.png` – Pie chart of the target macronutrient ratios
- `meal_calories.png` – Bar chart showing per-meal calories
- `synthetic_history.csv` – Synthetic dataset (only when `--generate-synthetic`
  is specified)

## Dish Database Format

The dish database is a JSON array where each entry contains the following
fields:

- `dish_name`: Name of the meal
- `ingredients`: Ingredient list (array)
- `weight`: Weight in grams
- `calories`: Energy in kcal
- `protein`, `fat`, and `carbs`: Macronutrient content in grams
- `tags`: List of dietary tags (e.g., `vegetarian`, `low-salt`, `low-sugar`)

You can replace `data/dishes.json` with your own dataset that follows the same
structure.
