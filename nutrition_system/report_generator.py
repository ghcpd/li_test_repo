"""
Report generation with visualizations and export functionality.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import Dict, List
from pathlib import Path
import io
import base64

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from .models import MealPlan, UserProfile, NutritionRequirements


class ReportGenerator:
    """Generate nutrition analysis reports with visualizations."""
    
    def __init__(self):
        # Set up matplotlib style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def generate_macro_pie_chart(self, meal_plan: MealPlan, save_path: str = None) -> str:
        """Generate pie chart showing macronutrient distribution."""
        macros = meal_plan.get_macro_percentages()
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        labels = ['Protein', 'Fat', 'Carbohydrates']
        sizes = [macros['protein'], macros['fat'], macros['carbs']]
        colors = ['#ff9999', '#66b3ff', '#99ff99']
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                         autopct='%1.1f%%', startangle=90)
        
        ax.set_title('Daily Macronutrient Distribution', fontsize=16, fontweight='bold')
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        # Return base64 encoded image for embedding
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return img_base64
    
    def generate_meal_nutrition_chart(self, meal_plan: MealPlan, save_path: str = None) -> str:
        """Generate bar chart showing nutrition by meal."""
        meal_data = []
        
        for meal in meal_plan.meals:
            meal_data.append({
                'Meal': meal.meal_name,
                'Calories': meal.total_calories,
                'Protein (g)': meal.total_protein,
                'Fat (g)': meal.total_fat,
                'Carbs (g)': meal.total_carbs
            })
        
        df = pd.DataFrame(meal_data)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Calories
        ax1.bar(df['Meal'], df['Calories'], color='skyblue')
        ax1.set_title('Calories by Meal', fontweight='bold')
        ax1.set_ylabel('Calories')
        ax1.tick_params(axis='x', rotation=45)
        
        # Protein
        ax2.bar(df['Meal'], df['Protein (g)'], color='lightcoral')
        ax2.set_title('Protein by Meal', fontweight='bold')
        ax2.set_ylabel('Protein (g)')
        ax2.tick_params(axis='x', rotation=45)
        
        # Fat
        ax3.bar(df['Meal'], df['Fat (g)'], color='lightgreen')
        ax3.set_title('Fat by Meal', fontweight='bold')
        ax3.set_ylabel('Fat (g)')
        ax3.tick_params(axis='x', rotation=45)
        
        # Carbs
        ax4.bar(df['Meal'], df['Carbs (g)'], color='gold')
        ax4.set_title('Carbohydrates by Meal', fontweight='bold')
        ax4.set_ylabel('Carbohydrates (g)')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        # Return base64 encoded image
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return img_base64
    
    def generate_nutrition_summary_table(self, meal_plan: MealPlan) -> pd.DataFrame:
        """Generate summary table of nutritional information."""
        summary = meal_plan.get_nutrition_summary()
        requirements = meal_plan.user_requirements
        
        data = {
            'Nutrient': ['Calories', 'Protein (g)', 'Fat (g)', 'Carbohydrates (g)'],
            'Target': [requirements.calories, requirements.protein, 
                      requirements.fat, requirements.carbs],
            'Actual': [summary['calories'], summary['protein'], 
                      summary['fat'], summary['carbs']],
            'Difference': [
                summary['calories'] - requirements.calories,
                summary['protein'] - requirements.protein,
                summary['fat'] - requirements.fat,
                summary['carbs'] - requirements.carbs
            ]
        }
        
        df = pd.DataFrame(data)
        df['% of Target'] = (df['Actual'] / df['Target'] * 100).round(1)
        
        return df
    
    def export_to_excel(self, meal_plan: MealPlan, user: UserProfile, filename: str):
        """Export meal plan to Excel format."""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # User profile sheet
            user_data = {
                'Parameter': ['Age', 'Gender', 'Weight (kg)', 'Height (cm)', 'Goal', 'Activity Level'],
                'Value': [user.age, user.gender.value, user.weight, user.height, 
                         user.goal.value, user.activity_level.name]
            }
            pd.DataFrame(user_data).to_excel(writer, sheet_name='User Profile', index=False)
            
            # Nutrition summary sheet
            summary_df = self.generate_nutrition_summary_table(meal_plan)
            summary_df.to_excel(writer, sheet_name='Nutrition Summary', index=False)
            
            # Meal details sheet
            meal_details = []
            for meal in meal_plan.meals:
                for dish in meal.dishes:
                    meal_details.append({
                        'Meal': meal.meal_name,
                        'Dish': dish.dish_name,
                        'Weight (g)': dish.weight,
                        'Calories': dish.calories,
                        'Protein (g)': dish.protein,
                        'Fat (g)': dish.fat,
                        'Carbs (g)': dish.carbs,
                        'Tags': ', '.join(dish.tags)
                    })
            
            pd.DataFrame(meal_details).to_excel(writer, sheet_name='Meal Details', index=False)
    
    def export_to_pdf(self, meal_plan: MealPlan, user: UserProfile, filename: str):
        """Export meal plan to PDF format."""
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph("Personalized Nutrition Plan", title_style))
        story.append(Spacer(1, 20))
        
        # User information
        story.append(Paragraph("User Profile", styles['Heading2']))
        user_info = [
            ['Parameter', 'Value'],
            ['Age', str(user.age)],
            ['Gender', user.gender.value.title()],
            ['Weight', f"{user.weight} kg"],
            ['Height', f"{user.height} cm"],
            ['Goal', user.goal.value.replace('_', ' ').title()],
            ['Activity Level', user.activity_level.name.replace('_', ' ').title()]
        ]
        
        user_table = Table(user_info)
        user_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(user_table)
        story.append(Spacer(1, 20))
        
        # Nutrition summary
        story.append(Paragraph("Nutrition Summary", styles['Heading2']))
        summary_df = self.generate_nutrition_summary_table(meal_plan)
        summary_data = [summary_df.columns.tolist()] + summary_df.values.tolist()
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Meal plan details
        story.append(Paragraph("Daily Meal Plan", styles['Heading2']))
        
        for meal in meal_plan.meals:
            story.append(Paragraph(f"{meal.meal_name}", styles['Heading3']))
            
            meal_data = [['Dish', 'Calories', 'Protein (g)', 'Fat (g)', 'Carbs (g)']]
            for dish in meal.dishes:
                meal_data.append([
                    dish.dish_name,
                    str(round(dish.calories, 1)),
                    str(round(dish.protein, 1)),
                    str(round(dish.fat, 1)),
                    str(round(dish.carbs, 1))
                ])
            
            # Add meal totals
            meal_data.append([
                'TOTAL',
                str(round(meal.total_calories, 1)),
                str(round(meal.total_protein, 1)),
                str(round(meal.total_fat, 1)),
                str(round(meal.total_carbs, 1))
            ])
            
            meal_table = Table(meal_data)
            meal_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(meal_table)
            story.append(Spacer(1, 12))
        
        doc.build(story)
    
    def generate_complete_report(self, meal_plan: MealPlan, user: UserProfile, 
                               output_dir: str = "reports") -> Dict[str, str]:
        """Generate complete nutrition report with all visualizations."""
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
        # Generate visualizations
        pie_chart = self.generate_macro_pie_chart(meal_plan, 
                                                 f"{output_dir}/macro_distribution.png")
        meal_chart = self.generate_meal_nutrition_chart(meal_plan, 
                                                       f"{output_dir}/meal_nutrition.png")
        
        # Generate exports
        excel_file = f"{output_dir}/nutrition_plan.xlsx"
        pdf_file = f"{output_dir}/nutrition_plan.pdf"
        
        self.export_to_excel(meal_plan, user, excel_file)
        self.export_to_pdf(meal_plan, user, pdf_file)
        
        return {
            'pie_chart': pie_chart,
            'meal_chart': meal_chart,
            'excel_file': excel_file,
            'pdf_file': pdf_file,
            'summary_table': self.generate_nutrition_summary_table(meal_plan)
        }