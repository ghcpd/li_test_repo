"""Reporting utilities for nutrition analysis."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence
from zipfile import ZIP_DEFLATED, ZipFile

from .models import MealPlan, NutritionTargets


@dataclass
class NutritionReportGenerator:
    """Produces report artifacts such as charts and exports."""

    def summarize(self, plan: MealPlan, targets: NutritionTargets) -> Dict[str, object]:
        total = plan.totals()
        difference = {
            "calories": round(total.calories - targets.calories, 2),
            "protein_g": round(total.protein_g - targets.protein_g, 2),
            "fat_g": round(total.fat_g - targets.fat_g, 2),
            "carbs_g": round(total.carbs_g - targets.carbs_g, 2),
        }
        meals = []
        for meal in plan.meals:
            meals.append(
                {
                    "name": meal.name,
                    "totals": meal.totals().as_dict(),
                }
            )
        return {
            "targets": targets.as_dict(),
            "totals": total.as_dict(),
            "difference": difference,
            "meals": meals,
        }

    def macro_pie_chart_svg(self, plan: MealPlan, output_path: str) -> str:
        totals = plan.totals()
        macro_values = [
            ("Protein", totals.protein_g * 4, "#4CAF50"),
            ("Fat", totals.fat_g * 9, "#FF9800"),
            ("Carbohydrates", totals.carbs_g * 4, "#2196F3"),
        ]
        total_value = sum(value for _, value, _ in macro_values)
        if total_value <= 0:
            raise ValueError("Meal plan must contain positive macronutrient values")
        svg = _SVGBuilder(width=400, height=300)
        center_x, center_y, radius = 200, 150, 120
        current_angle = 0.0
        for label, value, color in macro_values:
            sweep = (value / total_value) * 2 * math.pi
            svg.add_pie_slice(center_x, center_y, radius, current_angle, current_angle + sweep, color, label, value / total_value)
            current_angle += sweep
        svg.add_legend(20, 20, [(label, color, value / total_value) for label, value, color in macro_values])
        svg.save(output_path)
        return output_path

    def meal_barchart_svg(self, plan: MealPlan, output_path: str) -> str:
        rows = []
        for meal in plan.meals:
            totals = meal.totals()
            rows.append((meal.name, totals.calories, totals.protein_g, totals.fat_g, totals.carbs_g))
        svg = _SVGBuilder(width=500, height=320)
        svg.add_bar_chart(rows)
        svg.save(output_path)
        return output_path

    def export_to_excel(self, summary: Dict[str, object], output_path: str) -> str:
        rows: List[List[object]] = [["Metric", "Calories", "Protein (g)", "Fat (g)", "Carbs (g)"]]
        totals = summary["totals"]
        targets = summary["targets"]
        difference = summary["difference"]
        rows.append(["Target", targets["calories"], targets["protein_g"], targets["fat_g"], targets["carbs_g"]])
        rows.append(["Actual", totals["calories"], totals["protein_g"], totals["fat_g"], totals["carbs_g"]])
        rows.append(["Difference", difference["calories"], difference["protein_g"], difference["fat_g"], difference["carbs_g"]])
        rows.append([])
        rows.append(["Meal", "Calories", "Protein (g)", "Fat (g)", "Carbs (g)"])
        for meal in summary["meals"]:
            totals = meal["totals"]
            rows.append([meal["name"], totals["calories"], totals["protein_g"], totals["fat_g"], totals["carbs_g"]])
        writer = _MinimalXLSXWriter()
        writer.add_sheet("Summary", rows)
        writer.save(output_path)
        return output_path

    def export_to_pdf(self, summary: Dict[str, object], output_path: str) -> str:
        pdf = _SimplePDFBuilder()
        pdf.add_title("Daily Nutrition Report")
        totals = summary["totals"]
        targets = summary["targets"]
        difference = summary["difference"]
        pdf.add_paragraph(f"Target Calories: {targets['calories']:.2f}")
        pdf.add_paragraph(f"Actual Calories: {totals['calories']:.2f}")
        pdf.add_paragraph(f"Difference: {difference['calories']:.2f}")
        pdf.add_paragraph("Meal Breakdown:")
        for meal in summary["meals"]:
            totals = meal["totals"]
            pdf.add_paragraph(
                f"- {meal['name']}: {totals['calories']:.2f} kcal, {totals['protein_g']:.2f} g protein, {totals['fat_g']:.2f} g fat, {totals['carbs_g']:.2f} g carbs"
            )
        pdf.save(output_path)
        return output_path


class _SVGBuilder:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.elements: List[str] = [
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{self.width}' height='{self.height}'>"
        ]

    def add_pie_slice(
        self,
        cx: float,
        cy: float,
        radius: float,
        start_angle: float,
        end_angle: float,
        color: str,
        label: str,
        percentage: float,
    ) -> None:
        start_x = cx + radius * math.cos(start_angle)
        start_y = cy + radius * math.sin(start_angle)
        end_x = cx + radius * math.cos(end_angle)
        end_y = cy + radius * math.sin(end_angle)
        large_arc_flag = 1 if end_angle - start_angle > math.pi else 0
        path = (
            f"M {cx} {cy} L {start_x:.2f} {start_y:.2f} A {radius} {radius} 0 {large_arc_flag} 1 {end_x:.2f} {end_y:.2f} Z"
        )
        self.elements.append(f"<path d='{path}' fill='{color}' opacity='0.8'></path>")
        mid_angle = (start_angle + end_angle) / 2
        label_x = cx + (radius * 0.6) * math.cos(mid_angle)
        label_y = cy + (radius * 0.6) * math.sin(mid_angle)
        self.elements.append(
            f"<text x='{label_x:.2f}' y='{label_y:.2f}' font-size='12' text-anchor='middle'>{int(percentage * 100)}%</text>"
        )

    def add_legend(self, x: float, y: float, items: Sequence[tuple[str, str, float]]) -> None:
        offset_y = y
        for label, color, pct in items:
            self.elements.append(f"<rect x='{x}' y='{offset_y}' width='14' height='14' fill='{color}'></rect>")
            self.elements.append(
                f"<text x='{x + 20}' y='{offset_y + 12}' font-size='12'>{label} ({pct * 100:.0f}%)</text>"
            )
            offset_y += 20

    def add_bar_chart(self, rows: List[tuple[str, float, float, float, float]]) -> None:
        margin = 50
        chart_width = self.width - margin * 2
        chart_height = self.height - margin * 2
        max_value = max(row[1] for row in rows)
        bar_width = chart_width / (len(rows) * 4)
        x_offset = margin
        colors = ["#03A9F4", "#4CAF50", "#FF9800", "#9C27B0"]
        for meal, calories, protein, fat, carbs in rows:
            values = [calories, protein * 4, fat * 9, carbs * 4]
            for index, value in enumerate(values):
                height = (value / max_value) * chart_height if max_value else 0
                x = x_offset + (index * bar_width)
                y = margin + chart_height - height
                self.elements.append(
                    f"<rect x='{x:.2f}' y='{y:.2f}' width='{bar_width - 4:.2f}' height='{height:.2f}' fill='{colors[index]}'></rect>"
                )
            self.elements.append(f"<text x='{x_offset + bar_width}' y='{self.height - 10}' font-size='12'>{meal}</text>")
            x_offset += bar_width * 4
        self.elements.append(f"<line x1='{margin}' y1='{margin}' x2='{margin}' y2='{self.height - margin}' stroke='#333'></line>")
        self.elements.append(
            f"<line x1='{margin}' y1='{self.height - margin}' x2='{self.width - margin}' y2='{self.height - margin}' stroke='#333'></line>"
        )

    def save(self, path: str) -> None:
        self.elements.append("</svg>")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(self.elements))



_SHEET_OVERRIDE_TEMPLATE = "<Override PartName='/xl/worksheets/sheet{index}.xml' ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml'/>"


class _MinimalXLSXWriter:
    def __init__(self) -> None:
        self.sheets: List[tuple[str, List[List[object]]]] = []

    def add_sheet(self, name: str, rows: List[List[object]]) -> None:
        self.sheets.append((name, rows))

    def save(self, path: str) -> None:
        if not self.sheets:
            raise ValueError("No sheets added")
        with ZipFile(path, "w", ZIP_DEFLATED) as zf:
            overrides = []
            zf.writestr("_rels/.rels", _ROOT_RELS)
            sheet_rels = []
            sheet_refs = []
            for index, (name, rows) in enumerate(self.sheets, start=1):
                sheet_rels.append(
                    f"<Relationship Id='rId{index}' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet' Target='worksheets/sheet{index}.xml'/>"
                )
                sheet_refs.append(
                    f"<sheet name='{_xml_escape(name)}' sheetId='{index}' r:id='rId{index}'/>"
                )
                overrides.append(_SHEET_OVERRIDE_TEMPLATE.format(index=index))
                sheet_xml = _sheet_xml(rows)
                zf.writestr(f"xl/worksheets/sheet{index}.xml", sheet_xml)
            workbook_rels = _WORKBOOK_RELS_TEMPLATE.format(sheet_rels="".join(sheet_rels))
            zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
            workbook_xml = _WORKBOOK_TEMPLATE.format(sheets="".join(sheet_refs))
            zf.writestr("xl/workbook.xml", workbook_xml)
            content_types = _CONTENT_TYPES_TEMPLATE.format(sheet_overrides="".join(overrides))
            zf.writestr("[Content_Types].xml", content_types)


class _SimplePDFBuilder:
    def __init__(self) -> None:
        self.lines: List[str] = []
    def add_title(self, text: str) -> None:
        self.lines.append(f"<b>{text}</b>")

    def add_paragraph(self, text: str) -> None:
        self.lines.append(text)

    def save(self, path: str) -> None:
        pdf_objects: List[str] = []
        offsets: List[int] = []

        def register(obj: str) -> None:
            offsets.append(sum(len(obj) for obj in pdf_objects))
            pdf_objects.append(obj)

        register("1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
        register("2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
        content = "BT /F1 12 Tf 72 720 Td "
        y_offset = 0
        for line in self.lines:
            cleaned = line.replace("(", "[").replace(")", "]")
            content += f"({cleaned}) Tj 0 -18 Td "
            y_offset += 18
        content += "ET"
        stream = f"4 0 obj<< /Length {len(content)} >>stream\n{content}\nendstream\n"
        register("3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n")
        register(stream)
        register("5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n")
        header = "%PDF-1.4\n"
        xref_offset = len(header) + sum(len(obj) for obj in pdf_objects)
        xref_lines = ["xref", "0 6", "0000000000 65535 f "]
        total_offset = len(header)
        for obj in pdf_objects:
            xref_lines.append(f"{total_offset:010} 00000 n ")
            total_offset += len(obj)
        trailer = "trailer<< /Size 6 /Root 1 0 R >>startxref\n" + str(xref_offset) + "\n%%EOF"
        with open(path, "wb") as handle:
            handle.write(header.encode("latin-1"))
            for obj in pdf_objects:
                handle.write(obj.encode("latin-1"))
            handle.write("\n".join(xref_lines).encode("latin-1"))
            handle.write(b"\n")
            handle.write(trailer.encode("latin-1"))


_CONTENT_TYPES_TEMPLATE = """<?xml version='1.0' encoding='UTF-8'?>
<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>
<Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/>
<Default Extension='xml' ContentType='application/xml'/>
<Override PartName='/xl/workbook.xml' ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml'/>
{sheet_overrides}
</Types>"""

_ROOT_RELS = """<?xml version='1.0' encoding='UTF-8'?>
<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>
<Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' Target='xl/workbook.xml'/>
</Relationships>"""

_WORKBOOK_RELS_TEMPLATE = """<?xml version='1.0' encoding='UTF-8'?>
<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>
{sheet_rels}
</Relationships>"""

_WORKBOOK_TEMPLATE = """<?xml version='1.0' encoding='UTF-8'?>
<workbook xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main' xmlns:r='http://schemas.openxmlformats.org/officeDocument/2006/relationships'>
<sheets>{sheets}</sheets>
</workbook>"""


def _sheet_xml(rows: Iterable[Sequence[object]]) -> str:
    xml_rows: List[str] = ["<?xml version='1.0' encoding='UTF-8'?>", "<worksheet xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'>", "<sheetData>"]
    for row_index, row in enumerate(rows, start=1):
        xml_rows.append(f"<row r='{row_index}'>")
        for col_index, value in enumerate(row, start=1):
            cell_ref = _column_letter(col_index) + str(row_index)
            if isinstance(value, (int, float)):
                xml_rows.append(f"<c r='{cell_ref}' t='n'><v>{value}</v></c>")
            elif value == "":
                xml_rows.append(f"<c r='{cell_ref}'/>")
            else:
                xml_rows.append(f"<c r='{cell_ref}' t='inlineStr'><is><t>{_xml_escape(str(value))}</t></is></c>")
        xml_rows.append("</row>")
    xml_rows.append("</sheetData></worksheet>")
    return "".join(xml_rows)


def _column_letter(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _xml_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;").replace('"', "&quot;")
