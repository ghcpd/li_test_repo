"""
Validation utilities for comparing detected conflicts with known conflicts.
"""
from typing import List, Dict, Tuple, Set
from datetime import datetime
from utils.data_parser import ConflictItem
from algorithms.brute_force import ConflictResult


class ValidationMetrics:
    """Container for validation metrics."""
    
    def __init__(self, precision: float, recall: float, f1_score: float,
                 true_positives: int, false_positives: int, false_negatives: int):
        self.precision = precision
        self.recall = recall
        self.f1_score = f1_score
        self.true_positives = true_positives
        self.false_positives = false_positives
        self.false_negatives = false_negatives
    
    def __repr__(self):
        return f"ValidationMetrics(P={self.precision:.3f}, R={self.recall:.3f}, F1={self.f1_score:.3f})"


class ConflictValidator:
    """Validates detected conflicts against known ground truth conflicts."""
    
    @staticmethod
    def validate_conflicts(detected_conflicts: List[ConflictResult], 
                         known_conflicts: List[ConflictItem],
                         tolerance_minutes: int = 5) -> ValidationMetrics:
        """
        Validate detected conflicts against known conflicts.
        
        Args:
            detected_conflicts: List of detected ConflictResult objects
            known_conflicts: List of known ConflictItem objects
            tolerance_minutes: Time tolerance for matching conflicts (default: 5 minutes)
            
        Returns:
            ValidationMetrics object with precision, recall, and F1 score
        """
        # Convert detected conflicts to a standardized format for comparison
        detected_set = ConflictValidator._conflicts_to_comparable_set(detected_conflicts)
        known_set = ConflictValidator._known_conflicts_to_comparable_set(known_conflicts)
        
        # Find matches with tolerance
        matched_detected = set()
        matched_known = set()
        
        for detected in detected_set:
            for known in known_set:
                if ConflictValidator._conflicts_match(detected, known, tolerance_minutes):
                    matched_detected.add(detected)
                    matched_known.add(known)
                    break  # Each detected conflict can only match one known conflict
        
        # Calculate metrics
        true_positives = len(matched_detected)
        false_positives = len(detected_set) - true_positives
        false_negatives = len(known_set) - len(matched_known)
        
        precision = true_positives / len(detected_set) if detected_set else 0.0
        recall = true_positives / len(known_set) if known_set else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return ValidationMetrics(precision, recall, f1_score, true_positives, false_positives, false_negatives)
    
    @staticmethod
    def _conflicts_to_comparable_set(conflicts: List[ConflictResult]) -> Set[Tuple]:
        """Convert detected conflicts to a set of comparable tuples."""
        comparable_set = set()
        
        for conflict in conflicts:
            # Create a tuple that uniquely identifies the conflict
            # Sort activities to ensure consistent ordering
            activities = sorted([conflict.item1.activity_name, conflict.item2.activity_name])
            
            conflict_tuple = (
                conflict.item1.person_id,
                activities[0],
                activities[1],
                conflict.overlap_start,
                conflict.overlap_end
            )
            comparable_set.add(conflict_tuple)
        
        return comparable_set
    
    @staticmethod
    def _known_conflicts_to_comparable_set(known_conflicts: List[ConflictItem]) -> Set[Tuple]:
        """Convert known conflicts to a set of comparable tuples."""
        comparable_set = set()
        
        for conflict in known_conflicts:
            # Create a tuple that uniquely identifies the conflict
            # Sort activities to ensure consistent ordering
            activities = sorted([conflict.activity_1, conflict.activity_2])
            
            # Use the overlap period from the conflict schedule
            conflict_tuple = (
                conflict.person_id,
                activities[0],
                activities[1],
                conflict.conflict_start,
                conflict.conflict_end
            )
            comparable_set.add(conflict_tuple)
        
        return comparable_set
    
    @staticmethod
    def _conflicts_match(detected: Tuple, known: Tuple, tolerance_minutes: int) -> bool:
        """
        Check if a detected conflict matches a known conflict within tolerance.
        
        Args:
            detected: Tuple representing detected conflict
            known: Tuple representing known conflict
            tolerance_minutes: Time tolerance in minutes
            
        Returns:
            True if conflicts match within tolerance
        """
        # Unpack tuples
        det_person, det_act1, det_act2, det_start, det_end = detected
        known_person, known_act1, known_act2, known_start, known_end = known
        
        # Check if person and activities match
        if det_person != known_person:
            return False
        
        if det_act1 != known_act1 or det_act2 != known_act2:
            return False
        
        # Check if time periods overlap within tolerance
        tolerance_seconds = tolerance_minutes * 60
        
        # Calculate time differences
        start_diff = abs((det_start - known_start).total_seconds())
        end_diff = abs((det_end - known_end).total_seconds())
        
        # Consider a match if both start and end times are within tolerance
        return start_diff <= tolerance_seconds and end_diff <= tolerance_seconds
    
    @staticmethod
    def generate_validation_report(detected_conflicts: List[ConflictResult],
                                 known_conflicts: List[ConflictItem],
                                 metrics: ValidationMetrics) -> List[Dict]:
        """
        Generate a detailed validation report showing correctness per conflict.
        
        Args:
            detected_conflicts: List of detected conflicts
            known_conflicts: List of known conflicts
            metrics: Validation metrics
            
        Returns:
            List of dictionaries representing the validation report
        """
        report = []
        
        # Convert to comparable sets for matching
        detected_set = ConflictValidator._conflicts_to_comparable_set(detected_conflicts)
        known_set = ConflictValidator._known_conflicts_to_comparable_set(known_conflicts)
        
        # Track which conflicts have been matched
        matched_detected = set()
        matched_known = set()
        
        # Add detected conflicts to report
        for i, conflict in enumerate(detected_conflicts):
            detected_tuple = list(ConflictValidator._conflicts_to_comparable_set([conflict]))[0]
            
            # Check if this detected conflict matches any known conflict
            is_correct = False
            matched_known_conflict = None
            
            for known_tuple in known_set:
                if ConflictValidator._conflicts_match(detected_tuple, known_tuple, 5):
                    is_correct = True
                    matched_known_conflict = known_tuple
                    matched_detected.add(detected_tuple)
                    matched_known.add(known_tuple)
                    break
            
            report_entry = {
                'conflict_id': f"DETECTED_{i+1}",
                'person_id': conflict.item1.person_id,
                'activity_1': conflict.item1.activity_name,
                'activity_2': conflict.item2.activity_name,
                'detected_start': conflict.overlap_start.strftime('%Y-%m-%d %H:%M'),
                'detected_end': conflict.overlap_end.strftime('%Y-%m-%d %H:%M'),
                'is_correct': is_correct,
                'status': 'True Positive' if is_correct else 'False Positive'
            }
            
            if matched_known_conflict:
                report_entry['known_start'] = matched_known_conflict[3].strftime('%Y-%m-%d %H:%M')
                report_entry['known_end'] = matched_known_conflict[4].strftime('%Y-%m-%d %H:%M')
            
            report.append(report_entry)
        
        # Add missed known conflicts (false negatives)
        unmatched_known = known_set - matched_known
        for i, known_tuple in enumerate(unmatched_known):
            person_id, act1, act2, start_time, end_time = known_tuple
            
            report_entry = {
                'conflict_id': f"MISSED_{i+1}",
                'person_id': person_id,
                'activity_1': act1,
                'activity_2': act2,
                'detected_start': 'N/A',
                'detected_end': 'N/A',
                'known_start': start_time.strftime('%Y-%m-%d %H:%M'),
                'known_end': end_time.strftime('%Y-%m-%d %H:%M'),
                'is_correct': False,
                'status': 'False Negative'
            }
            
            report.append(report_entry)
        
        return report