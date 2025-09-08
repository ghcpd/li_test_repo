#!/usr/bin/env python3
"""
Multi-Person Schedule Conflict Detection System

A complete Python command-line tool for detecting scheduling conflicts in 
multi-person, multi-activity scenarios and generating verifiable analysis reports.
"""

import argparse
import time
import tracemalloc
import traceback
from typing import List, Dict, Any
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_parser import DataParser, ScheduleItem, ConflictItem
from algorithms.brute_force import BruteForceDetector, ConflictResult
from algorithms.sweep_line import SweepLineDetector
from algorithms.interval_tree import IntervalTreeDetector
from utils.validator import ConflictValidator, ValidationMetrics
from utils.reporter import ReportGenerator, PerformanceStats
from utils.visualizer import Visualizer


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-Person Schedule Conflict Detection System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python schedule_conflict_detector.py --input test_schedule.csv --known known_conflicts.json --output report/
  python schedule_conflict_detector.py --input test_schedule.csv --algorithms brute_force sweep_line
  python schedule_conflict_detector.py --input test_schedule.csv --no-visualization
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input CSV file containing schedule data"
    )
    
    parser.add_argument(
        "--known", "-k",
        help="JSON file containing known conflicts for validation"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="report",
        help="Output directory for reports and visualizations (default: report)"
    )
    
    parser.add_argument(
        "--algorithms", "-a",
        nargs="+",
        choices=["brute_force", "sweep_line", "interval_tree"],
        default=["brute_force", "sweep_line", "interval_tree"],
        help="Algorithms to run (default: all algorithms)"
    )
    
    parser.add_argument(
        "--no-visualization",
        action="store_true",
        help="Skip generating visualizations"
    )
    
    parser.add_argument(
        "--tolerance",
        type=int,
        default=5,
        help="Time tolerance in minutes for conflict validation (default: 5)"
    )
    
    parser.add_argument(
        "--max-persons",
        type=int,
        default=10,
        help="Maximum number of persons to display in Gantt chart (default: 10)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def run_algorithm_with_profiling(algorithm_class, schedules: List[ScheduleItem], 
                                algorithm_name: str, verbose: bool = False) -> tuple:
    """
    Run conflict detection algorithm with performance profiling.
    
    Args:
        algorithm_class: Algorithm class to run
        schedules: List of schedule items
        algorithm_name: Name of the algorithm for reporting
        verbose: Whether to print verbose output
        
    Returns:
        Tuple of (conflicts, performance_stats)
    """
    if verbose:
        print(f"Running {algorithm_name} algorithm...")
    
    # Start memory profiling
    tracemalloc.start()
    
    # Record start time
    start_time = time.time()
    
    # Run the algorithm
    conflicts = algorithm_class.detect_conflicts(schedules)
    
    # Record end time
    end_time = time.time()
    
    # Get memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Calculate metrics
    execution_time_ms = (end_time - start_time) * 1000
    memory_usage_mb = peak / 1024 / 1024  # Convert to MB
    
    performance_stats = PerformanceStats(
        algorithm_name=algorithm_name,
        execution_time_ms=execution_time_ms,
        memory_usage_mb=memory_usage_mb,
        conflicts_found=len(conflicts)
    )
    
    if verbose:
        print(f"  - Found {len(conflicts)} conflicts")
        print(f"  - Execution time: {execution_time_ms:.2f} ms")
        print(f"  - Memory usage: {memory_usage_mb:.2f} MB")
    
    return conflicts, performance_stats


def main():
    """Main function."""
    args = parse_arguments()
    
    if args.verbose:
        print("Multi-Person Schedule Conflict Detection System")
        print("=" * 50)
        print(f"Input file: {args.input}")
        print(f"Known conflicts file: {args.known}")
        print(f"Output directory: {args.output}")
        print(f"Algorithms to run: {', '.join(args.algorithms)}")
        print()
    
    try:
        # Parse input data
        if args.verbose:
            print("Parsing input data...")
        
        if not os.path.exists(args.input):
            print(f"Error: Input file '{args.input}' not found.")
            sys.exit(1)
        
        schedules = DataParser.parse_schedule_csv(args.input)
        
        if not schedules:
            print("Error: No valid schedule data found in input file.")
            sys.exit(1)
        
        if args.verbose:
            print(f"Loaded {len(schedules)} schedule items")
        
        # Parse known conflicts if provided
        known_conflicts = []
        if args.known:
            if os.path.exists(args.known):
                known_conflicts = DataParser.parse_known_conflicts_json(args.known)
                if args.verbose:
                    print(f"Loaded {len(known_conflicts)} known conflicts")
            else:
                print(f"Warning: Known conflicts file '{args.known}' not found. Skipping validation.")
        
        # Initialize components
        reporter = ReportGenerator(args.output)
        visualizer = Visualizer(args.output) if not args.no_visualization else None
        
        # Algorithm mapping
        algorithm_map = {
            "brute_force": (BruteForceDetector, "Brute Force"),
            "sweep_line": (SweepLineDetector, "Sweep Line"),
            "interval_tree": (IntervalTreeDetector, "Interval Tree")
        }
        
        # Run algorithms
        all_conflicts = {}
        all_performance_stats = []
        all_validation_metrics = {}
        
        for algorithm_name in args.algorithms:
            if algorithm_name in algorithm_map:
                algorithm_class, display_name = algorithm_map[algorithm_name]
                
                conflicts, performance_stats = run_algorithm_with_profiling(
                    algorithm_class, schedules, display_name, args.verbose
                )
                
                all_conflicts[display_name] = conflicts
                all_performance_stats.append(performance_stats)
                
                # Validate against known conflicts if available
                if known_conflicts:
                    validation_metrics = ConflictValidator.validate_conflicts(
                        conflicts, known_conflicts, args.tolerance
                    )
                    all_validation_metrics[display_name] = validation_metrics
                    
                    if args.verbose:
                        print(f"  - Precision: {validation_metrics.precision:.4f}")
                        print(f"  - Recall: {validation_metrics.recall:.4f}")
                        print(f"  - F1 Score: {validation_metrics.f1_score:.4f}")
                
                if args.verbose:
                    print()
        
        # Generate reports
        if args.verbose:
            print("Generating reports...")
        
        report_files = []
        
        # Generate conflict reports for each algorithm
        for algorithm_name, conflicts in all_conflicts.items():
            safe_name = algorithm_name.lower().replace(" ", "_")
            
            # CSV report
            csv_file = reporter.generate_conflict_report_csv(
                conflicts, f"conflicts_{safe_name}.csv"
            )
            report_files.append(csv_file)
            
            # Text report
            txt_file = reporter.generate_conflict_report_txt(
                conflicts, f"conflicts_{safe_name}.txt"
            )
            report_files.append(txt_file)
        
        # Generate performance report
        performance_file = reporter.generate_performance_report(
            all_performance_stats, all_validation_metrics
        )
        report_files.append(performance_file)
        
        # Generate validation report if known conflicts were provided
        if known_conflicts and all_conflicts:
            # Use the first algorithm's results for detailed validation report
            first_algorithm = list(all_conflicts.keys())[0]
            first_conflicts = all_conflicts[first_algorithm]
            first_metrics = all_validation_metrics.get(first_algorithm)
            
            if first_metrics:
                validation_report = ConflictValidator.generate_validation_report(
                    first_conflicts, known_conflicts, first_metrics
                )
                validation_file = reporter.generate_validation_report(validation_report)
                report_files.append(validation_file)
        
        # Generate summary report
        summary_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "input_file": args.input,
            "known_conflicts_file": args.known,
            "total_schedules": len(schedules),
            "algorithms_run": args.algorithms,
            "conflicts_detected": {alg: len(conflicts) for alg, conflicts in all_conflicts.items()},
            "performance_stats": [stats.to_dict() for stats in all_performance_stats],
            "validation_metrics": {
                alg: {
                    "precision": metrics.precision,
                    "recall": metrics.recall,
                    "f1_score": metrics.f1_score
                } for alg, metrics in all_validation_metrics.items()
            },
            "report_files": report_files
        }
        
        summary_file = reporter.generate_summary_json(summary_data)
        report_files.append(summary_file)
        
        # Generate visualizations
        if visualizer and not args.no_visualization:
            if args.verbose:
                print("Generating visualizations...")
            
            # Use the first algorithm's results for visualizations
            if all_conflicts:
                first_algorithm = list(all_conflicts.keys())[0]
                first_conflicts = all_conflicts[first_algorithm]
                
                # Gantt chart
                gantt_file = visualizer.create_gantt_chart(
                    schedules, first_conflicts, args.max_persons
                )
                report_files.append(gantt_file)
                
                # Conflict heatmap
                heatmap_file = visualizer.create_conflict_heatmap(first_conflicts)
                report_files.append(heatmap_file)
            
            # Performance comparison chart
            if len(all_performance_stats) > 1:
                performance_chart_file = visualizer.create_performance_comparison_chart(
                    all_performance_stats
                )
                report_files.append(performance_chart_file)
        
        # Final summary
        print("Schedule Conflict Detection Complete!")
        print(f"Output directory: {args.output}")
        print(f"Total schedules processed: {len(schedules)}")
        
        if all_conflicts:
            print("\nConflicts detected by algorithm:")
            for algorithm_name, conflicts in all_conflicts.items():
                print(f"  {algorithm_name}: {len(conflicts)} conflicts")
        
        if all_validation_metrics:
            print("\nValidation metrics:")
            for algorithm_name, metrics in all_validation_metrics.items():
                print(f"  {algorithm_name}: P={metrics.precision:.3f}, R={metrics.recall:.3f}, F1={metrics.f1_score:.3f}")
        
        print(f"\nGenerated {len(report_files)} output files:")
        for file_path in report_files:
            print(f"  {file_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if args.verbose:
            print("\nTraceback:")
            print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()