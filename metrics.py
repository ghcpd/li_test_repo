"""
Metrics calculation module for evaluating conflict detection performance.
"""

from typing import List, Dict, Set, Tuple
from datetime import datetime


def normalize_conflict_key(person_id: str, start1: datetime, end1: datetime,
                           start2: datetime, end2: datetime) -> Tuple:
    """
    Create a normalized key for conflict comparison.
    Ensures that conflicts are compared regardless of order.
    
    Args:
        person_id: Person identifier
        start1, end1: First time interval
        start2, end2: Second time interval
        
    Returns:
        Tuple representing the conflict in canonical form
    """
    # Sort the time intervals to create canonical representation
    if start1 < start2 or (start1 == start2 and end1 <= end2):
        return (person_id, start1, end1, start2, end2)
    else:
        return (person_id, start2, end2, start1, end1)


def conflicts_match(detected: Dict, known: Dict, tolerance_minutes: int = 5) -> bool:
    """
    Check if a detected conflict matches a known conflict.
    Allows for small time differences due to rounding or parsing.
    
    Args:
        detected: Detected conflict dictionary
        known: Known conflict dictionary
        tolerance_minutes: Tolerance in minutes for time matching
        
    Returns:
        True if conflicts match, False otherwise
    """
    if detected['person_id'] != known['person_id']:
        return False
    
    # Check if the conflicts involve the same time ranges (with tolerance)
    def times_match(t1: datetime, t2: datetime) -> bool:
        diff = abs((t1 - t2).total_seconds() / 60)
        return diff <= tolerance_minutes
    
    # Try matching in both orders
    match1 = (
        times_match(detected['start_time_1'], known['original_start']) and
        times_match(detected['end_time_1'], known['original_end']) and
        times_match(detected['start_time_2'], known['conflict_start']) and
        times_match(detected['end_time_2'], known['conflict_end'])
    )
    
    match2 = (
        times_match(detected['start_time_1'], known['conflict_start']) and
        times_match(detected['end_time_1'], known['conflict_end']) and
        times_match(detected['start_time_2'], known['original_start']) and
        times_match(detected['end_time_2'], known['original_end'])
    )
    
    return match1 or match2


def validate_conflicts(detected_conflicts: List[Dict], 
                      known_conflicts: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Validate detected conflicts against known conflicts.
    
    Args:
        detected_conflicts: List of detected conflicts
        known_conflicts: List of known/ground truth conflicts
        
    Returns:
        Dictionary with keys:
        - 'true_positives': Correctly detected conflicts
        - 'false_positives': Incorrectly detected conflicts
        - 'false_negatives': Missed known conflicts
    """
    true_positives = []
    false_positives = []
    false_negatives = []
    
    # Track which known conflicts have been matched
    matched_known = set()
    
    # Check each detected conflict
    for detected in detected_conflicts:
        matched = False
        
        for i, known in enumerate(known_conflicts):
            if i in matched_known:
                continue
            
            if conflicts_match(detected, known):
                true_positives.append({
                    'detected': detected,
                    'known': known,
                    'status': 'match'
                })
                matched_known.add(i)
                matched = True
                break
        
        if not matched:
            false_positives.append({
                'detected': detected,
                'status': 'false_positive'
            })
    
    # Find unmatched known conflicts (false negatives)
    for i, known in enumerate(known_conflicts):
        if i not in matched_known:
            false_negatives.append({
                'known': known,
                'status': 'missed'
            })
    
    return {
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives
    }


def calculate_metrics(detected_conflicts: List[Dict], 
                     known_conflicts: List[Dict]) -> Dict[str, float]:
    """
    Calculate precision, recall, and F1 score.
    
    Args:
        detected_conflicts: List of detected conflicts
        known_conflicts: List of known conflicts
        
    Returns:
        Dictionary with precision, recall, f1_score, and counts
    """
    validation = validate_conflicts(detected_conflicts, known_conflicts)
    
    tp = len(validation['true_positives'])
    fp = len(validation['false_positives'])
    fn = len(validation['false_negatives'])
    
    # Calculate metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'true_positives': tp,
        'false_positives': fp,
        'false_negatives': fn,
        'total_detected': len(detected_conflicts),
        'total_known': len(known_conflicts)
    }
