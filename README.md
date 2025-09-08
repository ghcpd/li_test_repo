# Multi-Person Schedule Conflict Detection System

A complete Python command-line tool for detecting scheduling conflicts in multi-person, multi-activity scenarios and generating verifiable analysis reports.

## Features

### Core Algorithms
- **Brute Force Method** (O(n²)): Compare every pair of schedules
- **Sweep Line Method** (O(n log n)): Sort by start time and use scanning approach
- **Interval Tree Method** (O(n log n)): Use interval tree for efficient conflict queries

### Analysis & Validation
- Compare detected conflicts with ground truth data
- Compute evaluation metrics: Precision, Recall, F1 Score
- Generate validation reports showing correctness per conflict

### Report Generation
- **Conflict Reports**: CSV/TXT format with detailed conflict information
- **Performance Statistics**: Execution time, memory usage, accuracy metrics
- **Validation Reports**: Comparison with known conflicts

### Visualizations
- **Gantt Chart**: Activity timelines per person with conflict highlighting
- **Conflict Heatmap**: Conflict frequency by time and person
- **Performance Comparison**: Algorithm execution time and memory usage charts

## Requirements

- Python 3.7+
- Dependencies (install with `pip install -r requirements.txt`):
  - matplotlib>=3.5.0
  - pandas>=1.3.0
  - memory-profiler>=0.60.0
  - intervaltree>=3.1.0

## Usage

### Basic Usage
```bash
python schedule_conflict_detector.py --input test_schedule.csv --known known_conflicts.json --output report/
```

### Advanced Options
```bash
# Run specific algorithms only
python schedule_conflict_detector.py --input test_schedule.csv --algorithms brute_force sweep_line

# Skip visualizations (faster execution)
python schedule_conflict_detector.py --input test_schedule.csv --no-visualization

# Verbose output with detailed metrics
python schedule_conflict_detector.py --input test_schedule.csv --verbose

# Limit Gantt chart to specific number of persons
python schedule_conflict_detector.py --input test_schedule.csv --max-persons 5

# Adjust time tolerance for conflict matching
python schedule_conflict_detector.py --input test_schedule.csv --tolerance 10
```

### Command-Line Arguments

- `--input, -i`: Input CSV file containing schedule data (required)
- `--known, -k`: JSON file containing known conflicts for validation
- `--output, -o`: Output directory for reports (default: report)
- `--algorithms, -a`: Algorithms to run (choices: brute_force, sweep_line, interval_tree)
- `--no-visualization`: Skip generating visualizations
- `--tolerance`: Time tolerance in minutes for conflict validation (default: 5)
- `--max-persons`: Maximum persons to display in Gantt chart (default: 10)
- `--verbose, -v`: Enable verbose output

## Input Data Formats

### Schedule CSV Format
```csv
person_id,start_time,end_time,activity_name,location,scenario
P001,2025-09-15 11:30,2025-09-15 12:15,Training,Conference Room B,5people_sparse
P001,2025-09-09 16:15,2025-09-09 16:45,Testing,Conference Room B,5people_sparse
```

### Known Conflicts JSON Format
```json
[
  {
    "person_id": "P004",
    "original_schedule": "2025-09-17 18:45 - 2025-09-17 19:15",
    "conflict_schedule": "2025-09-17 19:02 - 2025-09-17 19:48",
    "activity_1": "Requirements Analysis",
    "activity_2": "Design Review"
  }
]
```

## Output Files

The system generates comprehensive reports in the specified output directory:

### Conflict Reports
- `conflicts_[algorithm].csv`: Detailed conflict data in CSV format
- `conflicts_[algorithm].txt`: Human-readable conflict report

### Performance & Validation Reports
- `performance_[timestamp].csv`: Algorithm performance comparison
- `validation_[timestamp].csv`: Validation against known conflicts
- `summary_[timestamp].json`: Complete summary in JSON format

### Visualizations
- `gantt_chart_[timestamp].png`: Schedule timeline with conflicts
- `conflict_heatmap_[timestamp].png`: Conflict frequency visualization
- `performance_comparison_[timestamp].png`: Algorithm performance charts

## Example Results

### Performance Comparison (12,074 schedule items)
| Algorithm     | Execution Time | Memory Usage | Conflicts Found |
|---------------|----------------|--------------|-----------------|
| Brute Force   | 29,087 ms      | 0.58 MB      | 3,766          |
| Sweep Line    | 91 ms          | 0.70 MB      | 3,766          |
| Interval Tree | 500 ms         | 0.74 MB      | 3,766          |

### Validation Metrics
- **Precision**: 0.134 (13.4% of detected conflicts are true positives)
- **Recall**: 0.320 (32.0% of known conflicts were detected)
- **F1 Score**: 0.189

## Algorithm Details

### Brute Force (O(n²))
- Compares every pair of schedule items
- Simple but inefficient for large datasets
- Best for small datasets or verification

### Sweep Line (O(n log n))
- Sorts events by time and processes chronologically
- Maintains active intervals during sweep
- Most efficient for this problem type

### Interval Tree (O(n log n))
- Uses specialized tree structure for interval queries
- Good for repeated queries but has overhead
- Memory efficient for large datasets

## Project Structure

```
├── schedule_conflict_detector.py    # Main CLI application
├── requirements.txt                 # Python dependencies
├── algorithms/                      # Conflict detection algorithms
│   ├── __init__.py
│   ├── brute_force.py              # O(n²) brute force algorithm
│   ├── sweep_line.py               # O(n log n) sweep line algorithm
│   └── interval_tree.py            # O(n log n) interval tree algorithm
├── utils/                          # Utility modules
│   ├── __init__.py
│   ├── data_parser.py              # CSV/JSON parsing utilities
│   ├── validator.py                # Conflict validation against ground truth
│   ├── reporter.py                 # Report generation utilities
│   └── visualizer.py               # Visualization utilities
└── report/                         # Output directory (created automatically)
```

## Contributing

This system is designed to be extensible:

1. **Add new algorithms**: Implement in `algorithms/` following the interface pattern
2. **Add new report formats**: Extend `utils/reporter.py`
3. **Add new visualizations**: Extend `utils/visualizer.py`
4. **Add new input formats**: Extend `utils/data_parser.py`

## License

This project is part of the li_test_repo and follows the repository's licensing terms.