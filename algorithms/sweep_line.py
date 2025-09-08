"""
Sweep Line conflict detection algorithm.
Time complexity: O(n log n)
"""
from typing import List, Tuple
from datetime import datetime
from utils.data_parser import ScheduleItem
from algorithms.brute_force import ConflictResult


class Event:
    """Represents a start or end event for the sweep line algorithm."""
    
    def __init__(self, time: datetime, event_type: str, schedule_item: ScheduleItem):
        self.time = time
        self.event_type = event_type  # 'start' or 'end'
        self.schedule_item = schedule_item
    
    def __lt__(self, other):
        """Sort events by time, with 'end' events before 'start' events at the same time."""
        if self.time != other.time:
            return self.time < other.time
        # If times are equal, process 'end' events before 'start' events
        return self.event_type == 'end' and other.event_type == 'start'
    
    def __repr__(self):
        return f"Event({self.time}, {self.event_type}, {self.schedule_item.person_id})"


class SweepLineDetector:
    """Sweep line conflict detection algorithm."""
    
    @staticmethod
    def detect_conflicts(schedules: List[ScheduleItem]) -> List[ConflictResult]:
        """
        Detect conflicts using sweep line approach.
        Time complexity: O(n log n)
        
        Args:
            schedules: List of ScheduleItem objects
            
        Returns:
            List of ConflictResult objects representing detected conflicts
        """
        if not schedules:
            return []
        
        conflicts = []
        
        # Group schedules by person to process each person separately
        person_schedules = {}
        for schedule in schedules:
            if schedule.person_id not in person_schedules:
                person_schedules[schedule.person_id] = []
            person_schedules[schedule.person_id].append(schedule)
        
        # Process each person's schedules separately
        for person_id, person_schedule_list in person_schedules.items():
            person_conflicts = SweepLineDetector._detect_conflicts_for_person(person_schedule_list)
            conflicts.extend(person_conflicts)
        
        return conflicts
    
    @staticmethod
    def _detect_conflicts_for_person(schedules: List[ScheduleItem]) -> List[ConflictResult]:
        """
        Detect conflicts for a single person using sweep line algorithm.
        
        Args:
            schedules: List of ScheduleItem objects for a single person
            
        Returns:
            List of ConflictResult objects
        """
        if len(schedules) < 2:
            return []
        
        conflicts = []
        events = []
        
        # Create start and end events for each schedule
        for schedule in schedules:
            events.append(Event(schedule.start_time, 'start', schedule))
            events.append(Event(schedule.end_time, 'end', schedule))
        
        # Sort events by time
        events.sort()
        
        # Track active schedules
        active_schedules = []
        
        # Process events
        for event in events:
            if event.event_type == 'start':
                # Check for conflicts with all currently active schedules
                for active_schedule in active_schedules:
                    # Calculate overlap
                    overlap_start = max(active_schedule.start_time, event.schedule_item.start_time)
                    overlap_end = min(active_schedule.end_time, event.schedule_item.end_time)
                    
                    if overlap_start < overlap_end:
                        conflict = ConflictResult(
                            active_schedule, 
                            event.schedule_item, 
                            overlap_start, 
                            overlap_end
                        )
                        conflicts.append(conflict)
                
                # Add this schedule to active list
                active_schedules.append(event.schedule_item)
            
            else:  # event.event_type == 'end'
                # Remove this schedule from active list
                active_schedules = [s for s in active_schedules if s != event.schedule_item]
        
        return conflicts
    
    @staticmethod
    def get_algorithm_name() -> str:
        """Return the name of this algorithm."""
        return "Sweep Line"
    
    @staticmethod
    def get_time_complexity() -> str:
        """Return the time complexity of this algorithm."""
        return "O(n log n)"