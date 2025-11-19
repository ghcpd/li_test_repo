"""Reporting utilities for nutrition analysis."""

from __future__ import annotations

import csv
import math
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence
from zipfile import ZipFile

from .analyzer import NutritionTargets
from .models import MealPlan, UserProfile

SVG_HEADER = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>"
SVG_NAMESPACE = "http://www.w3.org/2000/svg"


@dataclass
class ReportArtifacts:
    summary: Dict[str, float]
    macro_ratios: Dict[str, float]
    pie_chart_svg: str
    bar_chart_svg: str
    pdf_path: str | None = None
    excel_path: str | None = None
    pie_chart_path: str | None = None
    bar_chart_path: str | None = None


class NutritionReport:
    """Generate reports and exports for nutrition analysis."""

    def __init__(self, user: UserProfile, targets: NutritionTargets, plan: MealPlan) -> None:
        self.user = user
        self.targets = targets
        self.plan = plan

    def summary(self) -> Dict[str, float]:
        totals = self.plan.summary()
        return {
            "calories_target": round(self.targets.calories, 2),
            "calories_actual": totals["calories"],
            "protein_target": round(self.targets.protein_grams, 2),
            "protein_actual": totals["protein"],
            "fat_target": round(self.targets.fat_grams, 2),
            "fat_actual": totals["fat"],
            "carb_target": round(self.targets.carb_grams, 2),
            "carb_actual": totals["carbs"],
        }

    def macro_ratios(self) -> Dict[str, float]:
        return self.targets.macro_ratios()

    def create_pie_chart_svg(self) -> str:
        ratios = self.macro_ratios()
        segments = [
            ("protein", ratios.get("protein", 0.0), "#ff7043"),
            ("fat", ratios.get("fat", 0.0), "#66bb6a"),
            ("carbs", ratios.get("carbs", 0.0), "#42a5f5"),
        ]
        cx, cy, radius = 100, 100, 90
        start_angle = -math.pi / 2
        paths = []
        for label, value, color in segments:
            sweep = value * 2 * math.pi
            end_angle = start_angle + sweep
            x1 = cx + radius * math.cos(start_angle)
            y1 = cy + radius * math.sin(start_angle)
            x2 = cx + radius * math.cos(end_angle)
            y2 = cy + radius * math.sin(end_angle)
            large_arc = 1 if sweep > math.pi else 0
            if value <= 0:
                start_angle = end_angle
                continue
            path = (
                f"<path d=\"M {cx} {cy} L {x1:.2f} {y1:.2f} A {radius} {radius} 0 "
                f"{large_arc} 1 {x2:.2f} {y2:.2f} Z\" fill=\"{color}\" "
                f"stroke=\"#ffffff\" stroke-width=\"1\" />"
            )
            paths.append(path)
            start_angle = end_angle
        legend_entries = []
        for idx, (label, value, color) in enumerate(segments):
            legend_entries.append(
                f"<rect x=\"210\" y=\"{20 + idx * 20}\" width=\"12\" height=\"12\" fill=\"{color}\" />"
            )
            legend_entries.append(
                f"<text x=\"230\" y=\"{30 + idx * 20}\" font-size=\"12\">"
                f"{label.title()} {(value * 100):.1f}%</text>"
            )
        svg = (
            f"{SVG_HEADER}<svg xmlns=\"{SVG_NAMESPACE}\" width=\"320\" height=\"200\">"
            f"<g>{''.join(paths)}</g>"
            f"{''.join(legend_entries)}</svg>"
        )
        return svg

    def create_bar_chart_svg(self) -> str:
        meals = self.plan.meals
        if not meals:
            return f"{SVG_HEADER}<svg xmlns=\"{SVG_NAMESPACE}\" width=\"400\" height=\"200\" />"
        metrics = []
        for meal in meals:
            metrics.append(
                {
                    "label": meal.description,
                    "calories": meal.calories,
                    "protein": meal.protein * 4,
                    "fat": meal.fat * 9,
                    "carbs": meal.carbs * 4,
                }
            )
        numeric_keys = ["calories", "protein", "fat", "carbs"]
        max_value = max(
            max(item[key] for key in numeric_keys) for item in metrics
        )
        width = 120 * len(metrics)
        svg_elements = [
            f"{SVG_HEADER}<svg xmlns=\"{SVG_NAMESPACE}\" width=\"{width}\" height=\"220\">"
        ]
        for idx, meal in enumerate(metrics):
            x_base = idx * 120 + 40
            for offset, (key, color) in enumerate(
                [
                    ("calories", "#42a5f5"),
                    ("protein", "#ef5350"),
                    ("fat", "#ab47bc"),
                    ("carbs", "#66bb6a"),
                ]
            ):
                value = meal[key]
                height = 160 * (value / max_value) if max_value else 0
                x = x_base + offset * 20
                y = 200 - height
                svg_elements.append(
                    f"<rect x=\"{x}\" y=\"{y:.2f}\" width=\"16\" height=\"{height:.2f}\" fill=\"{color}\" />"
                )
            svg_elements.append(
                f"<text x=\"{x_base + 40}\" y=\"210\" font-size=\"12\" text-anchor=\"middle\">"
                f"{meal['label']}</text>"
            )
        svg_elements.append("</svg>")
        return "".join(svg_elements)

    def _pdf_text(self, x: int, y: int, text: str) -> str:
        escaped = text.replace("(", "\\(").replace(")", "\\)")
        return f"BT /F1 12 Tf {x} {y} Td ({escaped}) Tj ET"

    def export_pdf(self, path: str) -> None:
        lines = [
            "Nutrition Analysis & Meal Plan",
            f"User: Age {self.user.age}, {self.user.gender.title()}; Goal: {self.user.goal.title()}",
            f"Calories: {self.targets.calories:.0f} kcal",
            f"Protein Target: {self.targets.protein_grams:.1f} g",
            f"Fat Target: {self.targets.fat_grams:.1f} g",
            f"Carb Target: {self.targets.carb_grams:.1f} g",
        ]
        lines.append("Meal Plan:")
        for idx, meal in enumerate(self.plan.meals, start=1):
            lines.append(
                f"  {idx}. {meal.description} - {meal.calories:.0f} kcal, P {meal.protein:.1f}g, "
                f"F {meal.fat:.1f}g, C {meal.carbs:.1f}g"
            )
        content_stream = "\n".join(self._pdf_text(50, 760 - i * 20, line) for i, line in enumerate(lines))
        stream_bytes = content_stream.encode("latin-1", "replace")
        objects = [
            "1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj",
            "2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj",
            "3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
            "/Resources <</Font <</F1 5 0 R>>>>>> endobj",
            f"4 0 obj <</Length {len(stream_bytes)}>> stream\n{content_stream}\nendstream endobj",
            "5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj",
        ]
        with open(path, "wb") as handle:
            handle.write(b"%PDF-1.4\n")
            offsets: List[int] = []
            for obj in objects:
                offsets.append(handle.tell())
                handle.write((obj + "\n").encode("latin-1", "replace"))
            xref_start = handle.tell()
            count = len(objects) + 1
            handle.write(f"xref\n0 {count}\n".encode("ascii"))
            handle.write(b"0000000000 65535 f \n")
            for off in offsets:
                handle.write(f"{off:010d} 00000 n \n".encode("ascii"))
            handle.write(
                f"trailer <</Size {count} /Root 1 0 R>>\nstartxref\n{xref_start}\n%%EOF"
                .encode("ascii")
            )

    def _xml_escape(self, value: object) -> str:
        return (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\"", "&quot;")
        )

    def _sheet_rows(self) -> List[List[object]]:
        summary_rows = [["Metric", "Value"]]
        for key, value in self.summary().items():
            summary_rows.append([key.replace("_", " ").title(), value])
        meal_rows = self.plan.to_rows()
        blank_row = [""] * max(len(summary_rows[0]), len(meal_rows[0]))
        return summary_rows + [blank_row] + meal_rows

    def export_excel(self, path: str) -> None:
        rows = self._sheet_rows()
        workbook_xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" "
            "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
            "<sheets><sheet name=\"Report\" sheetId=\"1\" r:id=\"rId1\"/></sheets>"
            "</workbook>"
        )
        relationships_xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" "
            "Target=\"worksheets/sheet1.xml\"/>"
            "</Relationships>"
        )
        rels_xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" "
            "Target=\"xl/workbook.xml\"/>"
            "</Relationships>"
        )
        sheet_rows = []
        for idx, row in enumerate(rows, start=1):
            cells = []
            for col_idx, value in enumerate(row, start=1):
                column_letter = chr(ord("A") + col_idx - 1)
                cell_ref = f"{column_letter}{idx}"
                cell_value = self._xml_escape(value)
                cells.append(
                    f"<c r=\"{cell_ref}\" t=\"inlineStr\"><is><t>{cell_value}</t></is></c>"
                )
            sheet_rows.append(f"<row r=\"{idx}\">{''.join(cells)}</row>")
        sheet_xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
            f"<sheetData>{''.join(sheet_rows)}</sheetData></worksheet>"
        )
        content_types = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
            "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
            "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
            "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
            "<Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
            "</Types>"
        )
        with ZipFile(path, "w") as archive:
            archive.writestr("[Content_Types].xml", content_types)
            archive.writestr("_rels/.rels", rels_xml)
            archive.writestr("xl/workbook.xml", workbook_xml)
            archive.writestr("xl/_rels/workbook.xml.rels", relationships_xml)
            archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)

    def export_csv(self, path: str) -> None:
        rows = self._sheet_rows()
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerows(rows)

    def save_charts(self, directory: str, base_name: str = "nutrition") -> Dict[str, str]:
        os.makedirs(directory, exist_ok=True)
        pie_path = os.path.join(directory, f"{base_name}_macro_pie.svg")
        bar_path = os.path.join(directory, f"{base_name}_meals_bar.svg")
        with open(pie_path, "w", encoding="utf-8") as pie:
            pie.write(self.create_pie_chart_svg())
        with open(bar_path, "w", encoding="utf-8") as bar:
            bar.write(self.create_bar_chart_svg())
        return {"pie_chart": pie_path, "bar_chart": bar_path}

    def export_all(
        self,
        directory: str,
        base_name: str = "nutrition_report",
        include_pdf: bool = True,
        include_excel: bool = True,
    ) -> ReportArtifacts:
        os.makedirs(directory, exist_ok=True)
        pdf_path = os.path.join(directory, f"{base_name}.pdf") if include_pdf else None
        excel_path = os.path.join(directory, f"{base_name}.xlsx") if include_excel else None
        pie_chart_svg = self.create_pie_chart_svg()
        bar_chart_svg = self.create_bar_chart_svg()
        saved_charts = self.save_charts(directory, base_name)
        if include_pdf and pdf_path:
            self.export_pdf(pdf_path)
        if include_excel and excel_path:
            self.export_excel(excel_path)
        return ReportArtifacts(
            summary=self.summary(),
            macro_ratios=self.macro_ratios(),
            pie_chart_svg=pie_chart_svg,
            bar_chart_svg=bar_chart_svg,
            pdf_path=pdf_path,
            excel_path=excel_path,
            pie_chart_path=saved_charts.get("pie_chart"),
            bar_chart_path=saved_charts.get("bar_chart"),
        )
