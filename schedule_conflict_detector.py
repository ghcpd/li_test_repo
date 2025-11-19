#!/usr/bin/env python3
"""
Multi-Person Schedule Conflict Detection System

A command-line tool for detecting scheduling conflicts in multi-person, multi-activity scenarios
and generating verifiable analysis reports with performance benchmarking and visualization.
"""

import argparse
import sys
import os
import traceback
from pathlib import Path
import json
import time
import tracemalloc
from typing import List, Dict, Tuple, Set
from datetime import datetime

from conflict_detector import BruteForceDetector, SweepLineDetector, IntervalTreeDetector
from data_loader import load_schedules, load_known_conflicts
from metrics import calculate_metrics, validate_conflicts
from report_generator import generate_conflict_report, generate_performance_report, generate_validation_report
from visualizer import create_gantt_chart, create_conflict_heatmap, create_performance_chart


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-Person Schedule Conflict Detection System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input test_schedule.csv --known known_conflicts.json --output report/
  %(prog)s --input test_schedule.csv --known known_conflicts.json --output report/ --algorithm all
  %(prog)s --input test_schedule.csv --output report/ --algorithm sweep --no-viz
        """
    )
    
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input CSV file containing schedule data'
    )
    
    parser.add_argument(
        '--known',
        type=str,
        default=None,
        help='Ground truth JSON file containing known conflicts for validation'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output directory for reports and visualizations'
    )
    
    parser.add_argument(
        '--algorithm',
        type=str,
        choices=['brute', 'sweep', 'interval', 'all'],
        default='all',
        help='Conflict detection algorithm to use (default: all)'
    )
    
    parser.add_argument(
        '--no-viz',
        action='store_true',
        help='Disable visualization generation'
    )
    
    parser.add_argument(
        '--filter-person',
        type=str,
        help='Filter visualizations for specific person ID'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()


def run_detection_algorithm(detector_class, schedules, verbose=False):
    """
    Run a conflict detection algorithm and measure performance.
    
    Args:
        detector_class: The detector class to instantiate
        schedules: List of schedule entries
        verbose: Whether to print verbose output
        
    Returns:
        Tuple of (conflicts, execution_time_ms, memory_usage_mb)
    """
    algorithm_name = detector_class.__name__
    
    if verbose:
        print(f"Running {algorithm_name}...")
    
    # Initialize detector
    detector = detector_class()
    
    # Start performance measurement
    tracemalloc.start()
    start_time = time.perf_counter()
    
    # Run detection
    conflicts = detector.detect_conflicts(schedules)
    
    # Measure performance
    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    execution_time_ms = (end_time - start_time) * 1000
    memory_usage_mb = peak / 1024 / 1024
    
    if verbose:
        print(f"  Found {len(conflicts)} conflicts")
        print(f"  Execution time: {execution_time_ms:.2f} ms")
        print(f"  Peak memory usage: {memory_usage_mb:.2f} MB")
    
    return conflicts, execution_time_ms, memory_usage_mb


def main():
    """Main entry point for the schedule conflict detector."""
    args = parse_arguments()
    
    # Validate input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.verbose:
        print("=" * 80)
        print("Multi-Person Schedule Conflict Detection System")
        print("=" * 80)
        print(f"\nInput file: {args.input}")
        print(f"Output directory: {args.output}")
        if args.known:
            print(f"Known conflicts file: {args.known}")
        print(f"Algorithm(s): {args.algorithm}")
        print()
    
    # Load input data
    if args.verbose:
        print("Loading schedule data...")
    
    try:
        schedules = load_schedules(args.input)
        if args.verbose:
            print(f"  Loaded {len(schedules)} schedule entries")
            unique_persons = len(set(s['person_id'] for s in schedules))
            print(f"  Unique persons: {unique_persons}")
    except Exception as e:
        print(f"Error loading schedules: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)
    
    # Load known conflicts if provided
    known_conflicts = None
    if args.known:
        if not os.path.exists(args.known):
            print(f"Warning: Known conflicts file '{args.known}' not found", file=sys.stderr)
        else:
            try:
                known_conflicts = load_known_conflicts(args.known)
                if args.verbose:
                    print(f"  Loaded {len(known_conflicts)} known conflicts")
            except Exception as e:
                print(f"Error loading known conflicts: {e}", file=sys.stderr)
                if args.verbose:
                    traceback.print_exc()
    
    # Determine which algorithms to run
    detectors = []
    if args.algorithm == 'all':
        detectors = [
            ('Brute Force', BruteForceDetector),
            ('Sweep Line', SweepLineDetector),
            ('Interval Tree', IntervalTreeDetector)
        ]
    elif args.algorithm == 'brute':
        detectors = [('Brute Force', BruteForceDetector)]
    elif args.algorithm == 'sweep':
        detectors = [('Sweep Line', SweepLineDetector)]
    elif args.algorithm == 'interval':
        detectors = [('Interval Tree', IntervalTreeDetector)]
    
    # Run detection algorithms and collect results
    results = {}
    
    if args.verbose:
        print("\nDetecting conflicts...")
    
    for name, detector_class in detectors:
        conflicts, exec_time, memory = run_detection_algorithm(
            detector_class, schedules, args.verbose
        )
        
        results[name] = {
            'conflicts': conflicts,
            'execution_time_ms': exec_time,
            'memory_usage_mb': memory,
            'num_conflicts': len(conflicts)
        }
    
    # Validate and calculate metrics if known conflicts are available
    if known_conflicts:
        if args.verbose:
            print("\nValidating detected conflicts...")
        
        for name, result in results.items():
            metrics = calculate_metrics(result['conflicts'], known_conflicts)
            result['metrics'] = metrics
            
            if args.verbose:
                print(f"\n{name} Metrics:")
                print(f"  Precision: {metrics['precision']:.4f}")
                print(f"  Recall: {metrics['recall']:.4f}")
                print(f"  F1 Score: {metrics['f1_score']:.4f}")
    
    # Generate reports
    if args.verbose:
        print("\nGenerating reports...")
    
    # Use the first algorithm's results for conflict report
    primary_result = list(results.values())[0]
    
    # Generate conflict report
    conflict_report_path = output_dir / "conflict_report.csv"
    generate_conflict_report(
        primary_result['conflicts'],
        conflict_report_path
    )
    if args.verbose:
        print(f"  Conflict report: {conflict_report_path}")
    
    # Generate performance report
    performance_report_path = output_dir / "performance_report.csv"
    generate_performance_report(
        results,
        performance_report_path
    )
    if args.verbose:
        print(f"  Performance report: {performance_report_path}")
    
    # Generate validation report if known conflicts available
    if known_conflicts:
        validation_report_path = output_dir / "validation_report.csv"
        generate_validation_report(
            primary_result['conflicts'],
            known_conflicts,
            validation_report_path
        )
        if args.verbose:
            print(f"  Validation report: {validation_report_path}")
    
    # Generate visualizations
    if not args.no_viz:
        if args.verbose:
            print("\nGenerating visualizations...")
        
        try:
            # Gantt chart
            gantt_path = output_dir / "gantt_chart.png"
            create_gantt_chart(
                schedules,
                primary_result['conflicts'],
                gantt_path,
                filter_person=args.filter_person
            )
            if args.verbose:
                print(f"  Gantt chart: {gantt_path}")
            
            # Conflict heatmap
            heatmap_path = output_dir / "conflict_heatmap.png"
            create_conflict_heatmap(
                schedules,
                primary_result['conflicts'],
                heatmap_path
            )
            if args.verbose:
                print(f"  Conflict heatmap: {heatmap_path}")
            
            # Performance comparison chart
            if len(results) > 1:
                performance_chart_path = output_dir / "performance_comparison.png"
                create_performance_chart(
                    results,
                    performance_chart_path
                )
                if args.verbose:
                    print(f"  Performance chart: {performance_chart_path}")
        
        except Exception as e:
            print(f"Warning: Error generating visualizations: {e}", file=sys.stderr)
            if args.verbose:
                traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for name, result in results.items():
        print(f"\n{name}:")
        print(f"  Conflicts detected: {result['num_conflicts']}")
        print(f"  Execution time: {result['execution_time_ms']:.2f} ms")
        print(f"  Memory usage: {result['memory_usage_mb']:.2f} MB")
        
        if 'metrics' in result:
            metrics = result['metrics']
            print(f"  Precision: {metrics['precision']:.4f}")
            print(f"  Recall: {metrics['recall']:.4f}")
            print(f"  F1 Score: {metrics['f1_score']:.4f}")
    
    print(f"\nAll reports saved to: {output_dir}")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
