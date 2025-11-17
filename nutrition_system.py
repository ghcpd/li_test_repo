import json
import math
import os
import random
from dataclasses import dataclass, asdict
from itertools import combinations_with_replacement
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:  # pragma: no cover - availability depends on environment
    import matplotlib  # type: ignore

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt  # noqa: E402
    from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

    MATPLOTLIB_AVAILABLE = True
except Exception:  # pragma: no cover - fallback when matplotlib is missing
    MATPLOTLIB_AVAILABLE = False
    plt = None
    PdfPages = None


CALORIES_PER_GRAM = {"protein": 4, "carbs": 4, "fat": 9}
GOAL_CALORIE_MULTIPLIER = {
    "weight_loss": 0.85,
    "muscle_gain": 1.15,
    "maintenance": 1.0,
}
GOAL_MACRO_RATIOS = {
    "weight_loss": {"protein": 0.35, "fat": 0.25, "carbs": 0.40},
    "muscle_gain": {"protein": 0.30, "fat": 0.25, "carbs": 0.45},
    "maintenance": {"protein": 0.25, "fat": 0.25, "carbs": 0.50},
}
DEFAULT_ACTIVITY_FACTOR = 1.375


@dataclass
class UserProfile:
    age: int
    gender: str
    weight: float
    height: float
    goal: str
    activity_factor: float = DEFAULT_ACTIVITY_FACTOR
    dietary_preferences: Optional[Sequence[str]] = None


@dataclass
class Dish:
    dish_name: str
    ingredients: List[str]
    weight: float
    calories: float
    protein: float
    fat: float
    carbs: float
    tags: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Dish":
        return cls(
            dish_name=str(data["dish_name"]),
            ingredients=list(data.get("ingredients", [])),
            weight=float(data["weight"]),
            calories=float(data["calories"]),
            protein=float(data["protein"]),
            fat=float(data["fat"]),
            carbs=float(data["carbs"]),
            tags=[t.lower() for t in data.get("tags", [])],
        )


@dataclass
class MealPlan:
    dishes: List[Dish]
    totals: Dict[str, float]
    meal_count: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "dishes": [asdict(dish) for dish in self.dishes],
            "totals": self.totals,
            "meal_count": self.meal_count,
        }


def load_dishes(database_path: str) -> List[Dish]:
    if not os.path.exists(database_path):
        raise FileNotFoundError(f"Dish database not found at {database_path}")
    with open(database_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return [Dish.from_dict(entry) for entry in data]


def calculate_bmr(user: UserProfile) -> float:
    gender = user.gender.strip().lower()
    if gender not in {"male", "female"}:
        raise ValueError("Gender must be 'male' or 'female'")
    base = 10 * user.weight + 6.25 * user.height - 5 * user.age
    if gender == "male":
        return base + 5
    return base - 161


def estimate_tdee(user: UserProfile) -> float:
    return calculate_bmr(user) * user.activity_factor


def caloric_target(user: UserProfile) -> float:
    goal_key = user.goal.strip().lower().replace(" ", "_")
    multiplier = GOAL_CALORIE_MULTIPLIER.get(goal_key)
    if multiplier is None:
        raise ValueError("Unknown goal. Choose from weight_loss, muscle_gain, maintenance")
    return estimate_tdee(user) * multiplier


def macro_targets(total_calories: float, goal: str) -> Dict[str, float]:
    goal_key = goal.strip().lower().replace(" ", "_")
    ratios = GOAL_MACRO_RATIOS.get(goal_key)
    if ratios is None:
        raise ValueError("Unknown goal. Choose from weight_loss, muscle_gain, maintenance")
    targets = {}
    for macro, ratio in ratios.items():
        gram_value = (total_calories * ratio) / CALORIES_PER_GRAM[macro]
        targets[macro] = gram_value
    return targets


def _score_plan(plan_totals: Dict[str, float], target_calories: float, targets: Dict[str, float]) -> float:
    calorie_diff = abs(plan_totals["calories"] - target_calories)
    protein_diff = abs(plan_totals["protein"] - targets["protein"]) * CALORIES_PER_GRAM["protein"]
    fat_diff = abs(plan_totals["fat"] - targets["fat"]) * CALORIES_PER_GRAM["fat"]
    carb_diff = abs(plan_totals["carbs"] - targets["carbs"]) * CALORIES_PER_GRAM["carbs"]
    return calorie_diff + protein_diff + fat_diff + carb_diff


def _plan_totals(dishes: Iterable[Dish]) -> Dict[str, float]:
    totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    for dish in dishes:
        totals["calories"] += dish.calories
        totals["protein"] += dish.protein
        totals["fat"] += dish.fat
        totals["carbs"] += dish.carbs
    return totals

SVG_COLORS = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f"]


def _polar_to_cartesian(cx: float, cy: float, radius: float, angle_deg: float) -> Tuple[float, float]:
    angle_rad = math.radians(angle_deg)
    return cx + radius * math.cos(angle_rad), cy + radius * math.sin(angle_rad)


def _create_svg_pie(labels: Sequence[str], values: Sequence[float], path: str, title: str) -> str:
    total = sum(max(value, 0.0) for value in values) or 1.0
    radius = 120
    center = radius + 10
    segments = []
    start_angle = 0.0
    for idx, (label, value) in enumerate(zip(labels, values)):
        if value <= 0:
            continue
        angle = 360.0 * value / total
        end_angle = start_angle + angle
        x1, y1 = _polar_to_cartesian(center, center, radius, start_angle)
        x2, y2 = _polar_to_cartesian(center, center, radius, end_angle)
        large_arc = 1 if angle > 180 else 0
        color = SVG_COLORS[idx % len(SVG_COLORS)]
        path_data = (
            f"M {center} {center} L {x1:.2f} {y1:.2f} A {radius} {radius} 0 {large_arc} 1 {x2:.2f} {y2:.2f} Z"
        )
        segments.append(
            f"    <path d=\"{path_data}\" fill=\"{color}\" stroke=\"#ffffff\" stroke-width=\"1\" />"
        )
        label_angle = start_angle + angle / 2
        lx, ly = _polar_to_cartesian(center, center, radius * 0.6, label_angle)
        segments.append(
            f"    <text x=\"{lx:.2f}\" y=\"{ly:.2f}\" fill=\"#ffffff\" font-size=\"12\" text-anchor=\"middle\">{label}</text>"
        )
        start_angle = end_angle
    chart = [
        "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{0}\" height=\"{1}\">".format(
            (radius * 2) + 40, (radius * 2) + 40
        ),
        f"  <rect x=\"0\" y=\"0\" width=\"{(radius * 2) + 40}\" height=\"{(radius * 2) + 40}\" fill=\"#f9f9f9\"/>",
        f"  <text x=\"{center}\" y=\"30\" text-anchor=\"middle\" font-size=\"16\" fill=\"#333333\">{title}</text>",
    ]
    chart.extend(segments)
    chart.append("</svg>")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(chart))
    return path


def _create_svg_bar_chart(
    labels: Sequence[str],
    series: Dict[str, Sequence[float]],
    path: str,
    title: str,
    y_label: str,
) -> str:
    width = 600
    height = 350
    chart_width = width - 100
    chart_height = height - 100
    max_value = max((max(values) for values in series.values() if values), default=1)
    bar_gap = 10
    num_categories = len(labels)
    num_series = len(series)
    bar_width = (chart_width - (num_categories + 1) * bar_gap) / max(num_categories * num_series, 1)
    svg_lines = [
        f"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{width}\" height=\"{height}\">",
        "  <rect x=\"0\" y=\"0\" width=\"{0}\" height=\"{1}\" fill=\"#fdfdfd\" />".format(width, height),
        f"  <text x=\"{width/2}\" y=\"30\" text-anchor=\"middle\" font-size=\"18\" fill=\"#333\">{title}</text>",
        f"  <text x=\"60\" y=\"60\" font-size=\"12\" fill=\"#333\">{y_label}</text>",
        f"  <line x1=\"60\" y1=\"{height-60}\" x2=\"{width-40}\" y2=\"{height-60}\" stroke=\"#555\" stroke-width=\"1\" />",
        f"  <line x1=\"60\" y1=\"80\" x2=\"60\" y2=\"{height-60}\" stroke=\"#555\" stroke-width=\"1\" />",
    ]
    legend_x = width - 120
    legend_y = 90
    for idx, (series_name, values) in enumerate(series.items()):
        color = SVG_COLORS[idx % len(SVG_COLORS)]
        svg_lines.append(
            f"  <rect x=\"{legend_x}\" y=\"{legend_y + idx * 20}\" width=\"12\" height=\"12\" fill=\"{color}\" />"
        )
        svg_lines.append(
            f"  <text x=\"{legend_x + 18}\" y=\"{legend_y + idx * 20 + 10}\" font-size=\"12\" fill=\"#333\">{series_name}</text>"
        )
    for i, label in enumerate(labels):
        x_base = 60 + bar_gap + i * ((bar_width * num_series) + bar_gap)
        svg_lines.append(
            f"  <text x=\"{x_base + (bar_width * num_series)/2}\" y=\"{height-40}\" font-size=\"10\" fill=\"#333\" text-anchor=\"middle\" transform=\"rotate(45,{x_base + (bar_width * num_series)/2},{height-40})\">{label}</text>"
        )
        for s_idx, (series_name, values) in enumerate(series.items()):
            color = SVG_COLORS[s_idx % len(SVG_COLORS)]
            value = values[i]
            bar_height = 0 if max_value == 0 else (value / max_value) * (chart_height - 40)
            x = x_base + s_idx * bar_width
            y = (height - 60) - bar_height
            svg_lines.append(
                f"  <rect x=\"{x:.2f}\" y=\"{y:.2f}\" width=\"{bar_width:.2f}\" height=\"{bar_height:.2f}\" fill=\"{color}\" />"
            )
    svg_lines.append("</svg>")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(svg_lines))
    return path


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_simple_pdf(lines: Sequence[str], output_path: str) -> str:
    header = "%PDF-1.4\n"
    objects: List[str] = []
    offsets: List[int] = []

    def add_object(content: str) -> None:
        offsets.append(len(header) + sum(len(obj.encode("latin-1")) for obj in objects))
        objects.append(content)

    add_object("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    add_object("2 0 obj\n<< /Type /Pages /Kids [4 0 R] /Count 1 >>\nendobj\n")
    add_object("3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    content_lines = []
    y_position = 760
    for line in lines:
        safe = _escape_pdf_text(line)
        content_lines.append(f"BT /F1 12 Tf 60 {y_position} Td ({safe}) Tj ET")
        y_position -= 16
    content_stream = "\n".join(content_lines)
    add_object(
        "4 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 3 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>\nendobj\n"
    )
    add_object(
        "5 0 obj\n<< /Length {0} >>\nstream\n{1}\nendstream\nendobj\n".format(
            len(content_stream.encode("latin-1")), content_stream
        )
    )

    xref_start = len(header) + sum(len(obj.encode("latin-1")) for obj in objects)
    with open(output_path, "wb") as handle:
        handle.write(header.encode("latin-1"))
        for obj in objects:
            handle.write(obj.encode("latin-1"))
        handle.write(b"xref\n")
        handle.write(f"0 {len(objects) + 1}\n".encode("latin-1"))
        handle.write(b"0000000000 65535 f \n")
        for offset in offsets:
            handle.write(f"{offset:010} 00000 n \n".encode("latin-1"))
        handle.write(b"trailer\n")
        handle.write(f"<< /Root 1 0 R /Size {len(objects) + 1} >>\n".encode("latin-1"))
        handle.write(b"startxref\n")
        handle.write(f"{xref_start}\n".encode("latin-1"))
        handle.write(b"%%EOF")
    return output_path


    for dish in dishes:
        totals["calories"] += dish.calories
        totals["protein"] += dish.protein
        totals["fat"] += dish.fat
        totals["carbs"] += dish.carbs
    return totals


class MealPlanGenerator:
    def __init__(self, dishes: Sequence[Dish]):
        if not dishes:
            raise ValueError("Meal plan generator requires at least one dish")
        self.dishes = list(dishes)

    def _filter_by_preferences(self, preferences: Optional[Sequence[str]]) -> List[Dish]:
        if not preferences:
            return list(self.dishes)
        preferences = [pref.strip().lower() for pref in preferences]
        filtered = [dish for dish in self.dishes if all(pref in dish.tags for pref in preferences)]
        return filtered or list(self.dishes)

    def _candidate_combinations(
        self, dishes: List[Dish], meals_per_day: int
    ) -> Iterable[Tuple[Dish, ...]]:
        limited_dishes = dishes[: min(len(dishes), 7)]
        combos: List[Tuple[Dish, ...]] = []
        for count in range(1, meals_per_day + 1):
            combos.extend(combinations_with_replacement(limited_dishes, count))
        random.shuffle(combos)
        return combos[:500]

    def generate_plans(
        self,
        target_calories: float,
        targets: Dict[str, float],
        meals_per_day: int = 3,
        dietary_preferences: Optional[Sequence[str]] = None,
        num_options: int = 3,
    ) -> List[MealPlan]:
        if meals_per_day <= 0 or meals_per_day > 5:
            raise ValueError("Meals per day must be between 1 and 5")
        dishes = self._filter_by_preferences(dietary_preferences)
        best_plans: List[Tuple[float, MealPlan]] = []
        for combo in self._candidate_combinations(dishes, meals_per_day):
            totals = _plan_totals(combo)
            score = _score_plan(totals, target_calories, targets)
            best_plans.append((score, MealPlan(list(combo), totals, len(combo))))
        best_plans.sort(key=lambda item: item[0])
        unique_plans: List[MealPlan] = []
        seen_signatures = set()
        for _, plan in best_plans:
            signature = tuple(sorted(d.dish_name for d in plan.dishes))
            if signature not in seen_signatures:
                unique_plans.append(plan)
                seen_signatures.add(signature)
            if len(unique_plans) >= num_options:
                break
        if not unique_plans:
            raise ValueError("Unable to generate meal plans with the provided parameters")
        return unique_plans


def create_macro_pie_chart(plan: MealPlan, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    totals = plan.totals
    grams = [totals["protein"], totals["fat"], totals["carbs"]]
    labels = ["Protein", "Fat", "Carbohydrates"]
    if MATPLOTLIB_AVAILABLE and plt is not None:
        fig, ax = plt.subplots()
        ax.pie(grams, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.set_title("Macronutrient Distribution")
        path = os.path.join(output_dir, "macro_pie_chart.png")
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
    else:
        path = os.path.join(output_dir, "macro_pie_chart.svg")
        _create_svg_pie(labels, grams, path, "Macronutrient Distribution")
    return path


def create_meal_bar_chart(plan: MealPlan, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    labels = [dish.dish_name for dish in plan.dishes]
    calories = [dish.calories for dish in plan.dishes]
    protein = [dish.protein for dish in plan.dishes]
    fat = [dish.fat for dish in plan.dishes]
    carbs = [dish.carbs for dish in plan.dishes]

    if MATPLOTLIB_AVAILABLE and plt is not None:
        x_positions = range(len(labels))
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(x_positions, calories, label="Calories")
        ax.set_xticks(list(x_positions))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_ylabel("Calories")
        ax.set_title("Meal Level Calorie Distribution")
        fig.tight_layout()
        path_calories = os.path.join(output_dir, "meal_calories_bar_chart.png")
        fig.savefig(path_calories)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(8, 5))
        width = 0.2
        x_positions = list(range(len(labels)))
        ax.bar([x - width for x in x_positions], protein, width=width, label="Protein")
        ax.bar(x_positions, fat, width=width, label="Fat")
        ax.bar([x + width for x in x_positions], carbs, width=width, label="Carbs")
        ax.set_xticks(x_positions)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_ylabel("Grams")
        ax.set_title("Meal Level Macronutrients")
        ax.legend()
        fig.tight_layout()
        path_macros = os.path.join(output_dir, "meal_macros_bar_chart.png")
        fig.savefig(path_macros)
        plt.close(fig)
    else:
        path_calories = os.path.join(output_dir, "meal_calories_bar_chart.svg")
        _create_svg_bar_chart(
            labels,
            {"Calories": calories},
            path_calories,
            "Meal Level Calorie Distribution",
            "Calories",
        )
        path_macros = os.path.join(output_dir, "meal_macros_bar_chart.svg")
        _create_svg_bar_chart(
            labels,
            {"Protein": protein, "Fat": fat, "Carbs": carbs},
            path_macros,
            "Meal Level Macronutrients",
            "Grams",
        )
    return ";".join([path_calories, path_macros])


def export_report_pdf(
    plan: MealPlan,
    user: UserProfile,
    target_calories: float,
    macro_targets: Dict[str, float],
    output_path: str,
    pie_chart_path: Optional[str] = None,
    bar_chart_paths: Optional[str] = None,
) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    lines = ["Nutrition Analysis Report", "", "User Profile:"]
    for key, value in asdict(user).items():
        lines.append(f"  {key}: {value}")
    lines.extend(
        [
            "",
            f"Target Calories: {target_calories:.0f} kcal",
            "Target Macros (grams):",
            f"  Protein: {macro_targets['protein']:.1f}",
            f"  Fat: {macro_targets['fat']:.1f}",
            f"  Carbs: {macro_targets['carbs']:.1f}",
            "",
            "Meal Plan Totals:",
            f"  Calories: {plan.totals['calories']:.1f}",
            f"  Protein: {plan.totals['protein']:.1f}",
            f"  Fat: {plan.totals['fat']:.1f}",
            f"  Carbs: {plan.totals['carbs']:.1f}",
            "",
            "Meals:",
        ]
    )
    for idx, dish in enumerate(plan.dishes, start=1):
        lines.append(f"  {idx}. {dish.dish_name} ({dish.calories:.0f} kcal)")

    if MATPLOTLIB_AVAILABLE and PdfPages is not None and plt is not None:
        with PdfPages(output_path) as pdf:
            summary_fig, summary_ax = plt.subplots(figsize=(8.5, 11))
            summary_ax.axis("off")
            summary_text = "\n".join(lines)
            summary_ax.text(0, 1, summary_text, va="top", ha="left", fontsize=11)
            pdf.savefig(summary_fig, bbox_inches="tight")
            plt.close(summary_fig)

            if pie_chart_path:
                pie_fig = plt.figure()
                img = plt.imread(pie_chart_path)
                plt.imshow(img)
                plt.axis("off")
                pdf.savefig(pie_fig, bbox_inches="tight")
                plt.close(pie_fig)
            if bar_chart_paths:
                for path in bar_chart_paths.split(";"):
                    if path:
                        bar_fig = plt.figure()
                        img = plt.imread(path)
                        plt.imshow(img)
                        plt.axis("off")
                        pdf.savefig(bar_fig, bbox_inches="tight")
                        plt.close(bar_fig)
    else:
        extra_lines = [""]
        if pie_chart_path:
            extra_lines.append(f"Pie Chart: {pie_chart_path}")
        if bar_chart_paths:
            for path in bar_chart_paths.split(";"):
                if path:
                    extra_lines.append(f"Bar Chart: {path}")
        _write_simple_pdf(lines + extra_lines, output_path)
    return output_path


def export_plan_to_excel(plan: MealPlan, macro_targets: Dict[str, float], output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    rows = [
        "<?xml version=\"1.0\"?>",
        "<Workbook xmlns=\"urn:schemas-microsoft-com:office:spreadsheet\">",
        "  <Worksheet ss:Name=\"MealPlan\" xmlns:ss=\"urn:schemas-microsoft-com:office:spreadsheet\">",
        "    <Table>",
        "      <Row>",
        "        <Cell><Data ss:Type=\"String\">Dish Name</Data></Cell>",
        "        <Cell><Data ss:Type=\"Number\">Calories</Data></Cell>",
        "        <Cell><Data ss:Type=\"Number\">Protein</Data></Cell>",
        "        <Cell><Data ss:Type=\"Number\">Fat</Data></Cell>",
        "        <Cell><Data ss:Type=\"Number\">Carbs</Data></Cell>",
        "      </Row>",
    ]
    for dish in plan.dishes:
        rows.append("      <Row>")
        rows.append(f"        <Cell><Data ss:Type=\"String\">{dish.dish_name}</Data></Cell>")
        rows.append(f"        <Cell><Data ss:Type=\"Number\">{dish.calories}</Data></Cell>")
        rows.append(f"        <Cell><Data ss:Type=\"Number\">{dish.protein}</Data></Cell>")
        rows.append(f"        <Cell><Data ss:Type=\"Number\">{dish.fat}</Data></Cell>")
        rows.append(f"        <Cell><Data ss:Type=\"Number\">{dish.carbs}</Data></Cell>")
        rows.append("      </Row>")
    rows.extend(
        [
            "      <Row>",
            "        <Cell><Data ss:Type=\"String\">Totals</Data></Cell>",
            f"        <Cell><Data ss:Type=\"Number\">{plan.totals['calories']}</Data></Cell>",
            f"        <Cell><Data ss:Type=\"Number\">{plan.totals['protein']}</Data></Cell>",
            f"        <Cell><Data ss:Type=\"Number\">{plan.totals['fat']}</Data></Cell>",
            f"        <Cell><Data ss:Type=\"Number\">{plan.totals['carbs']}</Data></Cell>",
            "      </Row>",
            "      <Row>",
            "        <Cell><Data ss:Type=\"String\">Macro Targets (g)</Data></Cell>",
            f"        <Cell><Data ss:Type=\"Number\">{macro_targets['protein']}</Data></Cell>",
            f"        <Cell><Data ss:Type=\"Number\">{macro_targets['fat']}</Data></Cell>",
            f"        <Cell><Data ss:Type=\"Number\">{macro_targets['carbs']}</Data></Cell>",
            "        <Cell><Data ss:Type=\"String\"></Data></Cell>",
            "      </Row>",
            "    </Table>",
            "  </Worksheet>",
            "</Workbook>",
        ]
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(rows))
    return output_path


def generate_synthetic_dataset(num_records: int, output_path: str) -> str:
    if num_records <= 0:
        raise ValueError("Number of records must be positive")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    goals = list(GOAL_CALORIE_MULTIPLIER.keys())
    dietary_options = [
        None,
        ["vegetarian"],
        ["low-carb"],
        ["low-sugar"],
        ["high-protein"],
    ]
    records = []
    for _ in range(num_records):
        age = random.randint(18, 65)
        gender = random.choice(["male", "female"])
        weight = random.randint(50, 100)
        height = random.randint(150, 200)
        goal = random.choice(goals)
        activity_factor = random.choice([1.2, 1.375, 1.55])
        dietary_preferences = random.choice(dietary_options)
        profile = UserProfile(
            age=age,
            gender=gender,
            weight=weight,
            height=height,
            goal=goal,
            activity_factor=activity_factor,
            dietary_preferences=dietary_preferences,
        )
        target_cal = caloric_target(profile)
        macro_target = macro_targets(target_cal, goal)
        records.append(
            {
                "profile": asdict(profile),
                "target_calories": target_cal,
                "macro_targets": macro_target,
            }
        )
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2)
    return output_path


def generate_meal_plan(
    user: UserProfile,
    dishes: Sequence[Dish],
    meals_per_day: int = 3,
    dietary_preferences: Optional[Sequence[str]] = None,
    num_options: int = 3,
) -> Tuple[MealPlan, List[MealPlan], float, Dict[str, float]]:
    target_cal = caloric_target(user)
    macro_target = macro_targets(target_cal, user.goal)
    generator = MealPlanGenerator(dishes)
    plans = generator.generate_plans(
        target_cal,
        macro_target,
        meals_per_day=meals_per_day,
        dietary_preferences=dietary_preferences or user.dietary_preferences,
        num_options=num_options,
    )
    return plans[0], plans, target_cal, macro_target


__all__ = [
    "UserProfile",
    "Dish",
    "MealPlan",
    "calculate_bmr",
    "estimate_tdee",
    "caloric_target",
    "macro_targets",
    "load_dishes",
    "MealPlanGenerator",
    "create_macro_pie_chart",
    "create_meal_bar_chart",
    "export_report_pdf",
    "export_plan_to_excel",
    "generate_synthetic_dataset",
    "generate_meal_plan",
]
