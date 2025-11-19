# Personalized Nutrition Analysis & Meal Plan System

This repository provides a simple command line application that:

- Calculates personalized calorie needs and macronutrient targets using the Mifflin-St Jeor formula.
- Recommends meal plan combinations from a curated dish dataset while respecting dietary preferences.
- Generates PDF and Excel (XLSX) reports along with SVG charts for macronutrient ratios and meal-level distribution.
- Exports synthetic nutrition datasets for testing and data science workflows.

## Getting Started

1. Ensure Python 3.10+ is installed (no additional third-party dependencies are required).
2. Optional: create and activate a virtual environment.
3. Run commands using the module entry point:

```bash
python -m nutrition.cli analyze \
  --age 30 \
  --gender male \
  --weight 72 \
  --height 175 \
  --goal "Maintenance" \
  --preference vegetarian \
  --export-dir ./reports \
  --chart-dir ./reports/charts
```

The command prints the calculated daily targets, recommended meal plans, and, when `--export-dir` is provided, writes PDF/Excel reports plus SVG visualizations.

### Generating Synthetic Datasets

Create synthetic user nutrition records for testing:

```bash
python -m nutrition.cli generate-synthetic --output ./synthetic_data.csv --count 30
```

### Available Options

- `--dataset <path>`: load additional dish datasets (JSON format) alongside the bundled dataset.
- `--meals-per-day`: customize the number of meals to plan for (1–5).
- `--num-options`: produce multiple alternative meal plans.
- `--no-pdf` / `--no-excel`: skip specific report exports when not needed.
- `--output-basename`: customize the filename prefix for generated artifacts.

The generated Excel file is a fully valid `.xlsx` workbook that can be opened in spreadsheet applications, and the PDF file provides a summary of calculated targets and meal selections.
