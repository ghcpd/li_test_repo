"""
Visualization utilities for schedule conflict detection system.
"""
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless environments
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os
from utils.data_parser import ScheduleItem
from algorithms.brute_force import ConflictResult
from utils.reporter import PerformanceStats


class Visualizer:
    """Creates various visualizations for the conflict detection system."""
    
    def __init__(self, output_dir: str = "report"):
        """
        Initialize visualizer.
        
        Args:
            output_dir: Directory to save visualizations (default: "report")
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
        
        # Set matplotlib style
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
    
    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def create_gantt_chart(self, schedules: List[ScheduleItem], conflicts: List[ConflictResult],
                          max_persons: int = 10, filename: str = None) -> str:
        """
        Create a Gantt chart visualizing activities and conflicts on timelines per person.
        
        Args:
            schedules: List of schedule items
            conflicts: List of detected conflicts
            max_persons: Maximum number of persons to display (default: 10)
            filename: Optional filename (default: gantt_chart_TIMESTAMP.png)
            
        Returns:
            Path to generated chart file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gantt_chart_{timestamp}.png"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Group schedules by person
        person_schedules = {}
        for schedule in schedules:
            if schedule.person_id not in person_schedules:
                person_schedules[schedule.person_id] = []
            person_schedules[schedule.person_id].append(schedule)
        
        # Limit to max_persons for readability
        persons = sorted(list(person_schedules.keys()))[:max_persons]
        
        if not persons:
            # Create empty chart
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'No schedule data to display', 
                   ha='center', va='center', transform=ax.transAxes)
            plt.title('Schedule Gantt Chart')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return filepath
        
        # Create conflict lookup for quick access
        conflict_times = {}
        for conflict in conflicts:
            person_id = conflict.item1.person_id
            if person_id not in conflict_times:
                conflict_times[person_id] = []
            conflict_times[person_id].append((conflict.overlap_start, conflict.overlap_end))
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(15, max(8, len(persons) * 0.8)))
        
        # Color map for different activities
        activities = set()
        for person_schedules_list in person_schedules.values():
            for schedule in person_schedules_list:
                activities.add(schedule.activity_name)
        
        activity_colors = plt.cm.Set3(np.linspace(0, 1, len(activities)))
        activity_color_map = {activity: color for activity, color in zip(sorted(activities), activity_colors)}
        
        # Plot schedules for each person
        for i, person_id in enumerate(persons):
            y_position = i
            
            for schedule in person_schedules[person_id]:
                # Calculate bar position and width
                start_time = schedule.start_time
                duration = (schedule.end_time - schedule.start_time).total_seconds() / 3600  # hours
                
                # Draw activity bar
                color = activity_color_map[schedule.activity_name]
                bar = ax.barh(y_position, duration, left=start_time, height=0.6,
                            color=color, alpha=0.7, edgecolor='black', linewidth=0.5)
                
                # Add activity name text if bar is wide enough
                if duration > 0.5:  # If duration > 30 minutes
                    ax.text(start_time + timedelta(hours=duration/2), y_position,
                           schedule.activity_name[:15], ha='center', va='center', fontsize=8)
            
            # Highlight conflicts
            if person_id in conflict_times:
                for conflict_start, conflict_end in conflict_times[person_id]:
                    duration = (conflict_end - conflict_start).total_seconds() / 3600
                    ax.barh(y_position, duration, left=conflict_start, height=0.8,
                           color='red', alpha=0.3, edgecolor='red', linewidth=2)
        
        # Format the plot
        ax.set_yticks(range(len(persons)))
        ax.set_yticklabels(persons)
        ax.set_ylabel('Person ID')
        ax.set_xlabel('Time')
        ax.set_title('Schedule Gantt Chart with Conflicts (Red = Conflicts)')
        
        # Format x-axis to show dates/times nicely
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        plt.xticks(rotation=45)
        
        # Add legend for activities
        legend_elements = [plt.Rectangle((0,0),1,1, facecolor=activity_color_map[activity], 
                                       alpha=0.7, label=activity) for activity in sorted(activities)[:10]]
        if len(legend_elements) > 0:
            ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def create_conflict_heatmap(self, conflicts: List[ConflictResult], filename: str = None) -> str:
        """
        Create a heatmap visualizing frequency of conflicts by time and person.
        
        Args:
            conflicts: List of detected conflicts
            filename: Optional filename (default: conflict_heatmap_TIMESTAMP.png)
            
        Returns:
            Path to generated heatmap file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conflict_heatmap_{timestamp}.png"
        
        filepath = os.path.join(self.output_dir, filename)
        
        if not conflicts:
            # Create empty heatmap
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'No conflicts to display', 
                   ha='center', va='center', transform=ax.transAxes)
            plt.title('Conflict Heatmap')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return filepath
        
        # Prepare data for heatmap
        conflict_data = []
        for conflict in conflicts:
            conflict_data.append({
                'person_id': conflict.item1.person_id,
                'hour': conflict.overlap_start.hour,
                'day': conflict.overlap_start.strftime('%Y-%m-%d'),
                'duration': conflict.overlap_duration
            })
        
        df = pd.DataFrame(conflict_data)
        
        # Create pivot table for heatmap
        if len(df) > 0:
            # Option 1: Conflicts by person and hour of day
            pivot_hour = df.groupby(['person_id', 'hour']).size().unstack(fill_value=0)
            
            if len(pivot_hour) > 0:
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
                
                # Heatmap by hour of day
                im1 = ax1.imshow(pivot_hour.values, cmap='Reds', aspect='auto')
                ax1.set_xticks(range(len(pivot_hour.columns)))
                ax1.set_xticklabels([f"{hour:02d}:00" for hour in pivot_hour.columns])
                ax1.set_yticks(range(len(pivot_hour.index)))
                ax1.set_yticklabels(pivot_hour.index)
                ax1.set_xlabel('Hour of Day')
                ax1.set_ylabel('Person ID')
                ax1.set_title('Conflict Frequency by Person and Hour of Day')
                
                # Add colorbar
                cbar1 = plt.colorbar(im1, ax=ax1)
                cbar1.set_label('Number of Conflicts')
                
                # Add text annotations
                for i in range(len(pivot_hour.index)):
                    for j in range(len(pivot_hour.columns)):
                        value = pivot_hour.iloc[i, j]
                        if value > 0:
                            ax1.text(j, i, str(value), ha='center', va='center', 
                                   color='white' if value > pivot_hour.values.max()/2 else 'black')
                
                # Option 2: Conflicts by person and day
                pivot_day = df.groupby(['person_id', 'day']).size().unstack(fill_value=0)
                
                if len(pivot_day.columns) > 1:
                    im2 = ax2.imshow(pivot_day.values, cmap='Blues', aspect='auto')
                    ax2.set_xticks(range(len(pivot_day.columns)))
                    ax2.set_xticklabels([day[-5:] for day in pivot_day.columns], rotation=45)  # Show MM-DD
                    ax2.set_yticks(range(len(pivot_day.index)))
                    ax2.set_yticklabels(pivot_day.index)
                    ax2.set_xlabel('Date')
                    ax2.set_ylabel('Person ID')
                    ax2.set_title('Conflict Frequency by Person and Date')
                    
                    # Add colorbar
                    cbar2 = plt.colorbar(im2, ax=ax2)
                    cbar2.set_label('Number of Conflicts')
                    
                    # Add text annotations
                    for i in range(len(pivot_day.index)):
                        for j in range(len(pivot_day.columns)):
                            value = pivot_day.iloc[i, j]
                            if value > 0:
                                ax2.text(j, i, str(value), ha='center', va='center',
                                       color='white' if value > pivot_day.values.max()/2 else 'black')
                else:
                    ax2.text(0.5, 0.5, 'Insufficient data for daily heatmap', 
                           ha='center', va='center', transform=ax2.transAxes)
                    ax2.set_title('Conflict Frequency by Date (Insufficient Data)')
                
                plt.tight_layout()
            else:
                # Single plot if no data to pivot
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.text(0.5, 0.5, 'Insufficient data for heatmap visualization', 
                       ha='center', va='center', transform=ax.transAxes)
                plt.title('Conflict Heatmap')
        else:
            # No data
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'No conflict data available', 
                   ha='center', va='center', transform=ax.transAxes)
            plt.title('Conflict Heatmap')
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def create_performance_comparison_chart(self, performance_stats: List[PerformanceStats], 
                                          filename: str = None) -> str:
        """
        Create performance comparison chart showing execution time and memory usage.
        
        Args:
            performance_stats: List of performance statistics for each algorithm
            filename: Optional filename (default: performance_comparison_TIMESTAMP.png)
            
        Returns:
            Path to generated chart file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_comparison_{timestamp}.png"
        
        filepath = os.path.join(self.output_dir, filename)
        
        if not performance_stats:
            # Create empty chart
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'No performance data to display', 
                   ha='center', va='center', transform=ax.transAxes)
            plt.title('Performance Comparison')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return filepath
        
        # Extract data
        algorithms = [stat.algorithm_name for stat in performance_stats]
        execution_times = [stat.execution_time_ms for stat in performance_stats]
        memory_usage = [stat.memory_usage_mb for stat in performance_stats]
        conflicts_found = [stat.conflicts_found for stat in performance_stats]
        
        # Create subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Execution time comparison
        bars1 = ax1.bar(algorithms, execution_times, color=['skyblue', 'lightcoral', 'lightgreen'])
        ax1.set_ylabel('Execution Time (ms)')
        ax1.set_title('Algorithm Execution Time Comparison')
        ax1.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, value in zip(bars1, execution_times):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(execution_times)*0.01,
                    f'{value:.1f}', ha='center', va='bottom')
        
        # Memory usage comparison
        bars2 = ax2.bar(algorithms, memory_usage, color=['lightcyan', 'lightpink', 'lightgreen'])
        ax2.set_ylabel('Memory Usage (MB)')
        ax2.set_title('Algorithm Memory Usage Comparison')
        ax2.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, value in zip(bars2, memory_usage):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(memory_usage)*0.01,
                    f'{value:.1f}', ha='center', va='bottom')
        
        # Conflicts found comparison
        bars3 = ax3.bar(algorithms, conflicts_found, color=['gold', 'orange', 'yellow'])
        ax3.set_ylabel('Conflicts Found')
        ax3.set_title('Number of Conflicts Detected')
        ax3.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, value in zip(bars3, conflicts_found):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(conflicts_found)*0.01,
                    f'{value}', ha='center', va='bottom')
        
        # Combined efficiency chart (time vs memory)
        ax4.scatter(execution_times, memory_usage, s=100, alpha=0.7)
        for i, alg in enumerate(algorithms):
            ax4.annotate(alg, (execution_times[i], memory_usage[i]), 
                        xytext=(5, 5), textcoords='offset points')
        ax4.set_xlabel('Execution Time (ms)')
        ax4.set_ylabel('Memory Usage (MB)')
        ax4.set_title('Time vs Memory Usage')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath