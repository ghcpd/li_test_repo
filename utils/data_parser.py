"""
Data parsing utilities for schedule conflict detection system.
"""
import csv
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Tuple


class ScheduleItem:
    """Represents a single schedule item."""
    
    def __init__(self, person_id: str, start_time: datetime, end_time: datetime, 
                 activity_name: str, location: str, scenario: str = ""):
        self.person_id = person_id
        self.start_time = start_time
        self.end_time = end_time
        self.activity_name = activity_name
        self.location = location
        self.scenario = scenario
    
    def __repr__(self):
        return f"ScheduleItem({self.person_id}, {self.start_time}, {self.end_time}, {self.activity_name})"


class ConflictItem:
    """Represents a known conflict from ground truth data."""
    
    def __init__(self, person_id: str, original_schedule: str, conflict_schedule: str,
                 activity_1: str, activity_2: str):
        self.person_id = person_id
        self.original_schedule = original_schedule
        self.conflict_schedule = conflict_schedule
        self.activity_1 = activity_1
        self.activity_2 = activity_2
        
        # Parse time ranges
        self.original_start, self.original_end = self._parse_time_range(original_schedule)
        self.conflict_start, self.conflict_end = self._parse_time_range(conflict_schedule)
    
    def _parse_time_range(self, time_range: str) -> Tuple[datetime, datetime]:
        """Parse time range string like '2025-09-17 18:45 - 2025-09-17 19:15'"""
        start_str, end_str = time_range.split(' - ')
        start_time = datetime.strptime(start_str.strip(), '%Y-%m-%d %H:%M')
        end_time = datetime.strptime(end_str.strip(), '%Y-%m-%d %H:%M')
        return start_time, end_time
    
    def __repr__(self):
        return f"ConflictItem({self.person_id}, {self.activity_1} vs {self.activity_2})"


class DataParser:
    """Handles parsing of input CSV and known conflicts JSON files."""
    
    @staticmethod
    def parse_schedule_csv(filepath: str) -> List[ScheduleItem]:
        """Parse the schedule CSV file and return list of ScheduleItem objects."""
        schedules = []
        
        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    start_time = datetime.strptime(row['start_time'], '%Y-%m-%d %H:%M')
                    end_time = datetime.strptime(row['end_time'], '%Y-%m-%d %H:%M')
                    
                    schedule = ScheduleItem(
                        person_id=row['person_id'],
                        start_time=start_time,
                        end_time=end_time,
                        activity_name=row['activity_name'],
                        location=row['location'],
                        scenario=row.get('scenario', '')
                    )
                    schedules.append(schedule)
                except (ValueError, KeyError) as e:
                    print(f"Warning: Skipping invalid row: {row}. Error: {e}")
                    continue
        
        return schedules
    
    @staticmethod
    def parse_known_conflicts_json(filepath: str) -> List[ConflictItem]:
        """Parse the known conflicts JSON file and return list of ConflictItem objects."""
        conflicts = []
        
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
            for item in data:
                try:
                    conflict = ConflictItem(
                        person_id=item['person_id'],
                        original_schedule=item['original_schedule'],
                        conflict_schedule=item['conflict_schedule'],
                        activity_1=item['activity_1'],
                        activity_2=item['activity_2']
                    )
                    conflicts.append(conflict)
                except (ValueError, KeyError) as e:
                    print(f"Warning: Skipping invalid conflict: {item}. Error: {e}")
                    continue
        
        return conflicts
    
    @staticmethod
    def schedules_to_dataframe(schedules: List[ScheduleItem]) -> pd.DataFrame:
        """Convert list of ScheduleItem objects to pandas DataFrame."""
        data = []
        for schedule in schedules:
            data.append({
                'person_id': schedule.person_id,
                'start_time': schedule.start_time,
                'end_time': schedule.end_time,
                'activity_name': schedule.activity_name,
                'location': schedule.location,
                'scenario': schedule.scenario
            })
        return pd.DataFrame(data)