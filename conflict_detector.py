"""
Conflict detection algorithms for schedule overlap detection.
"""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from intervaltree import IntervalTree
from abc import ABC, abstractmethod


class ConflictDetector(ABC):
    """Abstract base class for conflict detectors."""
    
    @abstractmethod
    def detect_conflicts(self, schedules: List[Dict]) -> List[Dict]:
        """
        Detect conflicts in schedules.
        
        Args:
            schedules: List of schedule dictionaries
            
        Returns:
            List of conflict dictionaries
        """
        pass
    
    @staticmethod
    def calculate_overlap(start1: datetime, end1: datetime, 
                         start2: datetime, end2: datetime) -> Tuple[datetime, datetime, float]:
        """
        Calculate overlap between two time intervals.
        
        Args:
            start1, end1: First time interval
            start2, end2: Second time interval
            
        Returns:
            Tuple of (overlap_start, overlap_end, duration_minutes)
        """
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        if overlap_start < overlap_end:
            duration = (overlap_end - overlap_start).total_seconds() / 60
            return overlap_start, overlap_end, duration
        
        return None, None, 0.0
    
    @staticmethod
    def determine_conflict_type(start1: datetime, end1: datetime,
                               start2: datetime, end2: datetime) -> str:
        """
        Determine the type of conflict between two intervals.
        
        Returns:
            'full_overlap', 'partial_overlap', or 'containment'
        """
        # Check if one contains the other
        if start1 <= start2 and end1 >= end2:
            return 'containment'
        if start2 <= start1 and end2 >= end1:
            return 'containment'
        
        # Check if they are exactly the same
        if start1 == start2 and end1 == end2:
            return 'full_overlap'
        
        # Otherwise it's partial overlap
        return 'partial_overlap'
    
    @staticmethod
    def calculate_severity(duration_minutes: float) -> str:
        """
        Calculate severity rating based on conflict duration.
        
        Args:
            duration_minutes: Duration of conflict in minutes
            
        Returns:
            'Low', 'Medium', or 'High'
        """
        if duration_minutes < 15:
            return 'Low'
        elif duration_minutes < 60:
            return 'Medium'
        else:
            return 'High'
    
    def create_conflict_entry(self, schedule1: Dict, schedule2: Dict, 
                            conflict_id: int) -> Dict:
        """
        Create a conflict entry from two overlapping schedules.
        
        Args:
            schedule1, schedule2: The two conflicting schedules
            conflict_id: Unique identifier for this conflict
            
        Returns:
            Dictionary containing conflict information
        """
        overlap_start, overlap_end, duration = self.calculate_overlap(
            schedule1['start_time'], schedule1['end_time'],
            schedule2['start_time'], schedule2['end_time']
        )
        
        conflict_type = self.determine_conflict_type(
            schedule1['start_time'], schedule1['end_time'],
            schedule2['start_time'], schedule2['end_time']
        )
        
        severity = self.calculate_severity(duration)
        
        return {
            'conflict_id': conflict_id,
            'person_id': schedule1['person_id'],
            'activity_1': schedule1['activity_name'],
            'activity_2': schedule2['activity_name'],
            'location_1': schedule1['location'],
            'location_2': schedule2['location'],
            'start_time_1': schedule1['start_time'],
            'end_time_1': schedule1['end_time'],
            'start_time_2': schedule2['start_time'],
            'end_time_2': schedule2['end_time'],
            'overlap_start': overlap_start,
            'overlap_end': overlap_end,
            'overlap_duration_minutes': duration,
            'conflict_type': conflict_type,
            'severity': severity
        }


class BruteForceDetector(ConflictDetector):
    """
    Brute force conflict detection algorithm.
    Time complexity: O(n²)
    
    Compares every pair of schedules to find conflicts.
    """
    
    def detect_conflicts(self, schedules: List[Dict]) -> List[Dict]:
        """Detect conflicts using brute force approach."""
        conflicts = []
        conflict_id = 1
        
        # Group schedules by person
        person_schedules = {}
        for schedule in schedules:
            person_id = schedule['person_id']
            if person_id not in person_schedules:
                person_schedules[person_id] = []
            person_schedules[person_id].append(schedule)
        
        # Check each person's schedules
        for person_id, person_schedule_list in person_schedules.items():
            n = len(person_schedule_list)
            
            # Compare all pairs
            for i in range(n):
                for j in range(i + 1, n):
                    schedule1 = person_schedule_list[i]
                    schedule2 = person_schedule_list[j]
                    
                    # Check if schedules overlap
                    if (schedule1['start_time'] < schedule2['end_time'] and
                        schedule2['start_time'] < schedule1['end_time']):
                        
                        conflict = self.create_conflict_entry(
                            schedule1, schedule2, conflict_id
                        )
                        conflicts.append(conflict)
                        conflict_id += 1
        
        return conflicts


class SweepLineDetector(ConflictDetector):
    """
    Sweep line conflict detection algorithm.
    Time complexity: O(n log n)
    
    Sorts events by time and uses a sweep line approach to detect overlaps.
    """
    
    def detect_conflicts(self, schedules: List[Dict]) -> List[Dict]:
        """Detect conflicts using sweep line algorithm."""
        conflicts = []
        conflict_id = 1
        
        # Group schedules by person
        person_schedules = {}
        for schedule in schedules:
            person_id = schedule['person_id']
            if person_id not in person_schedules:
                person_schedules[person_id] = []
            person_schedules[person_id].append(schedule)
        
        # Process each person's schedules
        for person_id, person_schedule_list in person_schedules.items():
            # Create events for sweep line
            events = []
            for schedule in person_schedule_list:
                events.append(('start', schedule['start_time'], schedule))
                events.append(('end', schedule['end_time'], schedule))
            
            # Sort events by time, with 'end' events before 'start' events at same time
            events.sort(key=lambda x: (x[1], x[0] == 'start'))
            
            # Track active schedules
            active = []
            
            for event_type, time, schedule in events:
                if event_type == 'start':
                    # Check for conflicts with all active schedules
                    for active_schedule in active:
                        conflict = self.create_conflict_entry(
                            active_schedule, schedule, conflict_id
                        )
                        conflicts.append(conflict)
                        conflict_id += 1
                    
                    # Add to active schedules
                    active.append(schedule)
                else:
                    # Remove from active schedules
                    active.remove(schedule)
        
        return conflicts


class IntervalTreeDetector(ConflictDetector):
    """
    Interval tree conflict detection algorithm.
    Time complexity: O(n log n)
    
    Uses an interval tree data structure for efficient conflict detection.
    """
    
    def detect_conflicts(self, schedules: List[Dict]) -> List[Dict]:
        """Detect conflicts using interval tree."""
        conflicts = []
        conflict_id = 1
        
        # Group schedules by person
        person_schedules = {}
        for schedule in schedules:
            person_id = schedule['person_id']
            if person_id not in person_schedules:
                person_schedules[person_id] = []
            person_schedules[person_id].append(schedule)
        
        # Process each person's schedules
        for person_id, person_schedule_list in person_schedules.items():
            tree = IntervalTree()
            
            for schedule in person_schedule_list:
                # Convert datetime to timestamp for interval tree
                start = schedule['start_time'].timestamp()
                end = schedule['end_time'].timestamp()
                
                # Query for overlaps
                overlaps = tree[start:end]
                
                # Create conflict entries for all overlaps
                for interval in overlaps:
                    overlapping_schedule = interval.data
                    conflict = self.create_conflict_entry(
                        overlapping_schedule, schedule, conflict_id
                    )
                    conflicts.append(conflict)
                    conflict_id += 1
                
                # Add current schedule to tree
                tree[start:end] = schedule
        
        return conflicts
