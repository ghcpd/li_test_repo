"""
Module 3: Nutrition Analysis Report
Generates reports with visualizations and exports to PDF/Excel.
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import pandas as pd
from datetime import datetime
import os


class ReportGenerator:
    """Generates nutrition analysis reports with visualizations."""
    
    def __init__(self, nutrition_analysis, meal_plan):
        """
        Initialize report generator.
        
        Args:
            nutrition_analysis (dict): Nutrition analysis results
            meal_plan (dict): Selected meal plan
        """
        self.nutrition_analysis = nutrition_analysis
        self.meal_plan = meal_plan
    
    def create_pie_chart(self, output_path='macro_pie_chart.png'):
        """
        Create a pie chart showing macronutrient distribution.
        
        Args:
            output_path (str): Path to save the chart
        
        Returns:
            str: Path to saved chart
        """
        # Get total macros from meal plan
        totals = self.meal_plan['total_nutrition']
        
        # Calculate calories from each macro
        protein_cal = totals['protein'] * 4
        fat_cal = totals['fat'] * 9
        carbs_cal = totals['carbs'] * 4
        
        labels = ['Protein', 'Fat', 'Carbs']
        sizes = [protein_cal, fat_cal, carbs_cal]
        colors_list = ['#ff9999', '#66b3ff', '#99ff99']
        explode = (0.05, 0.05, 0.05)
        
        plt.figure(figsize=(8, 6))
        plt.pie(sizes, explode=explode, labels=labels, colors=colors_list,
                autopct='%1.1f%%', shadow=True, startangle=90)
        plt.axis('equal')
        plt.title('Macronutrient Distribution', fontsize=16, fontweight='bold')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def create_bar_chart(self, output_path='meal_bar_chart.png'):
        """
        Create a bar chart showing calories and macros per meal.
        
        Args:
            output_path (str): Path to save the chart
        
        Returns:
            str: Path to saved chart
        """
        meals = self.meal_plan['meals']
        meal_names = [meal['dish_name'] for meal in meals]
        
        # Prepare data
        calories = [meal['calories'] for meal in meals]
        protein = [meal['protein'] for meal in meals]
        fat = [meal['fat'] for meal in meals]
        carbs = [meal['carbs'] for meal in meals]
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Meal-Level Nutritional Breakdown', fontsize=16, fontweight='bold')
        
        # Calories
        axes[0, 0].bar(range(len(meal_names)), calories, color='#ff9999')
        axes[0, 0].set_title('Calories per Meal', fontweight='bold')
        axes[0, 0].set_ylabel('Calories')
        axes[0, 0].set_xticks(range(len(meal_names)))
        axes[0, 0].set_xticklabels(meal_names, rotation=45, ha='right')
        axes[0, 0].grid(axis='y', alpha=0.3)
        
        # Protein
        axes[0, 1].bar(range(len(meal_names)), protein, color='#66b3ff')
        axes[0, 1].set_title('Protein per Meal (g)', fontweight='bold')
        axes[0, 1].set_ylabel('Grams')
        axes[0, 1].set_xticks(range(len(meal_names)))
        axes[0, 1].set_xticklabels(meal_names, rotation=45, ha='right')
        axes[0, 1].grid(axis='y', alpha=0.3)
        
        # Fat
        axes[1, 0].bar(range(len(meal_names)), fat, color='#ffcc99')
        axes[1, 0].set_title('Fat per Meal (g)', fontweight='bold')
        axes[1, 0].set_ylabel('Grams')
        axes[1, 0].set_xticks(range(len(meal_names)))
        axes[1, 0].set_xticklabels(meal_names, rotation=45, ha='right')
        axes[1, 0].grid(axis='y', alpha=0.3)
        
        # Carbs
        axes[1, 1].bar(range(len(meal_names)), carbs, color='#99ff99')
        axes[1, 1].set_title('Carbs per Meal (g)', fontweight='bold')
        axes[1, 1].set_ylabel('Grams')
        axes[1, 1].set_xticks(range(len(meal_names)))
        axes[1, 1].set_xticklabels(meal_names, rotation=45, ha='right')
        axes[1, 1].grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def export_to_pdf(self, output_path='nutrition_report.pdf'):
        """
        Export nutrition analysis and meal plan to PDF.
        
        Args:
            output_path (str): Path to save the PDF
        
        Returns:
            str: Path to saved PDF
        """
        # Create charts
        pie_chart_path = '/tmp/macro_pie_chart.png'
        bar_chart_path = '/tmp/meal_bar_chart.png'
        self.create_pie_chart(pie_chart_path)
        self.create_bar_chart(bar_chart_path)
        
        # Create PDF
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        story.append(Paragraph('Personalized Nutrition Analysis Report', title_style))
        story.append(Paragraph(f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # User Information
        story.append(Paragraph('User Profile', heading_style))
        user_info = self.nutrition_analysis['user_info']
        user_data = [
            ['Parameter', 'Value'],
            ['Age', f"{user_info['age']} years"],
            ['Gender', user_info['gender'].capitalize()],
            ['Weight', f"{user_info['weight']} kg"],
            ['Height', f"{user_info['height']} cm"],
            ['Goal', user_info['goal'].replace('_', ' ').title()],
            ['Activity Level', user_info['activity_level'].replace('_', ' ').title()]
        ]
        
        user_table = Table(user_data, colWidths=[2.5*inch, 2.5*inch])
        user_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(user_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Nutritional Requirements
        story.append(Paragraph('Nutritional Requirements', heading_style))
        req_data = [
            ['Metric', 'Value'],
            ['Basal Metabolic Rate (BMR)', f"{self.nutrition_analysis['bmr']} calories/day"],
            ['Total Daily Energy Expenditure (TDEE)', f"{self.nutrition_analysis['tdee']} calories/day"],
            ['Target Calories', f"{self.nutrition_analysis['target_calories']} calories/day"],
            ['Target Protein', f"{self.nutrition_analysis['macros']['protein']} g"],
            ['Target Fat', f"{self.nutrition_analysis['macros']['fat']} g"],
            ['Target Carbohydrates', f"{self.nutrition_analysis['macros']['carbs']} g"]
        ]
        
        req_table = Table(req_data, colWidths=[3*inch, 2*inch])
        req_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(req_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Meal Plan
        story.append(Paragraph('Recommended Meal Plan', heading_style))
        meal_data = [['Meal', 'Calories', 'Protein (g)', 'Fat (g)', 'Carbs (g)']]
        
        for meal in self.meal_plan['meals']:
            meal_data.append([
                meal['dish_name'],
                str(meal['calories']),
                str(meal['protein']),
                str(meal['fat']),
                str(meal['carbs'])
            ])
        
        # Add totals row
        totals = self.meal_plan['total_nutrition']
        meal_data.append([
            'TOTAL',
            str(totals['calories']),
            str(totals['protein']),
            str(totals['fat']),
            str(totals['carbs'])
        ])
        
        meal_table = Table(meal_data, colWidths=[2.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        meal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f39c12')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(meal_table)
        story.append(PageBreak())
        
        # Charts
        story.append(Paragraph('Nutritional Visualizations', heading_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Add pie chart
        story.append(Image(pie_chart_path, width=5*inch, height=3.75*inch))
        story.append(Spacer(1, 0.3*inch))
        
        # Add bar chart
        story.append(Image(bar_chart_path, width=6.5*inch, height=4.875*inch))
        
        # Build PDF
        doc.build(story)
        
        # Clean up temporary files
        if os.path.exists(pie_chart_path):
            os.remove(pie_chart_path)
        if os.path.exists(bar_chart_path):
            os.remove(bar_chart_path)
        
        return output_path
    
    def export_to_excel(self, output_path='nutrition_report.xlsx'):
        """
        Export nutrition analysis and meal plan to Excel.
        
        Args:
            output_path (str): Path to save the Excel file
        
        Returns:
            str: Path to saved Excel file
        """
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # User Information
            user_info = self.nutrition_analysis['user_info']
            user_df = pd.DataFrame({
                'Parameter': ['Age', 'Gender', 'Weight (kg)', 'Height (cm)', 'Goal', 'Activity Level'],
                'Value': [
                    user_info['age'],
                    user_info['gender'].capitalize(),
                    user_info['weight'],
                    user_info['height'],
                    user_info['goal'].replace('_', ' ').title(),
                    user_info['activity_level'].replace('_', ' ').title()
                ]
            })
            user_df.to_excel(writer, sheet_name='User Profile', index=False)
            
            # Nutritional Requirements
            req_df = pd.DataFrame({
                'Metric': ['BMR (calories/day)', 'TDEE (calories/day)', 'Target Calories', 
                          'Target Protein (g)', 'Target Fat (g)', 'Target Carbs (g)'],
                'Value': [
                    self.nutrition_analysis['bmr'],
                    self.nutrition_analysis['tdee'],
                    self.nutrition_analysis['target_calories'],
                    self.nutrition_analysis['macros']['protein'],
                    self.nutrition_analysis['macros']['fat'],
                    self.nutrition_analysis['macros']['carbs']
                ]
            })
            req_df.to_excel(writer, sheet_name='Nutritional Requirements', index=False)
            
            # Meal Plan
            meals_data = []
            for meal in self.meal_plan['meals']:
                meals_data.append({
                    'Meal': meal['dish_name'],
                    'Weight (g)': meal['weight'],
                    'Calories': meal['calories'],
                    'Protein (g)': meal['protein'],
                    'Fat (g)': meal['fat'],
                    'Carbs (g)': meal['carbs'],
                    'Ingredients': ', '.join(meal['ingredients']),
                    'Tags': ', '.join(meal['tags'])
                })
            
            # Add totals row
            totals = self.meal_plan['total_nutrition']
            meals_data.append({
                'Meal': 'TOTAL',
                'Weight (g)': sum(m['weight'] for m in self.meal_plan['meals']),
                'Calories': totals['calories'],
                'Protein (g)': totals['protein'],
                'Fat (g)': totals['fat'],
                'Carbs (g)': totals['carbs'],
                'Ingredients': '',
                'Tags': ''
            })
            
            meals_df = pd.DataFrame(meals_data)
            meals_df.to_excel(writer, sheet_name='Meal Plan', index=False)
            
            # Accuracy Analysis
            accuracy = self.meal_plan['accuracy']
            accuracy_df = pd.DataFrame({
                'Nutrient': ['Calories', 'Protein (g)', 'Fat (g)', 'Carbs (g)'],
                'Target': [
                    self.meal_plan['target_nutrition']['calories'],
                    self.meal_plan['target_nutrition']['protein'],
                    self.meal_plan['target_nutrition']['fat'],
                    self.meal_plan['target_nutrition']['carbs']
                ],
                'Actual': [
                    totals['calories'],
                    totals['protein'],
                    totals['fat'],
                    totals['carbs']
                ],
                'Difference': [
                    accuracy['calories_diff'],
                    accuracy['protein_diff'],
                    accuracy['fat_diff'],
                    accuracy['carbs_diff']
                ]
            })
            accuracy_df.to_excel(writer, sheet_name='Accuracy Analysis', index=False)
        
        return output_path
