# Usage Examples

This document provides detailed examples of how to use the Personalized Nutrition Analysis & Meal Plan Recommendation System.

## Example 1: Basic Weight Loss Plan

A 30-year-old male wants to lose weight with moderate activity.

```bash
python nutrition_app.py \
  --age 30 \
  --gender male \
  --weight 85 \
  --height 180 \
  --goal weight_loss \
  --activity moderate \
  --meals 3
```

**Expected Output:**
- BMR calculation based on Mifflin-St Jeor formula
- TDEE adjusted for moderate activity (1.55x multiplier)
- Target calories 15% below TDEE
- 5 meal plan options with 3 meals each
- Macronutrient breakdown optimized for weight loss (30% protein, 30% fat, 40% carbs)

## Example 2: Vegetarian Muscle Gain

A 25-year-old female athlete wants to build muscle with a vegetarian diet.

```bash
python nutrition_app.py \
  --age 25 \
  --gender female \
  --weight 60 \
  --height 165 \
  --goal muscle_gain \
  --activity active \
  --meals 4 \
  --preferences "Vegetarian,High-protein" \
  --export-pdf muscle_gain_veggie.pdf
```

**Features Demonstrated:**
- Dietary preference filtering (Vegetarian + High-protein)
- Increased calorie target (10% surplus for muscle gain)
- Higher protein ratio (35%)
- 4 meals per day for better nutrient distribution
- PDF export with charts and detailed breakdown

## Example 3: Maintenance with Low-Carb Focus

A 40-year-old male maintaining current weight with low-carb preference.

```bash
python nutrition_app.py \
  --age 40 \
  --gender male \
  --weight 78 \
  --height 175 \
  --goal maintenance \
  --activity light \
  --meals 3 \
  --preferences "Low-carb,High-protein" \
  --export-excel maintenance_plan.xlsx
```

**Key Points:**
- Maintenance calories equal to TDEE
- Low-carb and high-protein dish selection
- Excel export for easy tracking and customization
- Light activity level (1.375x multiplier)

## Example 4: Interactive Mode

For users who prefer guided input:

```bash
python nutrition_app.py --interactive
```

The system will prompt for:
1. Age
2. Gender
3. Weight (kg)
4. Height (cm)
5. Health goal selection (1-3)
6. Activity level selection (1-5)
7. Dietary preferences (optional)
8. Number of meals per day

## Example 5: Complete Report Generation

Generate both PDF and Excel reports:

```bash
python nutrition_app.py \
  --age 28 \
  --gender female \
  --weight 65 \
  --height 168 \
  --goal weight_loss \
  --activity moderate \
  --meals 4 \
  --preferences "High-fiber,Low-fat" \
  --export-pdf complete_report.pdf \
  --export-excel complete_report.xlsx
```

**Generated Reports Include:**
- User profile summary
- BMR, TDEE, and target calorie calculations
- Macronutrient targets
- Detailed meal plan with nutrition per meal
- Total daily nutrition
- Accuracy comparison (actual vs. target)
- Pie chart showing macronutrient distribution
- Bar charts showing nutrition per meal

## Example 6: Programmatic Usage

Using the system in your own Python scripts:

```python
from nutrition_analysis import NutritionAnalyzer
from meal_planner import MealPlanner
from report_generator import ReportGenerator

# Step 1: Analyze nutritional requirements
analyzer = NutritionAnalyzer(
    age=35,
    gender='female',
    weight=70,
    height=170,
    goal='weight_loss',
    activity_level='moderate'
)

# Access calculated values
print(f"Your BMR: {analyzer.bmr} calories/day")
print(f"Your TDEE: {analyzer.tdee} calories/day")
print(f"Target Calories: {analyzer.target_calories} calories/day")
print(f"Protein: {analyzer.macros['protein']}g")
print(f"Fat: {analyzer.macros['fat']}g")
print(f"Carbs: {analyzer.macros['carbs']}g")

# Step 2: Generate meal plans
planner = MealPlanner('dish_database.json')

meal_plans = planner.generate_meal_plan(
    target_calories=analyzer.target_calories,
    target_protein=analyzer.macros['protein'],
    target_fat=analyzer.macros['fat'],
    target_carbs=analyzer.macros['carbs'],
    num_meals=3,
    preferences=['Vegetarian', 'Low-salt'],
    num_options=5
)

# Display the best option
best_plan = meal_plans[0]
print(f"\nBest Meal Plan (Option {best_plan['option_number']}):")
for meal in best_plan['meals']:
    print(f"  - {meal['dish_name']}: {meal['calories']} cal")

print(f"\nTotal: {best_plan['total_nutrition']['calories']} calories")

# Step 3: Generate reports
report_gen = ReportGenerator(
    nutrition_analysis=analyzer.get_analysis(),
    meal_plan=best_plan
)

# Export to both formats
report_gen.export_to_pdf('my_nutrition_plan.pdf')
report_gen.export_to_excel('my_nutrition_plan.xlsx')
print("\nReports generated successfully!")
```

## Example 7: High-Protein Athlete Plan

For serious athletes needing high protein intake:

```bash
python nutrition_app.py \
  --age 26 \
  --gender male \
  --weight 90 \
  --height 185 \
  --goal muscle_gain \
  --activity very_active \
  --meals 5 \
  --preferences "High-protein"
```

**Benefits:**
- Very active multiplier (1.9x)
- 5 meals for sustained protein intake
- Muscle gain surplus (10% extra calories)
- Focus on high-protein dishes

## Example 8: Custom Dish Database

You can use a custom dish database:

```bash
python nutrition_app.py \
  --age 32 \
  --gender female \
  --weight 58 \
  --height 162 \
  --goal maintenance \
  --activity moderate \
  --meals 3 \
  --database my_custom_dishes.json
```

Your custom database should follow this format:

```json
[
  {
    "dish_name": "My Custom Dish",
    "ingredients": ["Ingredient 1", "Ingredient 2"],
    "weight": 200,
    "calories": 350,
    "protein": 25,
    "fat": 12,
    "carbs": 35,
    "tags": ["Custom-tag", "Another-tag"]
  }
]
```

## Understanding the Output

### Meal Plan Display

Each meal plan option shows:
- **Meal Name**: Name of the dish
- **Nutrition per Meal**: Calories, Protein (g), Fat (g), Carbs (g)
- **Weight**: Serving size in grams
- **Tags**: Dietary classifications

### Total Summary

- **TOTAL**: Sum of all meals' nutrition
- **Difference from Target**: Shows how close the plan is to your targets
  - Positive (+): Over target
  - Negative (-): Under target

### Choosing the Best Plan

The system ranks plans by how closely they match your nutritional targets. Option 1 is always the best match, but you can review all 5 options to find one that includes your preferred dishes.

## Tips for Best Results

1. **Be Accurate with Your Data**: Provide accurate age, weight, and height for better calculations.

2. **Choose Appropriate Activity Level**:
   - Sedentary: Desk job, minimal exercise
   - Light: Light exercise 1-3 days/week
   - Moderate: Regular exercise 3-5 days/week
   - Active: Intense exercise 6-7 days/week
   - Very Active: Professional athlete, physical labor job

3. **Use Multiple Meals for Better Distribution**: More meals (4-5) help distribute nutrients more evenly throughout the day.

4. **Combine Compatible Preferences**: Some combinations work better:
   - "High-protein,Low-carb" for keto-style plans
   - "Vegetarian,High-fiber" for plant-based plans
   - "Low-salt,Low-sugar" for clean eating

5. **Export Reports for Tracking**: Use Excel exports to track your progress over time and make adjustments.

## Troubleshooting

**Problem**: "No dishes available matching the given preferences"
- **Solution**: Your preference combination may be too restrictive. Try removing some preferences or adding more dishes to the database.

**Problem**: All meal plans show large differences from target
- **Solution**: Try increasing the number of meals per day or adjusting your preferences to allow more dish variety.

**Problem**: PDF/Excel not generating
- **Solution**: Ensure you have write permissions in the output directory and all dependencies are installed.
