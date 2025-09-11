# li_test_repo

Personalized Nutrition Analysis & Meal Plan Recommendation System

Quick start:

- Ensure Python 3.10+ is installed.
- Optional: install dependencies for visualization and Excel export:
  - pip install pandas matplotlib openpyxl

Run an example:

python3 nutrition_planner.py \
  --age 30 --gender male --weight 70 --height 175 \
  --activity 1.2 --goal maintenance \
  --meals 3 --options 3 \
  --out sample_run --excel

Options:
- --goal: weight_loss | muscle_gain | maintenance
- --preferences: semicolon-separated tags to filter dishes, e.g. "vegetarian;low-sugar"
- --dishes_csv: path to a CSV with columns dish_name,ingredients,weight,calories,protein,fat,carbs,tags

Outputs:
- sample_run_macro_pie.png: macronutrient calorie distribution pie chart
- sample_run_meal_bars.png: calories per meal bar chart
- sample_run_report.pdf: PDF report containing summary and charts
- sample_run_plan.xlsx: Excel export (if --excel is used)
- dishes_sample.csv: generated sample dataset if no custom dataset is supplied
