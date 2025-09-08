"""
Interval Tree conflict detection algorithm.
Time complexity: O(n log n)
"""
from typing import List
from datetime import datetime
from intervaltree import IntervalTree, Interval
from utils.data_parser import ScheduleItem
from algorithms.brute_force import ConflictResult


class IntervalTreeDetector:
    """Interval tree conflict detection algorithm."""
    
    @staticmethod
    def detect_conflicts(schedules: List[ScheduleItem]) -> List[ConflictResult]:
        """
        Detect conflicts using interval tree approach.
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
            person_conflicts = IntervalTreeDetector._detect_conflicts_for_person(person_schedule_list)
            conflicts.extend(person_conflicts)
        
        return conflicts
    
    @staticmethod
    def _detect_conflicts_for_person(schedules: List[ScheduleItem]) -> List[ConflictResult]:
        """
        Detect conflicts for a single person using interval tree algorithm.
        
        Args:
            schedules: List of ScheduleItem objects for a single person
            
        Returns:
            List of ConflictResult objects
        """
        if len(schedules) < 2:
            return []
        
        conflicts = []
        
        # Create interval tree
        tree = IntervalTree()
        
        # Convert datetime to timestamp for interval tree (requires numeric values)
        for i, schedule in enumerate(schedules):
            start_timestamp = schedule.start_time.timestamp()
            end_timestamp = schedule.end_time.timestamp()
            
            # Check for overlaps with existing intervals
            overlapping_intervals = tree[start_timestamp:end_timestamp]
            
            for interval in overlapping_intervals:
                other_schedule = schedules[interval.data]
                
                # Calculate actual overlap times
                overlap_start = max(schedule.start_time, other_schedule.start_time)
                overlap_end = min(schedule.end_time, other_schedule.end_time)
                
                if overlap_start < overlap_end:
                    conflict = ConflictResult(
                        schedule,
                        other_schedule,
                        overlap_start,
                        overlap_end
                    )
                    conflicts.append(conflict)
            
            # Add current interval to tree
            tree[start_timestamp:end_timestamp] = i
        
        return conflicts
    
    @staticmethod
    def get_algorithm_name() -> str:
        """Return the name of this algorithm."""
        return "Interval Tree"
    
    @staticmethod
    def get_time_complexity() -> str:
        """Return the time complexity of this algorithm."""
        return "O(n log n)"