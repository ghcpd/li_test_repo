"""
Data loading and validation module for schedule conflict detection system.
"""

import csv
import json
from datetime import datetime
from typing import List, Dict


def load_schedules(filepath: str) -> List[Dict]:
    """
    Load schedules from CSV file.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        List of schedule dictionaries
        
    Raises:
        ValueError: If the CSV format is invalid
        FileNotFoundError: If the file doesn't exist
    """
    schedules = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Validate headers
        required_fields = ['person_id', 'start_time', 'end_time', 'activity_name', 'location']
        if not all(field in reader.fieldnames for field in required_fields):
            raise ValueError(f"CSV must contain fields: {', '.join(required_fields)}")
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
            try:
                # Parse datetime strings
                start_time = datetime.strptime(row['start_time'].strip(), '%Y-%m-%d %H:%M')
                end_time = datetime.strptime(row['end_time'].strip(), '%Y-%m-%d %H:%M')
                
                # Validate time order
                if start_time >= end_time:
                    raise ValueError(f"Start time must be before end time")
                
                schedule = {
                    'person_id': row['person_id'].strip(),
                    'start_time': start_time,
                    'end_time': end_time,
                    'activity_name': row['activity_name'].strip(),
                    'location': row['location'].strip(),
                    'row_number': row_num  # For debugging
                }
                
                # Include scenario if present
                if 'scenario' in row:
                    schedule['scenario'] = row['scenario'].strip()
                
                schedules.append(schedule)
                
            except ValueError as e:
                raise ValueError(f"Error parsing row {row_num}: {e}")
            except KeyError as e:
                raise ValueError(f"Missing required field in row {row_num}: {e}")
    
    return schedules


def load_known_conflicts(filepath: str) -> List[Dict]:
    """
    Load known conflicts from JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        List of known conflict dictionaries
        
    Raises:
        ValueError: If the JSON format is invalid
        FileNotFoundError: If the file doesn't exist
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        conflicts = json.load(f)
    
    # Validate and normalize conflict entries
    normalized_conflicts = []
    
    for i, conflict in enumerate(conflicts):
        try:
            # Parse time ranges
            original_start, original_end = conflict['original_schedule'].split(' - ')
            conflict_start, conflict_end = conflict['conflict_schedule'].split(' - ')
            
            normalized = {
                'person_id': conflict['person_id'],
                'original_start': datetime.strptime(original_start.strip(), '%Y-%m-%d %H:%M'),
                'original_end': datetime.strptime(original_end.strip(), '%Y-%m-%d %H:%M'),
                'conflict_start': datetime.strptime(conflict_start.strip(), '%Y-%m-%d %H:%M'),
                'conflict_end': datetime.strptime(conflict_end.strip(), '%Y-%m-%d %H:%M'),
                'activity_1': conflict['activity_1'],
                'activity_2': conflict['activity_2']
            }
            
            normalized_conflicts.append(normalized)
            
        except (KeyError, ValueError) as e:
            raise ValueError(f"Error parsing conflict {i}: {e}")
    
    return normalized_conflicts
