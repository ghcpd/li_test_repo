"""
Report generation module for creating output files.
"""

import csv
from typing import List, Dict
from pathlib import Path
from metrics import validate_conflicts


def generate_conflict_report(conflicts: List[Dict], output_path: Path):
    """
    Generate a CSV report of detected conflicts.
    
    Args:
        conflicts: List of conflict dictionaries
        output_path: Path to output CSV file
    """
    if not conflicts:
        # Create empty file with headers
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Conflict ID', 'Person ID', 'Activity 1', 'Activity 2',
                'Location 1', 'Location 2',
                'Start Time 1', 'End Time 1', 'Start Time 2', 'End Time 2',
                'Overlap Start', 'Overlap End', 'Overlap Duration (minutes)',
                'Conflict Type', 'Severity'
            ])
        return
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'Conflict ID', 'Person ID', 'Activity 1', 'Activity 2',
            'Location 1', 'Location 2',
            'Start Time 1', 'End Time 1', 'Start Time 2', 'End Time 2',
            'Overlap Start', 'Overlap End', 'Overlap Duration (minutes)',
            'Conflict Type', 'Severity'
        ]
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for conflict in conflicts:
            writer.writerow({
                'Conflict ID': conflict['conflict_id'],
                'Person ID': conflict['person_id'],
                'Activity 1': conflict['activity_1'],
                'Activity 2': conflict['activity_2'],
                'Location 1': conflict['location_1'],
                'Location 2': conflict['location_2'],
                'Start Time 1': conflict['start_time_1'].strftime('%Y-%m-%d %H:%M'),
                'End Time 1': conflict['end_time_1'].strftime('%Y-%m-%d %H:%M'),
                'Start Time 2': conflict['start_time_2'].strftime('%Y-%m-%d %H:%M'),
                'End Time 2': conflict['end_time_2'].strftime('%Y-%m-%d %H:%M'),
                'Overlap Start': conflict['overlap_start'].strftime('%Y-%m-%d %H:%M'),
                'Overlap End': conflict['overlap_end'].strftime('%Y-%m-%d %H:%M'),
                'Overlap Duration (minutes)': f"{conflict['overlap_duration_minutes']:.2f}",
                'Conflict Type': conflict['conflict_type'],
                'Severity': conflict['severity']
            })


def generate_performance_report(results: Dict[str, Dict], output_path: Path):
    """
    Generate a CSV report comparing algorithm performance.
    
    Args:
        results: Dictionary of algorithm results
        output_path: Path to output CSV file
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'Algorithm', 'Conflicts Detected', 'Execution Time (ms)', 
            'Memory Usage (MB)', 'Precision', 'Recall', 'F1 Score'
        ]
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for name, result in results.items():
            row = {
                'Algorithm': name,
                'Conflicts Detected': result['num_conflicts'],
                'Execution Time (ms)': f"{result['execution_time_ms']:.2f}",
                'Memory Usage (MB)': f"{result['memory_usage_mb']:.2f}",
            }
            
            if 'metrics' in result:
                metrics = result['metrics']
                row['Precision'] = f"{metrics['precision']:.4f}"
                row['Recall'] = f"{metrics['recall']:.4f}"
                row['F1 Score'] = f"{metrics['f1_score']:.4f}"
            else:
                row['Precision'] = 'N/A'
                row['Recall'] = 'N/A'
                row['F1 Score'] = 'N/A'
            
            writer.writerow(row)


def generate_validation_report(detected_conflicts: List[Dict],
                               known_conflicts: List[Dict],
                               output_path: Path):
    """
    Generate a detailed validation report showing correctness per conflict.
    
    Args:
        detected_conflicts: List of detected conflicts
        known_conflicts: List of known conflicts
        output_path: Path to output CSV file
    """
    validation = validate_conflicts(detected_conflicts, known_conflicts)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'Status', 'Person ID', 'Time Range 1', 'Time Range 2',
            'Activity 1', 'Activity 2', 'Notes'
        ]
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write true positives
        for entry in validation['true_positives']:
            detected = entry['detected']
            writer.writerow({
                'Status': 'TRUE POSITIVE',
                'Person ID': detected['person_id'],
                'Time Range 1': f"{detected['start_time_1'].strftime('%Y-%m-%d %H:%M')} - {detected['end_time_1'].strftime('%H:%M')}",
                'Time Range 2': f"{detected['start_time_2'].strftime('%Y-%m-%d %H:%M')} - {detected['end_time_2'].strftime('%H:%M')}",
                'Activity 1': detected['activity_1'],
                'Activity 2': detected['activity_2'],
                'Notes': 'Correctly detected conflict'
            })
        
        # Write false positives
        for entry in validation['false_positives']:
            detected = entry['detected']
            writer.writerow({
                'Status': 'FALSE POSITIVE',
                'Person ID': detected['person_id'],
                'Time Range 1': f"{detected['start_time_1'].strftime('%Y-%m-%d %H:%M')} - {detected['end_time_1'].strftime('%H:%M')}",
                'Time Range 2': f"{detected['start_time_2'].strftime('%Y-%m-%d %H:%M')} - {detected['end_time_2'].strftime('%H:%M')}",
                'Activity 1': detected['activity_1'],
                'Activity 2': detected['activity_2'],
                'Notes': 'Detected but not in known conflicts'
            })
        
        # Write false negatives
        for entry in validation['false_negatives']:
            known = entry['known']
            writer.writerow({
                'Status': 'FALSE NEGATIVE',
                'Person ID': known['person_id'],
                'Time Range 1': f"{known['original_start'].strftime('%Y-%m-%d %H:%M')} - {known['original_end'].strftime('%H:%M')}",
                'Time Range 2': f"{known['conflict_start'].strftime('%Y-%m-%d %H:%M')} - {known['conflict_end'].strftime('%H:%M')}",
                'Activity 1': known['activity_1'],
                'Activity 2': known['activity_2'],
                'Notes': 'Missed by detector'
            })
