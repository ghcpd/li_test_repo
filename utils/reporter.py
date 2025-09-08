"""
Report generation utilities for schedule conflict detection system.
"""
import csv
import os
import json
from typing import List, Dict, Any
from datetime import datetime
from algorithms.brute_force import ConflictResult
from utils.validator import ValidationMetrics


class PerformanceStats:
    """Container for algorithm performance statistics."""
    
    def __init__(self, algorithm_name: str, execution_time_ms: float, 
                 memory_usage_mb: float, conflicts_found: int):
        self.algorithm_name = algorithm_name
        self.execution_time_ms = execution_time_ms
        self.memory_usage_mb = memory_usage_mb
        self.conflicts_found = conflicts_found
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            'algorithm': self.algorithm_name,
            'execution_time_ms': round(self.execution_time_ms, 2),
            'memory_usage_mb': round(self.memory_usage_mb, 2),
            'conflicts_found': self.conflicts_found
        }


class ReportGenerator:
    """Generates various types of reports for the conflict detection system."""
    
    def __init__(self, output_dir: str = "report"):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory to save reports (default: "report")
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def generate_conflict_report_csv(self, conflicts: List[ConflictResult], filename: str = None) -> str:
        """
        Generate conflict report in CSV format.
        
        Args:
            conflicts: List of detected conflicts
            filename: Optional filename (default: conflicts_TIMESTAMP.csv)
            
        Returns:
            Path to generated report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conflicts_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            if not conflicts:
                # Write headers even if no conflicts
                writer = csv.writer(csvfile)
                writer.writerow([
                    'conflict_id', 'person_id', 'activity_1', 'activity_2',
                    'start_time_1', 'end_time_1', 'start_time_2', 'end_time_2',
                    'overlap_start', 'overlap_end', 'overlap_duration_minutes',
                    'conflict_type', 'severity', 'location_1', 'location_2'
                ])
                return filepath
            
            fieldnames = list(conflicts[0].to_dict().keys())
            fieldnames.insert(0, 'conflict_id')  # Add conflict ID as first column
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, conflict in enumerate(conflicts, 1):
                conflict_data = conflict.to_dict()
                conflict_data['conflict_id'] = f"CONF_{i:04d}"
                writer.writerow(conflict_data)
        
        return filepath
    
    def generate_conflict_report_txt(self, conflicts: List[ConflictResult], filename: str = None) -> str:
        """
        Generate conflict report in human-readable text format.
        
        Args:
            conflicts: List of detected conflicts
            filename: Optional filename (default: conflicts_TIMESTAMP.txt)
            
        Returns:
            Path to generated report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conflicts_{timestamp}.txt"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as txtfile:
            txtfile.write("SCHEDULE CONFLICT DETECTION REPORT\n")
            txtfile.write("=" * 50 + "\n\n")
            txtfile.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            txtfile.write(f"Total conflicts found: {len(conflicts)}\n\n")
            
            if not conflicts:
                txtfile.write("No conflicts detected.\n")
                return filepath
            
            # Group conflicts by person
            person_conflicts = {}
            for conflict in conflicts:
                person_id = conflict.item1.person_id
                if person_id not in person_conflicts:
                    person_conflicts[person_id] = []
                person_conflicts[person_id].append(conflict)
            
            # Write conflicts by person
            for person_id, person_conflict_list in sorted(person_conflicts.items()):
                txtfile.write(f"PERSON: {person_id}\n")
                txtfile.write("-" * 30 + "\n")
                
                for i, conflict in enumerate(person_conflict_list, 1):
                    txtfile.write(f"  Conflict {i}:\n")
                    txtfile.write(f"    Activities: {conflict.item1.activity_name} vs {conflict.item2.activity_name}\n")
                    txtfile.write(f"    Time 1: {conflict.item1.start_time.strftime('%Y-%m-%d %H:%M')} - {conflict.item1.end_time.strftime('%Y-%m-%d %H:%M')}\n")
                    txtfile.write(f"    Time 2: {conflict.item2.start_time.strftime('%Y-%m-%d %H:%M')} - {conflict.item2.end_time.strftime('%Y-%m-%d %H:%M')}\n")
                    txtfile.write(f"    Overlap: {conflict.overlap_start.strftime('%Y-%m-%d %H:%M')} - {conflict.overlap_end.strftime('%Y-%m-%d %H:%M')}\n")
                    txtfile.write(f"    Duration: {conflict.overlap_duration:.1f} minutes\n")
                    txtfile.write(f"    Type: {conflict.conflict_type}\n")
                    txtfile.write(f"    Severity: {conflict.severity}\n")
                    txtfile.write(f"    Locations: {conflict.item1.location} / {conflict.item2.location}\n")
                    txtfile.write("\n")
                
                txtfile.write("\n")
        
        return filepath
    
    def generate_performance_report(self, performance_stats: List[PerformanceStats], 
                                  validation_metrics: Dict[str, ValidationMetrics],
                                  filename: str = None) -> str:
        """
        Generate performance statistics report.
        
        Args:
            performance_stats: List of performance statistics for each algorithm
            validation_metrics: Dictionary mapping algorithm names to validation metrics
            filename: Optional filename (default: performance_TIMESTAMP.csv)
            
        Returns:
            Path to generated report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'algorithm', 'execution_time_ms', 'memory_usage_mb', 'conflicts_found',
                'precision', 'recall', 'f1_score', 'true_positives', 'false_positives', 'false_negatives'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for stats in performance_stats:
                row_data = stats.to_dict()
                
                # Add validation metrics if available
                if stats.algorithm_name in validation_metrics:
                    metrics = validation_metrics[stats.algorithm_name]
                    row_data.update({
                        'precision': round(metrics.precision, 4),
                        'recall': round(metrics.recall, 4),
                        'f1_score': round(metrics.f1_score, 4),
                        'true_positives': metrics.true_positives,
                        'false_positives': metrics.false_positives,
                        'false_negatives': metrics.false_negatives
                    })
                else:
                    # Fill with N/A if no validation metrics
                    row_data.update({
                        'precision': 'N/A',
                        'recall': 'N/A',
                        'f1_score': 'N/A',
                        'true_positives': 'N/A',
                        'false_positives': 'N/A',
                        'false_negatives': 'N/A'
                    })
                
                writer.writerow(row_data)
        
        return filepath
    
    def generate_validation_report(self, validation_report: List[Dict], filename: str = None) -> str:
        """
        Generate validation report showing correctness per conflict.
        
        Args:
            validation_report: List of validation report entries
            filename: Optional filename (default: validation_TIMESTAMP.csv)
            
        Returns:
            Path to generated report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"validation_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            if not validation_report:
                # Write headers even if no validation data
                writer = csv.writer(csvfile)
                writer.writerow([
                    'conflict_id', 'person_id', 'activity_1', 'activity_2',
                    'detected_start', 'detected_end', 'known_start', 'known_end',
                    'is_correct', 'status'
                ])
                return filepath
            
            # Get all possible fieldnames from all entries
            all_fieldnames = set()
            for entry in validation_report:
                all_fieldnames.update(entry.keys())
            
            # Sort fieldnames for consistent order
            fieldnames = sorted(list(all_fieldnames))
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in validation_report:
                # Fill missing fields with empty string
                complete_entry = {field: entry.get(field, '') for field in fieldnames}
                writer.writerow(complete_entry)
        
        return filepath
    
    def generate_summary_json(self, summary_data: Dict[str, Any], filename: str = None) -> str:
        """
        Generate summary report in JSON format.
        
        Args:
            summary_data: Dictionary containing summary information
            filename: Optional filename (default: summary_TIMESTAMP.json)
            
        Returns:
            Path to generated report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(summary_data, jsonfile, indent=2, default=str)
        
        return filepath