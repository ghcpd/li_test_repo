# Personalized Nutrition Analysis & Meal Plan Recommendation System

A comprehensive Python-based system for analyzing nutritional requirements and generating personalized meal plans based on user goals and preferences.

## Features

### 1️⃣ Nutrition Requirement Analysis
- **BMR Calculation**: Uses the Mifflin-St Jeor formula to calculate Basal Metabolic Rate
  - Male: BMR = 10×weight + 6.25×height - 5×age + 5
  - Female: BMR = 10×weight + 6.25×height - 5×age - 161
- **TDEE Calculation**: Estimates Total Daily Energy Expenditure based on activity level
- **Goal-Based Caloric Adjustment**: 
  - Weight Loss: 15% calorie deficit
  - Muscle Gain: 10% calorie surplus
  - Maintenance: Equal to TDEE
- **Macronutrient Distribution**: Customized protein, fat, and carb ratios based on goals

### 2️⃣ Meal Plan Recommendation
- Smart meal combination selection from a comprehensive dish database
- Dietary preference filtering (Vegetarian, Low-salt, Low-sugar, High-protein, etc.)
- Support for 1-5 meals per day
- Multiple alternative meal plan options for user selection
- Accuracy metrics showing how close plans match nutritional targets

### 3️⃣ Nutrition Analysis Reports
- **Visual Charts**:
  - Pie chart for macronutrient distribution
  - Bar charts for meal-level calories and macros
- **Export Formats**:
  - PDF reports with comprehensive analysis and visualizations
  - Excel spreadsheets with detailed nutritional breakdowns
- Daily nutrition totals and comparisons to targets

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ghcpd/li_test_repo.git
cd li_test_repo
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

#### Interactive Mode
Run the application in interactive mode for a guided experience:
```bash
python nutrition_app.py --interactive
```

#### Direct Command Line Usage
Provide all parameters directly:
```bash
python nutrition_app.py \
  --age 30 \
  --gender male \
  --weight 75 \
  --height 175 \
  --goal weight_loss \
  --activity moderate \
  --meals 3 \
  --preferences "High-protein,Vegetarian" \
  --export-pdf report.pdf \
  --export-excel report.xlsx
```

### Parameters

| Parameter | Description | Options/Format |
|-----------|-------------|----------------|
| `--age` | Age in years | Integer (1-120) |
| `--gender` | Biological gender | `male` or `female` |
| `--weight` | Weight in kilograms | Float (20-300) |
| `--height` | Height in centimeters | Float (100-250) |
| `--goal` | Health/fitness goal | `weight_loss`, `muscle_gain`, `maintenance` |
| `--activity` | Activity level | `sedentary`, `light`, `moderate`, `active`, `very_active` |
| `--meals` | Number of meals per day | Integer (1-5) |
| `--preferences` | Dietary preferences | Comma-separated tags (optional) |
| `--export-pdf` | Export to PDF | Output file path (optional) |
| `--export-excel` | Export to Excel | Output file path (optional) |

### Available Dietary Tags
- `Vegetarian`
- `High-protein`
- `Low-carb`
- `Low-fat`
- `Low-salt`
- `Low-sugar`
- `High-fiber`
- `Whole-grain`
- `Omega-3`

## Examples

### Example 1: Weight Loss Plan
```bash
python nutrition_app.py \
  --age 28 \
  --gender female \
  --weight 70 \
  --height 165 \
  --goal weight_loss \
  --activity light \
  --meals 4
```

### Example 2: Muscle Gain with High Protein
```bash
python nutrition_app.py \
  --age 25 \
  --gender male \
  --weight 80 \
  --height 180 \
  --goal muscle_gain \
  --activity active \
  --meals 5 \
  --preferences "High-protein" \
  --export-pdf muscle_gain_plan.pdf
```

### Example 3: Vegetarian Maintenance Plan
```bash
python nutrition_app.py \
  --age 35 \
  --gender female \
  --weight 65 \
  --height 170 \
  --goal maintenance \
  --activity moderate \
  --meals 3 \
  --preferences "Vegetarian,High-fiber" \
  --export-excel veggie_plan.xlsx
```

## Dish Database

The system includes a comprehensive dish database (`dish_database.json`) with 20 dishes covering various cuisines and dietary preferences. Each dish includes:
- Nutritional information (calories, protein, fat, carbs)
- Ingredient list
- Weight/serving size
- Dietary tags

You can extend the database by adding more dishes following the same JSON structure.

## Python API Usage

You can also use the system programmatically in your Python code:

```python
from nutrition_analysis import NutritionAnalyzer
from meal_planner import MealPlanner
from report_generator import ReportGenerator

# Analyze nutritional requirements
analyzer = NutritionAnalyzer(
    age=30,
    gender='male',
    weight=75,
    height=175,
    goal='weight_loss',
    activity_level='moderate'
)

print(f"BMR: {analyzer.bmr} calories/day")
print(f"Target Calories: {analyzer.target_calories} calories/day")

# Generate meal plans
planner = MealPlanner('dish_database.json')
meal_plans = planner.generate_meal_plan(
    target_calories=analyzer.target_calories,
    target_protein=analyzer.macros['protein'],
    target_fat=analyzer.macros['fat'],
    target_carbs=analyzer.macros['carbs'],
    num_meals=3,
    preferences=['Vegetarian'],
    num_options=5
)

# Generate reports
report_gen = ReportGenerator(
    nutrition_analysis=analyzer.get_analysis(),
    meal_plan=meal_plans[0]
)
report_gen.export_to_pdf('nutrition_report.pdf')
report_gen.export_to_excel('nutrition_report.xlsx')
```

## Testing

Run the test suite to verify the system:

```bash
python -m unittest test_nutrition_system -v
```

## Project Structure

```
li_test_repo/
├── nutrition_analysis.py      # Module 1: Nutrition requirement analysis
├── meal_planner.py            # Module 2: Meal plan recommendation
├── report_generator.py        # Module 3: Report generation & visualization
├── nutrition_app.py           # Main CLI application
├── dish_database.json         # Dish database with nutritional info
├── test_nutrition_system.py   # Unit tests
├── requirements.txt           # Python dependencies
├── .gitignore                # Git ignore file
└── README.md                 # This file
```

## Technical Details

### BMR Formula (Mifflin-St Jeor)
- **Male**: BMR = 10 × weight(kg) + 6.25 × height(cm) - 5 × age + 5
- **Female**: BMR = 10 × weight(kg) + 6.25 × height(cm) - 5 × age - 161

### Activity Factors
- Sedentary: 1.2 (little to no exercise)
- Light: 1.375 (light exercise 1-3 days/week)
- Moderate: 1.55 (moderate exercise 3-5 days/week)
- Active: 1.725 (heavy exercise 6-7 days/week)
- Very Active: 1.9 (very heavy exercise, physical job)

### Macronutrient Ratios
- **Weight Loss**: 30% protein, 30% fat, 40% carbs
- **Muscle Gain**: 35% protein, 25% fat, 40% carbs
- **Maintenance**: 25% protein, 30% fat, 45% carbs

### Calorie Conversions
- Protein: 4 calories per gram
- Fat: 9 calories per gram
- Carbohydrates: 4 calories per gram

## Dependencies

- **pandas**: Data manipulation and Excel export
- **matplotlib**: Chart generation
- **reportlab**: PDF report generation
- **openpyxl**: Excel file handling

## License

This project is available for educational and personal use.

## Contributing

To add new dishes to the database, edit `dish_database.json` following this structure:

```json
{
  "dish_name": "Dish Name",
  "ingredients": ["Ingredient 1", "Ingredient 2"],
  "weight": 150,
  "calories": 200,
  "protein": 25,
  "fat": 8,
  "carbs": 15,
  "tags": ["Tag1", "Tag2"]
}
```

## Future Enhancements

Potential improvements for future versions:
- Micronutrient tracking (vitamins, minerals)
- Meal prep scheduling and shopping lists
- Integration with fitness tracking APIs
- Mobile app interface
- Multi-day meal planning
- Recipe suggestions and cooking instructions
- User accounts and historical data tracking