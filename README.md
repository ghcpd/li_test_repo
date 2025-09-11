# Personalized Nutrition Analysis & Meal Plan Recommendation System

A comprehensive system for calculating personalized nutritional requirements, recommending meal plans, and generating detailed nutritional analysis reports.

## Features

### 🎯 Core Functionality

- **Nutrition Requirement Analysis**: Calculate BMR and TDEE using scientifically-backed formulas
- **Personalized Meal Planning**: Generate meal plans tailored to individual goals and preferences
- **Nutritional Analysis**: Comprehensive reporting with visualizations and export options
- **Flexible Goals**: Support for weight loss, muscle gain, and maintenance
- **Dietary Preferences**: Filter meals based on dietary restrictions and preferences

### 📊 Analysis Capabilities

- **BMR Calculation**: Using Mifflin-St Jeor equation for accurate basal metabolic rate
- **TDEE Estimation**: Incorporates activity level for total daily energy expenditure
- **Macronutrient Distribution**: Optimized protein, fat, and carbohydrate ratios based on goals
- **Visual Reports**: Interactive charts showing nutritional breakdowns and meal comparisons

### 🍽️ Meal Planning

- **Dish Database**: Comprehensive nutritional information for 20+ dishes
- **Smart Selection**: Algorithm selects dishes to meet caloric and macro targets
- **Multiple Options**: Generate several meal plan alternatives
- **Flexible Meals**: Support for 1-5 meals per day
- **Dietary Filters**: Vegetarian, high-protein, low-carb, and more

### 📈 Reporting & Export

- **Visual Charts**: Pie charts for macros, bar charts for meal nutrition
- **PDF Reports**: Professional formatted nutrition plans
- **Excel Export**: Detailed spreadsheets with all nutritional data
- **Summary Tables**: Easy-to-read nutritional breakdowns

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd li_test_repo
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Command Line Interface

Run the nutrition system with various options:

```bash
# Interactive mode - input your details
python3 -m nutrition_system.main

# Quick test with sample profile
python3 -m nutrition_system.main --sample

# Generate multiple meal options
python3 -m nutrition_system.main --sample --options 3

# Customize number of meals per day
python3 -m nutrition_system.main --sample --meals 5

# Export reports to PDF and Excel
python3 -m nutrition_system.main --sample --export

# Specify output directory
python3 -m nutrition_system.main --sample --export --output-dir my_reports
```

### Command Options

- `--meals, -m`: Number of meals per day (1-5, default: 3)
- `--options, -o`: Number of meal plan options to generate (1-10, default: 1)
- `--export, -e`: Export results to PDF and Excel
- `--output-dir, -d`: Output directory for exports (default: reports)
- `--sample, -s`: Use sample user profile for testing

### Example Output

```
=== Your Nutrition Requirements ===
Basal Metabolic Rate (BMR): 1730 calories
Total Daily Energy Expenditure (TDEE): 2682 calories
Target Daily Calories: 2982 calories
Protein: 186.3g
Fat: 82.8g
Carbohydrates: 372.7g

=== Your Personalized Meal Plan ===

Breakfast:
---------
  • Protein Smoothie
    Calories: 185, Protein: 25.0g, Fat: 3.0g, Carbs: 20.0g
  • Oatmeal Bowl
    Calories: 310, Protein: 10.0g, Fat: 8.0g, Carbs: 52.0g
  Meal Total: 495 calories, 35.0g protein, 11.0g fat, 72.0g carbs
```

## System Architecture

### Core Modules

1. **models.py**: Data structures for users, dishes, meals, and nutrition requirements
2. **nutrition_calculator.py**: BMR, TDEE, and macronutrient calculations
3. **meal_planner.py**: Meal selection algorithm and plan generation
4. **report_generator.py**: Visualization and export functionality
5. **main.py**: Command-line interface and workflow coordination

### Data Files

- **dishes.csv**: Comprehensive database of dishes with nutritional information
- Includes 20+ dishes with calories, macronutrients, ingredients, and dietary tags

## Nutritional Formulas

### BMR (Basal Metabolic Rate)
- **Male**: BMR = 10×weight + 6.25×height - 5×age + 5
- **Female**: BMR = 10×weight + 6.25×height - 5×age - 161

### TDEE (Total Daily Energy Expenditure)
- **TDEE** = BMR × Activity Factor
- Activity factors: 1.2 (sedentary) to 1.9 (very active)

### Goal Adjustments
- **Weight Loss**: -500 calories from TDEE
- **Muscle Gain**: +300 calories to TDEE  
- **Maintenance**: No adjustment

### Macronutrient Ratios
- **Weight Loss**: 30% protein, 25% fat, 45% carbs
- **Muscle Gain**: 25% protein, 25% fat, 50% carbs
- **Maintenance**: 20% protein, 30% fat, 50% carbs

## Testing

Run the comprehensive test suite:

```bash
python3 run_tests.py
```

The test suite covers:
- Nutrition calculation accuracy
- Meal planning logic
- Data model functionality
- Edge cases and error handling

## Dependencies

- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **matplotlib**: Chart generation
- **seaborn**: Enhanced visualizations
- **reportlab**: PDF generation
- **openpyxl**: Excel file creation
- **click**: Command-line interface

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is open source and available under the MIT License.

---

*Built with ❤️ for personalized nutrition and health*