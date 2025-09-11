#!/usr/bin/env python3
import argparse
import os
import sys
from typing import List, Dict, Tuple

try:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
except Exception:
    pd = None
    np = None
    plt = None


def ensure_deps():
    global pd, np, plt
    if pd is None or np is None or plt is None:
        print("Installing required dependencies (pandas, numpy, matplotlib, openpyxl)...")
        os.system(sys.executable + " -m pip install --quiet pandas numpy matplotlib openpyxl")
        import pandas as pd  # type: ignore
        import numpy as np  # type: ignore
        import matplotlib.pyplot as plt  # type: ignore
    return pd, np, plt


def mifflin_st_jeor_bmr(age: int, gender: str, weight: float, height: float) -> float:
    g = gender.strip().lower()
    if g.startswith('m'):
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161


def adjusted_calories(tdee: float, goal: str) -> float:
    g = goal.strip().lower()
    factor = 1.0
    if 'loss' in g:
        factor = 0.85
    elif 'gain' in g:
        factor = 1.10
    return tdee * factor


def macro_ratios(goal: str) -> Tuple[float, float, float]:
    g = goal.strip().lower()
    if 'loss' in g:
        return (0.30, 0.25, 0.45)
    if 'gain' in g:
        return (0.30, 0.20, 0.50)
    return (0.20, 0.30, 0.50)


def grams_from_calories(calories: float, protein_ratio: float, fat_ratio: float, carb_ratio: float) -> Tuple[float, float, float]:
    protein_g = (calories * protein_ratio) / 4.0
    fat_g = (calories * fat_ratio) / 9.0
    carb_g = (calories * carb_ratio) / 4.0
    return protein_g, fat_g, carb_g


def generate_synthetic_dishes(n: int = 20):
    pd, np, _ = ensure_deps()
    rng = np.random.default_rng(42)
    names = [f"Dish_{i+1}" for i in range(n)]
    tags_pool = ["Vegetarian", "Low-salt", "Low-sugar", "High-protein", "Gluten-free"]
    rows = []
    for nm in names:
        calories = int(rng.integers(200, 700))
        protein = round(float(rng.uniform(10, 40)), 1)
        fat = round(float(rng.uniform(5, 30)), 1)
        carbs = round(max(0.0, (calories - protein * 4 - fat * 9) / 4.0), 1)
        tags = ",".join(rng.choice(tags_pool, size=int(rng.integers(1, 3)), replace=False))
        rows.append({
            'dish_name': nm,
            'ingredients': 'Varied',
            'weight': 200,
            'calories': calories,
            'protein': protein,
            'fat': fat,
            'carbs': carbs,
            'tags': tags
        })
    return pd.DataFrame(rows)


def load_dishes(path: str):
    pd, _, _ = ensure_deps()
    if os.path.exists(path):
        return pd.read_csv(path)
    df = generate_synthetic_dishes()
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    df.to_csv(path, index=False)
    return df


def filter_by_preferences(df, preferences: List[str]):
    if not preferences:
        return df
    prefs = [p.strip().lower() for p in preferences if p.strip()]
    if not prefs:
        return df
    mask = df['tags'].fillna('').apply(lambda t: all(p in t.lower() for p in prefs))
    filtered = df[mask]
    if filtered.empty:
        print("Warning: No dishes match all preferences. Ignoring preferences.")
        return df
    return filtered


def pick_meal_plan(df, total_calories: float, meals: int, seed: int = 0):
    pd, np, _ = ensure_deps()
    rng = np.random.default_rng(seed)
    per_meal = total_calories / meals
    candidates = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    chosen_rows = []
    for _ in range(meals):
        diffs = (candidates['calories'] - per_meal).abs()
        idx = diffs.sort_values().index[0]
        row = candidates.loc[idx].copy()
        portion = max(1, int(round(per_meal / max(1.0, float(row['calories'])))))
        portion = min(portion, 3)
        row['portion'] = portion
        row['calories'] = float(row['calories']) * portion
        row['protein'] = float(row['protein']) * portion
        row['fat'] = float(row['fat']) * portion
        row['carbs'] = float(row['carbs']) * portion
        chosen_rows.append(row)
    plan = pd.DataFrame(chosen_rows)
    return plan


def summarize_plan(plan_df):
    totals = {
        'calories': float(plan_df['calories'].sum()),
        'protein': float(plan_df['protein'].sum()),
        'fat': float(plan_df['fat'].sum()),
        'carbs': float(plan_df['carbs'].sum()),
    }
    return totals


def visualize_and_export(plan_df, totals, outdir: str, prefix: str = "plan"):
    pd, np, plt = ensure_deps()
    os.makedirs(outdir, exist_ok=True)
    # Pie chart
    labels = ['Protein', 'Fat', 'Carbs']
    values = [totals['protein'], totals['fat'], totals['carbs']]
    fig1, ax1 = plt.subplots()
    ax1.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')
    pie_path_png = os.path.join(outdir, f"{prefix}_macros.png")
    pie_path_pdf = os.path.join(outdir, f"{prefix}_macros.pdf")
    fig1.savefig(pie_path_png)
    fig1.savefig(pie_path_pdf)
    plt.close(fig1)

    # Bar chart per meal
    fig2, ax2 = plt.subplots()
    x = np.arange(len(plan_df))
    ax2.bar(x - 0.2, plan_df['calories'], width=0.2, label='Calories')
    ax2.bar(x, plan_df['protein'] * 4, width=0.2, label='Protein (kcal)')
    ax2.bar(x + 0.2, plan_df['carbs'] * 4, width=0.2, label='Carbs (kcal)')
    ax2.legend()
    ax2.set_title('Meal-level calories and macros (kcal)')
    ax2.set_xlabel('Meal')
    ax2.set_ylabel('kcal')
    bar_path = os.path.join(outdir, f"{prefix}_meals.png")
    fig2.savefig(bar_path)
    plt.close(fig2)

    # Excel export
    excel_path = os.path.join(outdir, f"{prefix}.xlsx")
    with pd.ExcelWriter(excel_path) as writer:
        plan_df.to_excel(writer, index=False, sheet_name='meals')
        pd.DataFrame([totals]).to_excel(writer, index=False, sheet_name='totals')
    return pie_path_png, bar_path, excel_path


def main():
    parser = argparse.ArgumentParser(description='Personalized Nutrition Analysis & Meal Plan Recommendation System')
    parser.add_argument('--age', type=int, required=True)
    parser.add_argument('--gender', type=str, required=True, choices=['male', 'female', 'Male', 'Female', 'M', 'F'])
    parser.add_argument('--weight', type=float, required=True, help='kg')
    parser.add_argument('--height', type=float, required=True, help='cm')
    parser.add_argument('--goal', type=str, required=True, choices=['weight_loss', 'muscle_gain', 'maintenance'])
    parser.add_argument('--activity', type=float, default=1.2, help='Activity factor, e.g., 1.2 sedentary')
    parser.add_argument('--meals', type=int, default=3, help='Meals per day (1-5)')
    parser.add_argument('--preferences', type=str, default='', help='Comma-separated dietary tags, e.g., Vegetarian,Low-salt')
    parser.add_argument('--dishes', type=str, default='outputs/dishes.csv', help='Dish database CSV path')
    parser.add_argument('--alternatives', type=int, default=3, help='Number of meal plan alternatives')
    parser.add_argument('--generate-dataset', action='store_true', help='Generate synthetic dish dataset and exit')
    args = parser.parse_args()

    ensure_deps()

    if args.generate_dataset:
        df = generate_synthetic_dishes(30)
        os.makedirs(os.path.dirname(args.dishes) or '.', exist_ok=True)
        df.to_csv(args.dishes, index=False)
        print(f"Synthetic dataset written to {args.dishes}")
        return

    dishes = load_dishes(args.dishes)
    dishes = filter_by_preferences(dishes, [p.strip() for p in args.preferences.split(',') if p.strip()])

    bmr = mifflin_st_jeor_bmr(args.age, args.gender, args.weight, args.height)
    tdee = bmr * args.activity
    target_cals = adjusted_calories(tdee, args.goal)
    ratios = macro_ratios(args.goal)
    macro_grams = grams_from_calories(target_cals, *ratios)

    print(f"BMR: {bmr:.1f} kcal, TDEE: {tdee:.1f} kcal, Target: {target_cals:.1f} kcal")
    print(f"Macro targets (g): Protein {macro_grams[0]:.1f}, Fat {macro_grams[1]:.1f}, Carbs {macro_grams[2]:.1f}")

    outdir = os.path.join('outputs', 'plan_outputs')
    os.makedirs(outdir, exist_ok=True)

    for i in range(args.alternatives):
        plan = pick_meal_plan(dishes, target_cals, max(1, min(args.meals, 5)), seed=i)
        totals = summarize_plan(plan)
        pie, bar, excel = visualize_and_export(plan, totals, outdir, prefix=f"plan_{i+1}")
        print(f"Alternative {i+1} totals: {totals}")
        print(f"Saved visuals to: {pie}, {bar}; Excel: {excel}")


if __name__ == '__main__':
    main()
