"""
Visualization module for generating charts and graphs.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
from collections import defaultdict


def create_gantt_chart(schedules: List[Dict], conflicts: List[Dict], 
                       output_path: Path, filter_person: Optional[str] = None):
    """
    Create a Gantt chart visualizing activities and conflicts.
    
    Args:
        schedules: List of schedule dictionaries
        conflicts: List of conflict dictionaries
        output_path: Path to save the chart
        filter_person: Optional person ID to filter by
    """
    # Filter schedules if needed
    if filter_person:
        schedules = [s for s in schedules if s['person_id'] == filter_person]
        conflicts = [c for c in conflicts if c['person_id'] == filter_person]
    
    # Group schedules by person
    person_schedules = defaultdict(list)
    for schedule in schedules:
        person_schedules[schedule['person_id']].append(schedule)
    
    # Limit to first 5 people for readability with large datasets
    persons = sorted(person_schedules.keys())[:5]
    
    if not persons:
        # Create empty chart
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.text(0.5, 0.5, 'No data to display', ha='center', va='center')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return
    
    # Create figure - limit size to prevent overflow
    fig_height = min(20, max(8, len(persons) * 0.8))
    fig, ax = plt.subplots(figsize=(16, fig_height))
    
    # Create conflict lookup for highlighting
    conflict_times = defaultdict(list)
    for conflict in conflicts:
        if conflict['person_id'] in persons:
            conflict_times[conflict['person_id']].append({
                'start': conflict['overlap_start'],
                'end': conflict['overlap_end']
            })
    
    # Plot schedules
    y_pos = 0
    y_labels = []
    
    for person_id in persons:
        person_schedule_list = person_schedules[person_id]
        
        for schedule in person_schedule_list:
            start = mdates.date2num(schedule['start_time'])
            end = mdates.date2num(schedule['end_time'])
            duration = end - start
            
            # Check if this schedule is involved in a conflict
            is_conflict = any(
                schedule['start_time'] < ct['end'] and 
                schedule['end_time'] > ct['start']
                for ct in conflict_times[person_id]
            )
            
            color = 'red' if is_conflict else 'skyblue'
            alpha = 0.8 if is_conflict else 0.6
            
            # Draw rectangle
            rect = Rectangle((start, y_pos - 0.4), duration, 0.8,
                           facecolor=color, edgecolor='black', alpha=alpha)
            ax.add_patch(rect)
            
            # Add activity name
            mid_x = start + duration / 2
            ax.text(mid_x, y_pos, schedule['activity_name'][:15],
                   ha='center', va='center', fontsize=7, weight='bold')
        
        y_labels.append(person_id)
        y_pos += 1
    
    # Format axes
    ax.set_ylim(-0.5, len(persons) - 0.5)
    ax.set_yticks(range(len(persons)))
    ax.set_yticklabels(y_labels)
    
    # Format x-axis as dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d\n%H:%M'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    ax.set_xlabel('Date and Time', fontsize=12, weight='bold')
    ax.set_ylabel('Person ID', fontsize=12, weight='bold')
    ax.set_title('Schedule Gantt Chart (Red = Conflicts)', fontsize=14, weight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    
    try:
        plt.tight_layout()
    except Exception:
        pass  # Ignore tight layout warnings
    plt.savefig(output_path, dpi=100)
    plt.close()


def create_conflict_heatmap(schedules: List[Dict], conflicts: List[Dict],
                            output_path: Path):
    """
    Create a heatmap showing conflict frequency by time and person.
    
    Args:
        schedules: List of schedule dictionaries
        conflicts: List of conflict dictionaries
        output_path: Path to save the chart
    """
    if not conflicts:
        # Create empty chart
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, 'No conflicts to display', ha='center', va='center')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return
    
    # Count conflicts by person and hour
    person_hour_conflicts = defaultdict(lambda: defaultdict(int))
    
    for conflict in conflicts:
        person_id = conflict['person_id']
        hour = conflict['overlap_start'].hour
        person_hour_conflicts[person_id][hour] += 1
    
    # Prepare data for heatmap
    persons = sorted(person_hour_conflicts.keys())[:20]  # Limit to 20 persons
    hours = range(24)
    
    if not persons:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, 'No conflict data available', ha='center', va='center')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return
    
    data = np.zeros((len(persons), 24))
    
    for i, person_id in enumerate(persons):
        for hour in hours:
            data[i, hour] = person_hour_conflicts[person_id][hour]
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(14, max(8, len(persons) * 0.4)))
    
    im = ax.imshow(data, cmap='YlOrRd', aspect='auto')
    
    # Set ticks
    ax.set_xticks(range(24))
    ax.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45, ha='right')
    ax.set_yticks(range(len(persons)))
    ax.set_yticklabels(persons)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Number of Conflicts', rotation=270, labelpad=20, weight='bold')
    
    # Labels and title
    ax.set_xlabel('Hour of Day', fontsize=12, weight='bold')
    ax.set_ylabel('Person ID', fontsize=12, weight='bold')
    ax.set_title('Conflict Frequency Heatmap', fontsize=14, weight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    plt.close()


def create_performance_chart(results: Dict[str, Dict], output_path: Path):
    """
    Create a chart comparing algorithm performance.
    
    Args:
        results: Dictionary of algorithm results
        output_path: Path to save the chart
    """
    algorithms = list(results.keys())
    exec_times = [results[alg]['execution_time_ms'] for alg in algorithms]
    memory_usage = [results[alg]['memory_usage_mb'] for alg in algorithms]
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Execution time comparison
    bars1 = ax1.bar(algorithms, exec_times, color=['#3498db', '#2ecc71', '#e74c3c'])
    ax1.set_ylabel('Execution Time (ms)', fontsize=12, weight='bold')
    ax1.set_title('Algorithm Execution Time', fontsize=14, weight='bold')
    ax1.tick_params(axis='x', rotation=15)
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}ms',
                ha='center', va='bottom', fontsize=10)
    
    # Memory usage comparison
    bars2 = ax2.bar(algorithms, memory_usage, color=['#3498db', '#2ecc71', '#e74c3c'])
    ax2.set_ylabel('Memory Usage (MB)', fontsize=12, weight='bold')
    ax2.set_title('Algorithm Memory Usage', fontsize=14, weight='bold')
    ax2.tick_params(axis='x', rotation=15)
    
    # Add value labels on bars
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}MB',
                ha='center', va='bottom', fontsize=10)
    
    # Add metrics comparison if available
    if all('metrics' in results[alg] for alg in algorithms):
        fig.suptitle('Algorithm Performance Comparison', fontsize=16, weight='bold', y=1.02)
        
        # Add text summary
        metrics_text = "Metrics Summary:\n"
        for alg in algorithms:
            metrics = results[alg]['metrics']
            metrics_text += f"{alg}: P={metrics['precision']:.3f}, R={metrics['recall']:.3f}, F1={metrics['f1_score']:.3f}\n"
        
        fig.text(0.5, -0.05, metrics_text, ha='center', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    plt.close()
