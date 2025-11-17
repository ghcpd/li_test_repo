"""Reporting and visualization utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from .analysis import UserProfile
from .meal_planner import MealPlan


class ReportGenerator:
    """Generate visualizations and exportable reports for meal plans."""

    def __init__(self, profile: UserProfile, analysis: Dict[str, float]):
        self.profile = profile
        self.analysis = analysis

    def plan_dataframe(self, plan: MealPlan) -> pd.DataFrame:
        return pd.DataFrame(plan.meals)

    def export_to_excel(self, plan: MealPlan, output_path: Path) -> Path:
        df = self.plan_dataframe(plan)
        totals = plan.totals
        totals_row = {
            "meal_number": "Total",
            "dish_name": "",
            "ingredients": "",
            "calories": totals["calories"],
            "protein": totals["protein"],
            "fat": totals["fat"],
            "carbs": totals["carbs"],
            "tags": "",
        }
        with pd.ExcelWriter(output_path) as writer:
            df.to_excel(writer, index=False, sheet_name="Meal Plan")
            pd.DataFrame([totals_row]).to_excel(writer, index=False, sheet_name="Totals")
        return output_path

    def _macro_pie_figure(self, plan: MealPlan):
        totals = plan.totals
        fig, ax = plt.subplots(figsize=(6, 6))
        macros = [totals["protein"], totals["fat"], totals["carbs"]]
        labels = ["Protein (g)", "Fat (g)", "Carbs (g)"]
        ax.pie(macros, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.set_title("Macronutrient Distribution")
        ax.axis("equal")
        return fig

    def _meal_bar_figure(self, plan: MealPlan):
        df = self.plan_dataframe(plan)
        fig, ax = plt.subplots(figsize=(8, 6))
        x = df["meal_number"].astype(str)
        ax.bar(x, df["calories"], label="Calories", color="#FFB347")
        ax.set_xlabel("Meal")
        ax.set_ylabel("Calories")
        ax.set_title("Meal Calories")
        ax.legend(
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
        )
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        return fig

    def create_macro_pie_chart(self, plan: MealPlan, output_path: Path) -> Path:
        fig = self._macro_pie_figure(plan)
        fig.savefig(output_path, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def create_meal_bar_chart(self, plan: MealPlan, output_path: Path) -> Path:
        fig = self._meal_bar_figure(plan)
        fig.savefig(output_path, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def export_to_pdf(self, plan: MealPlan, output_path: Path) -> Path:
        totals = plan.totals
        df = self.plan_dataframe(plan)
        with PdfPages(output_path) as pdf:
            summary_fig, summary_ax = plt.subplots(figsize=(8.27, 11.69))
            summary_ax.axis("off")
            lines = [
                "Personalized Nutrition Report",
                "",
                f"Age: {self.profile.age}",
                f"Gender: {self.profile.gender}",
                f"Height (cm): {self.profile.height_cm}",
                f"Weight (kg): {self.profile.weight_kg}",
                f"Goal: {self.profile.goal}",
                f"Activity Level: {self.profile.activity_level}",
                "",
                f"BMR: {self.analysis['bmr']} kcal",
                f"TDEE: {self.analysis['tdee']} kcal",
                f"Calorie Target: {self.analysis['calorie_target']} kcal",
                f"Protein Target: {self.analysis['protein_target']} g",
                f"Fat Target: {self.analysis['fat_target']} g",
                f"Carbohydrate Target: {self.analysis['carb_target']} g",
                "",
                "Daily Meal Plan Totals:",
                f"Calories: {totals['calories']} kcal",
                f"Protein: {totals['protein']} g",
                f"Fat: {totals['fat']} g",
                f"Carbs: {totals['carbs']} g",
            ]
            summary_ax.text(0.05, 0.95, "\n".join(lines), va="top", fontsize=12)
            pdf.savefig(summary_fig, bbox_inches="tight")
            plt.close(summary_fig)

            table_fig, table_ax = plt.subplots(figsize=(10, 4))
            table_ax.axis("off")
            tbl = table_ax.table(
                cellText=df.values,
                colLabels=df.columns,
                loc="center",
            )
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(9)
            tbl.scale(1, 1.5)
            pdf.savefig(table_fig, bbox_inches="tight")
            plt.close(table_fig)

            pie_fig = self._macro_pie_figure(plan)
            pdf.savefig(pie_fig, bbox_inches="tight")
            plt.close(pie_fig)

            bar_fig = self._meal_bar_figure(plan)
            pdf.savefig(bar_fig, bbox_inches="tight")
            plt.close(bar_fig)
        return output_path
