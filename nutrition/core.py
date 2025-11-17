"""Core functionality for the nutrition analysis and meal planning system."""
from __future__ import annotations

import json
import math
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from itertools import combinations
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:  # pragma: no cover - matplotlib is optional and may not be available
    import matplotlib.pyplot as plt  # type: ignore
except Exception:  # pragma: no cover - we provide a safe fallback when missing
    plt = None  # type: ignore

# ---------------------------------------------------------------------------
# Basic domain models
# ---------------------------------------------------------------------------


class NutritionGoals(Enum):
    """Available nutrition goals."""

    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"


@dataclass
class UserProfile:
    """Information provided by the end user."""

    age: int
    gender: str
    weight: float  # kilograms
    height: float  # centimeters
    goal: NutritionGoals

    def normalized_gender(self) -> str:
        gender = self.gender.strip().lower()
        if gender not in {"male", "female"}:
            raise ValueError(f"Unsupported gender value: {self.gender!r}")
        return gender


@dataclass
class Dish:
    """Represents one entry in the dish database."""

    name: str
    ingredients: Sequence[str]
    weight: float
    calories: float
    protein: float
    fat: float
    carbs: float
    tags: Sequence[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "ingredients": list(self.ingredients),
            "weight": self.weight,
            "calories": self.calories,
            "protein": self.protein,
            "fat": self.fat,
            "carbs": self.carbs,
            "tags": list(self.tags),
        }


class DishDatabase:
    """Loads and filters dishes from the bundled data set."""

    def __init__(self, dishes: Sequence[Dish]):
        if not dishes:
            raise ValueError("Dish database may not be empty")
        self._dishes = list(dishes)

    def __iter__(self) -> Iterable[Dish]:
        return iter(self._dishes)

    @classmethod
    def load_default(cls) -> "DishDatabase":
        data_path = Path(__file__).resolve().parent / "dishes.json"
        with data_path.open("r", encoding="utf-8") as f:
            raw_dishes = json.load(f)
        dishes = [Dish(**entry) for entry in raw_dishes]
        return cls(dishes)

    def filter_by_preferences(self, preferences: Optional[Sequence[str]]) -> List[Dish]:
        if not preferences:
            return list(self._dishes)
        normalized = {pref.strip().lower() for pref in preferences if pref}
        if not normalized:
            return list(self._dishes)
        filtered: List[Dish] = []
        for dish in self._dishes:
            dish_tags = {tag.lower() for tag in dish.tags}
            if normalized.issubset(dish_tags):
                filtered.append(dish)
        return filtered or list(self._dishes)


@dataclass
class MealPlan:
    """Captures a generated meal plan and basic analytics."""

    dishes: Sequence[Dish]
    target_calories: float
    target_macros: Dict[str, float]
    total_calories: float = field(init=False)
    macro_totals: Dict[str, float] = field(init=False)

    def __post_init__(self) -> None:
        self.total_calories = sum(dish.calories for dish in self.dishes)
        self.macro_totals = {
            "protein": sum(dish.protein for dish in self.dishes),
            "fat": sum(dish.fat for dish in self.dishes),
            "carbs": sum(dish.carbs for dish in self.dishes),
        }

    @property
    def meal_breakdown(self) -> List[Dict[str, object]]:
        breakdown: List[Dict[str, object]] = []
        for index, dish in enumerate(self.dishes, start=1):
            breakdown.append(
                {
                    "meal": index,
                    "dish": dish.name,
                    "calories": dish.calories,
                    "protein": dish.protein,
                    "fat": dish.fat,
                    "carbs": dish.carbs,
                    "tags": list(dish.tags),
                }
            )
        return breakdown

    def error_score(self) -> float:
        cal_error = abs(self.total_calories - self.target_calories)
        macro_error = sum(
            abs(self.macro_totals[key] - self.target_macros[key]) for key in ("protein", "fat", "carbs")
        )
        return cal_error + macro_error


@dataclass
class NutritionReport:
    """Summarises the analytics and offers helper utilities."""

    profile: UserProfile
    goal: NutritionGoals
    activity_factor: float
    preferences: Sequence[str]
    daily_calories: float
    daily_macros: Dict[str, float]
    meal_options: Sequence[MealPlan]
    best_plan: MealPlan
    charts: Dict[str, Path] = field(default_factory=dict)

    def create_charts(self, output_dir: Path) -> Dict[str, Path]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        charts: Dict[str, Path] = {}

        macro_values = [self.daily_macros["protein"], self.daily_macros["fat"], self.daily_macros["carbs"]]
        macro_labels = ["Protein", "Fat", "Carbohydrates"]
        if plt is not None:
            pie_path = output_dir / "macros_pie.png"
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.pie(macro_values, labels=macro_labels, autopct="%1.1f%%")
            ax.set_title("Daily Macronutrient Distribution")
            fig.tight_layout()
            fig.savefig(pie_path)
            plt.close(fig)
        else:  # pragma: no cover - fallback path
            pie_path = output_dir / "macros_pie.txt"
            total = sum(macro_values)
            with pie_path.open("w", encoding="utf-8") as f:
                for label, value in zip(macro_labels, macro_values):
                    percentage = (value / total) * 100 if total else 0
                    f.write(f"{label}: {value:.1f}g ({percentage:.1f}%)\n")
        charts["macros"] = pie_path

        meal_path = output_dir / "meal_breakdown.png"
        meal_labels = [f"Meal {item['meal']}" for item in self.best_plan.meal_breakdown]
        meal_calories = [item["calories"] for item in self.best_plan.meal_breakdown]
        if plt is not None:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.bar(meal_labels, meal_calories, color="#4c72b0")
            ax.set_ylabel("Calories")
            ax.set_title("Meal Level Calorie Distribution")
            fig.tight_layout()
            fig.savefig(meal_path)
            plt.close(fig)
        else:  # pragma: no cover - fallback path
            meal_path = output_dir / "meal_breakdown.txt"
            with meal_path.open("w", encoding="utf-8") as f:
                for label, value in zip(meal_labels, meal_calories):
                    f.write(f"{label}: {value:.1f} kcal\n")
        charts["meals"] = meal_path

        self.charts = charts
        return charts

    def export_to_excel(self, output_path: Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        from xml.sax.saxutils import escape

        def column_letter(index: int) -> str:
            if index <= 0:
                raise ValueError("Column index must be positive")
            result = ""
            while index > 0:
                index, remainder = divmod(index - 1, 26)
                result = chr(65 + remainder) + result
            return result

        rows: List[List[object]] = [
            ["User", f"Goal: {self.goal.value.replace('_', ' ').title()}", "Activity Factor", self.activity_factor],
            ["Age", self.profile.age, "Gender", self.profile.gender.title()],
            ["Height (cm)", self.profile.height, "Weight (kg)", self.profile.weight],
            ["Target Calories", round(self.daily_calories, 2), "Preferences", ", ".join(self.preferences) or "None"],
            ["Target Protein (g)", round(self.daily_macros["protein"], 2)],
            ["Target Fat (g)", round(self.daily_macros["fat"], 2)],
            ["Target Carbs (g)", round(self.daily_macros["carbs"], 2)],
            [""],
            ["Meal", "Dish", "Calories", "Protein", "Fat", "Carbs", "Tags"],
        ]
        for item in self.best_plan.meal_breakdown:
            rows.append(
                [
                    item["meal"],
                    item["dish"],
                    round(item["calories"], 2),
                    round(item["protein"], 2),
                    round(item["fat"], 2),
                    round(item["carbs"], 2),
                    ", ".join(item["tags"]),
                ]
            )

        sheet_rows = []
        for row_index, row in enumerate(rows, start=1):
            cells = []
            for col_index, value in enumerate(row, start=1):
                cell_ref = f"{column_letter(col_index)}{row_index}"
                if value == "":
                    cells.append(f'<c r="{cell_ref}"/>')
                elif isinstance(value, (int, float)):
                    cells.append(f'<c r="{cell_ref}"><v>{value}</v></c>')
                else:
                    cell_text = escape(str(value))
                    cells.append(
                        f'<c r="{cell_ref}" t="inlineStr"><is><t>{cell_text}</t></is></c>'
                    )
            sheet_rows.append(f"<row r=\"{row_index}\">{''.join(cells)}</row>")

        worksheet_xml = (
            "<?xml version='1.0' encoding='UTF-8'?>"
            "<worksheet xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'"
            " xmlns:r='http://schemas.openxmlformats.org/officeDocument/2006/relationships'>"
            "<sheetData>"
            f"{''.join(sheet_rows)}"
            "</sheetData>"
            "</worksheet>"
        )

        workbook_xml = (
            "<?xml version='1.0' encoding='UTF-8'?>"
            "<workbook xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'"
            " xmlns:r='http://schemas.openxmlformats.org/officeDocument/2006/relationships'>"
            "<sheets>"
            "<sheet name='Nutrition Report' sheetId='1' r:id='rId1'/>"
            "</sheets>"
            "</workbook>"
        )

        workbook_rels = (
            "<?xml version='1.0' encoding='UTF-8'?>"
            "<Relationships xmlns='http://schemas.openxmlformats.org/officeDocument/2006/relationships'>"
            "<Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet' Target='worksheets/sheet1.xml'/>"
            "</Relationships>"
        )

        core_props = (
            "<?xml version='1.0' encoding='UTF-8'?>"
            "<cp:coreProperties xmlns:cp='http://schemas.openxmlformats.org/package/2006/metadata/core-properties'"
            " xmlns:dc='http://purl.org/dc/elements/1.1/'"
            " xmlns:dcterms='http://purl.org/dc/terms/'"
            " xmlns:dcmitype='http://purl.org/dc/dcmitype/'"
            " xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>"
            f"<dc:title>Nutrition Report for {escape(self.profile.gender.title())}</dc:title>"
            "<dc:creator>Nutrition System</dc:creator>"
            f"<cp:lastModifiedBy>Nutrition System</cp:lastModifiedBy>"
            f"<dcterms:created xsi:type='dcterms:W3CDTF'>{datetime.utcnow().isoformat()}Z</dcterms:created>"
            f"<dcterms:modified xsi:type='dcterms:W3CDTF'>{datetime.utcnow().isoformat()}Z</dcterms:modified>"
            "</cp:coreProperties>"
        )

        app_props = (
            "<?xml version='1.0' encoding='UTF-8'?>"
            "<Properties xmlns='http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'"
            " xmlns:vt='http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'>"
            "<Application>Nutrition System</Application>"
            "</Properties>"
        )

        content_types = (
            "<?xml version='1.0' encoding='UTF-8'?>"
            "<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>"
            "<Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/>"
            "<Default Extension='xml' ContentType='application/xml'/>"
            "<Override PartName='/xl/workbook.xml' ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml'/>"
            "<Override PartName='/xl/worksheets/sheet1.xml' ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml'/>"
            "<Override PartName='/docProps/core.xml' ContentType='application/vnd.openxmlformats-package.core-properties+xml'/>"
            "<Override PartName='/docProps/app.xml' ContentType='application/vnd.openxmlformats-officedocument.extended-properties+xml'/>"
            "</Types>"
        )

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", content_types)
            zf.writestr("_rels/.rels", "<?xml version='1.0' encoding='UTF-8'?><Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'><Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' Target='xl/workbook.xml'/></Relationships>")
            zf.writestr("docProps/core.xml", core_props)
            zf.writestr("docProps/app.xml", app_props)
            zf.writestr("xl/workbook.xml", workbook_xml)
            zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
            zf.writestr("xl/worksheets/sheet1.xml", worksheet_xml)

        return output_path


# ---------------------------------------------------------------------------
# Computation helpers
# ---------------------------------------------------------------------------


def calculate_bmr(profile: UserProfile) -> float:
    gender = profile.normalized_gender()
    if gender == "male":
        return 10 * profile.weight + 6.25 * profile.height - 5 * profile.age + 5
    return 10 * profile.weight + 6.25 * profile.height - 5 * profile.age - 161


def calculate_tdee(bmr: float, activity_factor: float) -> float:
    if activity_factor <= 0:
        raise ValueError("Activity factor must be positive")
    return bmr * activity_factor


def _goal_calorie_adjustment(goal: NutritionGoals) -> float:
    if goal == NutritionGoals.WEIGHT_LOSS:
        return 0.85
    if goal == NutritionGoals.MUSCLE_GAIN:
        return 1.1
    return 1.0


def _goal_macro_distribution(goal: NutritionGoals) -> Dict[str, float]:
    if goal == NutritionGoals.WEIGHT_LOSS:
        return {"protein": 0.27, "fat": 0.28, "carbs": 0.45}
    if goal == NutritionGoals.MUSCLE_GAIN:
        return {"protein": 0.3, "fat": 0.2, "carbs": 0.5}
    return {"protein": 0.25, "fat": 0.3, "carbs": 0.45}


def calculate_macros(calories: float, goal: NutritionGoals) -> Dict[str, float]:
    if calories <= 0:
        raise ValueError("Calorie target must be positive")
    distribution = _goal_macro_distribution(goal)
    protein = (calories * distribution["protein"]) / 4
    fat = (calories * distribution["fat"]) / 9
    carbs = (calories * distribution["carbs"]) / 4
    return {"protein": protein, "fat": fat, "carbs": carbs}


def _score_meal_combination(dishes: Sequence[Dish], target_calories: float, target_macros: Dict[str, float]) -> float:
    calories = sum(d.calories for d in dishes)
    protein = sum(d.protein for d in dishes)
    fat = sum(d.fat for d in dishes)
    carbs = sum(d.carbs for d in dishes)
    return abs(calories - target_calories) + abs(protein - target_macros["protein"]) + abs(fat - target_macros["fat"]) + abs(carbs - target_macros["carbs"])


def generate_meal_plan_options(
    profile: UserProfile,
    database: DishDatabase,
    activity_factor: float = 1.2,
    preferences: Optional[Sequence[str]] = None,
    num_meals: int = 3,
    alternatives: int = 3,
) -> Tuple[float, Dict[str, float], List[MealPlan]]:
    if num_meals < 1 or num_meals > 5:
        raise ValueError("Number of meals must be between 1 and 5")
    if alternatives < 1:
        raise ValueError("At least one meal plan should be produced")

    bmr = calculate_bmr(profile)
    tdee = calculate_tdee(bmr, activity_factor)
    caloric_multiplier = _goal_calorie_adjustment(profile.goal)
    daily_calories = tdee * caloric_multiplier
    daily_macros = calculate_macros(daily_calories, profile.goal)

    dishes = database.filter_by_preferences(preferences)
    if not dishes:
        raise ValueError("No dishes available for the given preferences")

    per_meal_calories = daily_calories / num_meals
    per_meal_macros = {key: value / num_meals for key, value in daily_macros.items()}

    # Rank dishes individually to reduce the search space when generating combinations.
    ranked_dishes = sorted(
        dishes,
        key=lambda dish: _score_meal_combination([dish], per_meal_calories, per_meal_macros),
    )
    search_pool = ranked_dishes[: max(num_meals + alternatives + 2, num_meals)]
    generated_plans: List[MealPlan] = []
    seen_signatures: set = set()

    for combo in combinations(search_pool, num_meals):
        signature = tuple(sorted(d.name for d in combo))
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        plan = MealPlan(dishes=list(combo), target_calories=daily_calories, target_macros=daily_macros)
        generated_plans.append(plan)

    generated_plans.sort(key=lambda plan: plan.error_score())

    while len(generated_plans) < alternatives:
        generated_plans.append(generated_plans[-1])

    return daily_calories, daily_macros, generated_plans[:alternatives]


def generate_nutrition_report(
    profile: UserProfile,
    activity_factor: float,
    database: Optional[DishDatabase] = None,
    preferences: Optional[Sequence[str]] = None,
    num_meals: int = 3,
    alternatives: int = 3,
    chart_dir: Optional[Path] = None,
) -> NutritionReport:
    database = database or DishDatabase.load_default()
    preferences = preferences or []

    daily_calories, daily_macros, meal_options = generate_meal_plan_options(
        profile,
        database,
        activity_factor=activity_factor,
        preferences=preferences,
        num_meals=num_meals,
        alternatives=alternatives,
    )

    report = NutritionReport(
        profile=profile,
        goal=profile.goal,
        activity_factor=activity_factor,
        preferences=preferences,
        daily_calories=daily_calories,
        daily_macros=daily_macros,
        meal_options=meal_options,
        best_plan=meal_options[0],
    )

    if chart_dir is not None:
        report.create_charts(chart_dir)

    return report
