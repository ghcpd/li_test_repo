#!/usr/bin/env python3
import argparse
import math
import random
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple

try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None  # pandas is optional; Excel export will be disabled if not available

try:
    import matplotlib.pyplot as plt  # type: ignore
    from matplotlib.backends.backend_pdf import PdfPages  # type: ignore
except Exception:
    plt = None
    PdfPages = None


@dataclass
class UserProfile:
    age: int
    gender: str
    weight: float  # kg
    height: float  # cm
    activity_factor: float
    goal: str  # weight_loss, muscle_gain, maintenance
    preferences: List[str]


@dataclass
class Dish:
    dish_name: str
    ingredients: str
    weight: float
    calories: float
    protein: float
    fat: float
    carbs: float
    tags: List[str]


@dataclass
class Plan:
    meals: List[Dish]
    total_calories: float
    total_protein: float
    total_fat: float
    total_carbs: float


GOAL_ADJUSTMENT = {
    "weight_loss": 0.85,
    "muscle_gain": 1.10,
    "maintenance": 1.00,
}

MACRO_RATIOS = {
    "weight_loss": {"protein": 0.30, "fat": 0.25, "carbs": 0.45},
    "muscle_gain": {"protein": 0.30, "fat": 0.25, "carbs": 0.45},
    "maintenance": {"protein": 0.20, "fat": 0.25, "carbs": 0.55},
}


def compute_bmr(profile: UserProfile) -> float:
    g = profile.gender.strip().lower()
    if g.startswith("m"):
        return 10 * profile.weight + 6.25 * profile.height - 5 * profile.age + 5
    else:
        return 10 * profile.weight + 6.25 * profile.height - 5 * profile.age - 161


def compute_targets(profile: UserProfile) -> Dict[str, float]:
    bmr = compute_bmr(profile)
    tdee = bmr * profile.activity_factor
    adj = GOAL_ADJUSTMENT.get(profile.goal, 1.0)
    calories = tdee * adj
    ratios = MACRO_RATIOS.get(profile.goal, MACRO_RATIOS["maintenance"])  # type: ignore
    protein_g = calories * ratios["protein"] / 4
    fat_g = calories * ratios["fat"] / 9
    carbs_g = calories * ratios["carbs"] / 4
    return {
        "bmr": bmr,
        "tdee": tdee,
        "calories": calories,
        "protein_g": protein_g,
        "fat_g": fat_g,
        "carbs_g": carbs_g,
    }


def load_dishes(csv_path: Optional[str]) -> List[Dish]:
    dishes: List[Dish] = []
    if csv_path and pd is not None:
        try:
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                tags = [t.strip() for t in str(row.get("tags", "")).split(";") if t and t.strip()]
                dishes.append(
                    Dish(
                        dish_name=str(row.get("dish_name", "Unknown")),
                        ingredients=str(row.get("ingredients", "")),
                        weight=float(row.get("weight", 0)),
                        calories=float(row.get("calories", 0)),
                        protein=float(row.get("protein", 0)),
                        fat=float(row.get("fat", 0)),
                        carbs=float(row.get("carbs", 0)),
                        tags=tags,
                    )
                )
            if dishes:
                return dishes
        except Exception:
            pass
    # Fallback synthetic dataset
    dishes = generate_synthetic_dishes()
    return dishes


def generate_synthetic_dishes() -> List[Dish]:
    base: List[Dish] = []
    data = [
        ("Grilled Chicken Salad", "Chicken breast;Lettuce;Tomatoes;Olive oil", 350, 420, 40, 18, 22, ["low-carb", "low-sugar"]),
        ("Oatmeal with Berries", "Oats;Milk;Blueberries;Honey", 300, 350, 12, 8, 58, ["vegetarian"]),
        ("Tofu Stir Fry", "Tofu;Broccoli;Bell peppers;Soy sauce", 400, 380, 22, 12, 50, ["vegetarian", "low-sugar"]),
        ("Salmon with Quinoa", "Salmon;Quinoa;Asparagus;Lemon", 380, 480, 35, 20, 36, ["low-sugar"]),
        ("Greek Yogurt Parfait", "Yogurt;Granola;Strawberries;Honey", 250, 280, 18, 6, 40, ["vegetarian"]),
        ("Veggie Omelette", "Eggs;Spinach;Mushrooms;Cheese", 280, 320, 21, 20, 6, ["vegetarian", "low-sugar"]),
        ("Lentil Soup", "Lentils;Carrots;Celery;Onions", 350, 300, 20, 6, 48, ["vegetarian", "low-fat"]),
        ("Turkey Sandwich", "Turkey;Whole grain bread;Lettuce;Mustard", 320, 410, 28, 12, 44, ["low-sugar"]),
        ("Brown Rice Bowl", "Brown rice;Chicken;Broccoli;Soy sauce", 420, 520, 36, 12, 70, ["low-sugar"]),
        ("Fruit Salad", "Apple;Banana;Grapes;Orange", 250, 180, 3, 1, 42, ["vegetarian", "low-fat", "low-salt"]),
        ("Avocado Toast", "Avocado;Whole grain bread;Tomatoes", 220, 260, 6, 14, 26, ["vegetarian"]),
        ("Quinoa Chickpea Bowl", "Quinoa;Chickpeas;Spinach;Olive oil", 380, 450, 18, 14, 62, ["vegetarian", "low-sugar"]),
    ]
    for d in data:
        base.append(Dish(*d))
    return base


def filter_by_preferences(dishes: List[Dish], preferences: List[str]) -> List[Dish]:
    prefs = [p.strip().lower() for p in preferences if p.strip()]
    if not prefs:
        return dishes
    filtered = [d for d in dishes if all(p in [t.lower() for t in d.tags] for p in prefs)]
    return filtered if filtered else dishes  # fallback to all if too strict


def score_dish(dish: Dish, per_meal_targets: Dict[str, float]) -> float:
    # Score based on closeness to per-meal calories and macro grams
    if per_meal_targets["calories"] <= 0:
        return 0
    score = 0.0
    # Normalize differences
    cal_diff = abs(dish.calories - per_meal_targets["calories"]) / per_meal_targets["calories"]
    p_diff = abs(dish.protein - per_meal_targets["protein_g"]) / max(1.0, per_meal_targets["protein_g"])
    f_diff = abs(dish.fat - per_meal_targets["fat_g"]) / max(1.0, per_meal_targets["fat_g"])
    c_diff = abs(dish.carbs - per_meal_targets["carbs_g"]) / max(1.0, per_meal_targets["carbs_g"])
    # Lower diff is better
    score = - (0.5 * cal_diff + 0.2 * p_diff + 0.15 * f_diff + 0.15 * c_diff)
    return score


def recommend_meal_plans(
    dishes: List[Dish],
    targets: Dict[str, float],
    meals_per_day: int = 3,
    options: int = 3,
    preferences: Optional[List[str]] = None,
    seed: int = 42,
) -> List[Plan]:
    rng = random.Random(seed)
    dishes_pref = filter_by_preferences(dishes, preferences or [])
    if not dishes_pref:
        dishes_pref = dishes
    per_meal_targets = {
        "calories": targets["calories"] / meals_per_day,
        "protein_g": targets["protein_g"] / meals_per_day,
        "fat_g": targets["fat_g"] / meals_per_day,
        "carbs_g": targets["carbs_g"] / meals_per_day,
    }

    # Pre-score dishes relative to per-meal targets
    scored = sorted(
        ((score_dish(d, per_meal_targets), d) for d in dishes_pref),
        key=lambda x: x[0],
        reverse=True,
    )

    top_dishes = [d for _, d in scored[: max(15, meals_per_day * 3)]] or dishes_pref

    plans: List[Plan] = []
    for i in range(options):
        rng.shuffle(top_dishes)
        selected = top_dishes[:meals_per_day]
        total_cals = sum(d.calories for d in selected)
        total_p = sum(d.protein for d in selected)
        total_f = sum(d.fat for d in selected)
        total_c = sum(d.carbs for d in selected)
        plans.append(
            Plan(
                meals=selected,
                total_calories=total_cals,
                total_protein=total_p,
                total_fat=total_f,
                total_carbs=total_c,
            )
        )
    # Sort plans by closeness to targets
    def plan_score(plan: Plan) -> float:
        cal_diff = abs(plan.total_calories - targets["calories"]) / targets["calories"]
        p_diff = abs(plan.total_protein - targets["protein_g"]) / max(1.0, targets["protein_g"])
        f_diff = abs(plan.total_fat - targets["fat_g"]) / max(1.0, targets["fat_g"])
        c_diff = abs(plan.total_carbs - targets["carbs_g"]) / max(1.0, targets["carbs_g"])
        return (0.5 * cal_diff + 0.2 * p_diff + 0.15 * f_diff + 0.15 * c_diff)

    plans.sort(key=plan_score)
    return plans


def visualize_and_export(
    plan: Plan,
    targets: Dict[str, float],
    out_prefix: str,
    export_pdf: bool = True,
    export_excel: bool = False,
):
    if plt is None:
        print("matplotlib is not available; skipping visualization.")
    else:
        # Pie chart for macro calorie ratio
        macro_calories = [
            plan.total_protein * 4,
            plan.total_fat * 9,
            plan.total_carbs * 4,
        ]
        labels = ["Protein", "Fat", "Carbs"]
        fig1, ax1 = plt.subplots()
        ax1.pie(macro_calories, labels=labels, autopct="%1.1f%%", startangle=90)
        ax1.axis("equal")
        fig1.suptitle("Macronutrient Calorie Distribution")
        fig1.tight_layout()
        fig1.savefig(f"{out_prefix}_macro_pie.png", dpi=150)

        # Bar chart for meal-level calories
        fig2, ax2 = plt.subplots()
        meal_names = [d.dish_name for d in plan.meals]
        meal_cals = [d.calories for d in plan.meals]
        ax2.bar(meal_names, meal_cals, color="#4c72b0")
        ax2.set_ylabel("Calories")
        ax2.set_title("Calories per Meal")
        ax2.set_xticklabels(meal_names, rotation=30, ha="right")
        fig2.tight_layout()
        fig2.savefig(f"{out_prefix}_meal_bars.png", dpi=150)

        if export_pdf and PdfPages is not None:
            with PdfPages(f"{out_prefix}_report.pdf") as pdf:
                # Summary page
                fig_sum, ax_sum = plt.subplots(figsize=(8.27, 11.69))  # A4 portrait
                ax_sum.axis("off")
                text_lines = [
                    "Nutrition Analysis Report",
                    "",
                    f"Target Calories: {targets['calories']:.0f}",
                    f"Target Protein (g): {targets['protein_g']:.0f}",
                    f"Target Fat (g): {targets['fat_g']:.0f}",
                    f"Target Carbs (g): {targets['carbs_g']:.0f}",
                    "",
                    f"Plan Calories: {plan.total_calories:.0f}",
                    f"Plan Protein (g): {plan.total_protein:.0f}",
                    f"Plan Fat (g): {plan.total_fat:.0f}",
                    f"Plan Carbs (g): {plan.total_carbs:.0f}",
                    "",
                    "Meals:",
                ]
                for d in plan.meals:
                    text_lines.append(
                        f"- {d.dish_name}: {d.calories:.0f} kcal | P {d.protein:.0f}g F {d.fat:.0f}g C {d.carbs:.0f}g"
                    )
                ax_sum.text(0.05, 0.95, "\n".join(text_lines), va="top", family="monospace")
                pdf.savefig(fig_sum)
                plt.close(fig_sum)

                pdf.savefig(fig1)
                pdf.savefig(fig2)
                plt.close(fig1)
                plt.close(fig2)

    if export_excel and pd is not None:
        out_xlsx = f"{out_prefix}_plan.xlsx"
        plan_rows = [
            {
                "dish_name": d.dish_name,
                "calories": d.calories,
                "protein_g": d.protein,
                "fat_g": d.fat,
                "carbs_g": d.carbs,
                "tags": ";".join(d.tags),
            }
            for d in plan.meals
        ]
        df_plan = pd.DataFrame(plan_rows)
        totals = pd.DataFrame(
            [
                {
                    "target_calories": targets["calories"],
                    "target_protein_g": targets["protein_g"],
                    "target_fat_g": targets["fat_g"],
                    "target_carbs_g": targets["carbs_g"],
                    "plan_calories": plan.total_calories,
                    "plan_protein_g": plan.total_protein,
                    "plan_fat_g": plan.total_fat,
                    "plan_carbs_g": plan.total_carbs,
                }
            ]
        )
        with pd.ExcelWriter(out_xlsx) as writer:
            df_plan.to_excel(writer, index=False, sheet_name="meals")
            totals.to_excel(writer, index=False, sheet_name="totals")



def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Personalized Nutrition & Meal Plan Recommender")
    parser.add_argument("--age", type=int, required=True, help="Age in years")
    parser.add_argument("--gender", type=str, required=True, choices=["male", "female", "m", "f"], help="Gender")
    parser.add_argument("--weight", type=float, required=True, help="Weight in kg")
    parser.add_argument("--height", type=float, required=True, help="Height in cm")
    parser.add_argument("--activity", type=float, default=1.2, help="Activity factor (default 1.2)")
    parser.add_argument("--goal", type=str, required=True, choices=["weight_loss", "muscle_gain", "maintenance"], help="Goal")
    parser.add_argument("--preferences", type=str, default="", help="Semicolon-separated dietary tags, e.g., 'vegetarian;low-sugar'")
    parser.add_argument("--meals", type=int, default=3, choices=[1, 2, 3, 4, 5], help="Meals per day (1-5)")
    parser.add_argument("--options", type=int, default=3, help="Number of alternative plans to generate")
    parser.add_argument("--dishes_csv", type=str, default="", help="Path to dishes CSV with columns: dish_name,ingredients,weight,calories,protein,fat,carbs,tags")
    parser.add_argument("--out", type=str, default="nutrition_output", help="Output prefix for files")
    parser.add_argument("--no-pdf", action="store_true", help="Skip exporting PDF report")
    parser.add_argument("--excel", action="store_true", help="Export plan to Excel (requires pandas)")
    return parser.parse_args(argv)



def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    preferences = [p.strip() for p in args.preferences.split(";") if p.strip()]
    profile = UserProfile(
        age=args.age,
        gender=args.gender,
        weight=args.weight,
        height=args.height,
        activity_factor=args.activity,
        goal=args.goal,
        preferences=preferences,
    )

    dishes = load_dishes(args.dishes_csv or None)
    targets = compute_targets(profile)

    plans = recommend_meal_plans(
        dishes=dishes,
        targets=targets,
        meals_per_day=args.meals,
        options=args.options,
        preferences=preferences,
        seed=42,
    )

    if not plans:
        print("No plans could be generated.")
        return 1

    best = plans[0]

    print("Computed targets:")
    for k in ["bmr", "tdee", "calories", "protein_g", "fat_g", "carbs_g"]:
        print(f"  {k}: {targets[k]:.2f}")

    print("\nBest Meal Plan:")
    for i, d in enumerate(best.meals, 1):
        print(f"  Meal {i}: {d.dish_name} | {d.calories:.0f} kcal | P {d.protein:.0f}g F {d.fat:.0f}g C {d.carbs:.0f}g | Tags: {', '.join(d.tags)}")

    print(
        f"\nTotals -> Calories: {best.total_calories:.0f}, Protein: {best.total_protein:.0f}g, Fat: {best.total_fat:.0f}g, Carbs: {best.total_carbs:.0f}g"
    )

    visualize_and_export(
        plan=best,
        targets=targets,
        out_prefix=args.out,
        export_pdf=not args.no_pdf,
        export_excel=args.excel,
    )

    # Save synthetic dishes if none provided, to allow users to modify later
    if not args.dishes_csv and pd is not None:
        df = pd.DataFrame(
            [
                {
                    "dish_name": d.dish_name,
                    "ingredients": d.ingredients,
                    "weight": d.weight,
                    "calories": d.calories,
                    "protein": d.protein,
                    "fat": d.fat,
                    "carbs": d.carbs,
                    "tags": ";".join(d.tags),
                }
                for d in dishes
            ]
        )
        try:
            df.to_csv("dishes_sample.csv", index=False)
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
