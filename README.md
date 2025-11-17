# Personalized Nutrition Analysis & Meal Plan System

This repository implements a nutrition analysis engine that:

- Calculates caloric and macronutrient requirements using the Mifflin-St Jeor formula.
- Generates goal-aligned meal plans from an included dish database.
- Respects optional dietary preferences (e.g., Vegetarian, Low-Carb).
- Exports meal plans with report-ready visualizations (PDF and Excel).
- Provides utilities to generate synthetic user datasets for testing.

## Getting Started

1. Create and activate a Python 3.10 environment.
2. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the automated tests:

   ```bash
   python -m unittest discover
   ```

## Command Line Usage

The `nutrition_cli.py` script allows you to run the analysis from the command line. Example:

```bash
python nutrition_cli.py --age 30 --gender Male --weight 82 --height 182 \
  --goal "muscle gain" --activity-level moderate --preferences Vegetarian \
  --meals 3 --alt-meals 2,4 --top 2 --export --show-json
```

This command will output recommended meal plans, create charts, and export the best match to both Excel (`reports/meal_plan.xlsx`) and PDF (`reports/nutrition_report.pdf`).

### Synthetic Dataset Generation

You can generate a synthetic dataset of users with nutritional targets through the API:

```python
from pathlib import Path
from nutrition_system import generate_synthetic_user_dataset

dataset = generate_synthetic_user_dataset(10, output_path=Path("synthetic_users.json"))
```

## Repository Contents

- `nutrition_system.py`: Core nutrition analysis, meal planning, charting, and export logic.
- `nutrition_cli.py`: Command line script for end-to-end analysis and report creation.
- `dish_database.json`: Structured dataset of dishes with nutritional information and tags.
- `tests/test_nutrition_system.py`: Unit tests covering core functionality and exports.
- `requirements.txt`: Python dependencies required for the analysis and reporting modules.
