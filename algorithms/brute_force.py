"""
Brute Force conflict detection algorithm.
Time complexity: O(n²)
"""
from typing import List, Tuple
from datetime import datetime, timedelta
from utils.data_parser import ScheduleItem


class ConflictResult:
    """Represents a detected conflict between two schedule items."""
    
    def __init__(self, item1: ScheduleItem, item2: ScheduleItem, 
                 overlap_start: datetime, overlap_end: datetime):
        self.item1 = item1
        self.item2 = item2
        self.overlap_start = overlap_start
        self.overlap_end = overlap_end
        self.overlap_duration = (overlap_end - overlap_start).total_seconds() / 60  # minutes
        
        # Determine conflict type
        self.conflict_type = self._determine_conflict_type()
        
        # Determine severity
        self.severity = self._determine_severity()
    
    def _determine_conflict_type(self) -> str:
        """Determine the type of conflict based on overlap patterns."""
        item1_start, item1_end = self.item1.start_time, self.item1.end_time
        item2_start, item2_end = self.item2.start_time, self.item2.end_time
        
        # Full overlap: one activity completely overlaps the other
        if (item1_start <= item2_start and item1_end >= item2_end) or \
           (item2_start <= item1_start and item2_end >= item1_end):
            return "full overlap"
        
        # Containment: one activity is completely contained within another
        if (item1_start >= item2_start and item1_end <= item2_end) or \
           (item2_start >= item1_start and item2_end <= item1_end):
            return "containment"
        
        # Partial overlap: activities partially overlap
        return "partial overlap"
    
    def _determine_severity(self) -> str:
        """Determine severity based on overlap duration."""
        if self.overlap_duration >= 60:  # 1 hour or more
            return "High"
        elif self.overlap_duration >= 30:  # 30 minutes or more
            return "Medium"
        else:
            return "Low"
    
    def to_dict(self) -> dict:
        """Convert conflict result to dictionary for reporting."""
        return {
            'person_id': self.item1.person_id,
            'activity_1': self.item1.activity_name,
            'activity_2': self.item2.activity_name,
            'start_time_1': self.item1.start_time.strftime('%Y-%m-%d %H:%M'),
            'end_time_1': self.item1.end_time.strftime('%Y-%m-%d %H:%M'),
            'start_time_2': self.item2.start_time.strftime('%Y-%m-%d %H:%M'),
            'end_time_2': self.item2.end_time.strftime('%Y-%m-%d %H:%M'),
            'overlap_start': self.overlap_start.strftime('%Y-%m-%d %H:%M'),
            'overlap_end': self.overlap_end.strftime('%Y-%m-%d %H:%M'),
            'overlap_duration_minutes': round(self.overlap_duration, 2),
            'conflict_type': self.conflict_type,
            'severity': self.severity,
            'location_1': self.item1.location,
            'location_2': self.item2.location
        }
    
    def __repr__(self):
        return f"ConflictResult({self.item1.person_id}, {self.item1.activity_name} vs {self.item2.activity_name})"


class BruteForceDetector:
    """Brute force conflict detection algorithm."""
    
    @staticmethod
    def detect_conflicts(schedules: List[ScheduleItem]) -> List[ConflictResult]:
        """
        Detect conflicts using brute force approach.
        Time complexity: O(n²)
        
        Args:
            schedules: List of ScheduleItem objects
            
        Returns:
            List of ConflictResult objects representing detected conflicts
        """
        conflicts = []
        n = len(schedules)
        
        # Compare every pair of schedules
        for i in range(n):
            for j in range(i + 1, n):
                item1 = schedules[i]
                item2 = schedules[j]
                
                # Only check conflicts for the same person
                if item1.person_id != item2.person_id:
                    continue
                
                # Check if there's an overlap
                overlap_start = max(item1.start_time, item2.start_time)
                overlap_end = min(item1.end_time, item2.end_time)
                
                # If overlap_start < overlap_end, there's a conflict
                if overlap_start < overlap_end:
                    conflict = ConflictResult(item1, item2, overlap_start, overlap_end)
                    conflicts.append(conflict)
        
        return conflicts
    
    @staticmethod
    def get_algorithm_name() -> str:
        """Return the name of this algorithm."""
        return "Brute Force"
    
    @staticmethod
    def get_time_complexity() -> str:
        """Return the time complexity of this algorithm."""
        return "O(n²)"