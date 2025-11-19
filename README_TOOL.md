# Multi-Person Schedule Conflict Detection System

A comprehensive Python command-line tool for detecting and analyzing scheduling conflicts in multi-person, multi-activity scenarios. The system provides deterministic conflict detection, performance benchmarking, and detailed visualization capabilities.

## Features

### Conflict Detection Algorithms

The system implements three different algorithms with varying time complexities:

1. **Brute Force Method** (O(n²))
   - Compares every pair of schedules
   - Simple and straightforward
   - Best for small datasets

2. **Sweep Line Method** (O(n log n))
   - Sorts events by time and uses a sweep line approach
   - Efficient for medium to large datasets
   - **Fastest algorithm in benchmarks**

3. **Interval Tree Method** (O(n log n))
   - Uses interval tree data structure
   - Efficient overlap queries
   - Good for repeated queries

### Analysis & Reporting

- **Conflict Reports**: Detailed CSV reports with conflict information including:
  - Conflict ID, Person ID, Activities involved
  - Time intervals and overlap duration
  - Conflict type (full overlap, partial overlap, containment)
  - Severity rating (Low/Medium/High)
  - Location information

- **Performance Statistics**: Algorithm comparison including:
  - Execution time (milliseconds)
  - Memory usage (MB)
  - Accuracy metrics (Precision, Recall, F1 Score)

- **Validation Reports**: Compare detected conflicts with known ground truth:
  - True positives (correctly detected)
  - False positives (incorrectly detected)
  - False negatives (missed conflicts)

### Visualization

The system generates three types of charts:

1. **Gantt Chart**: Timeline view of activities per person with conflicts highlighted in red
2. **Conflict Heatmap**: Shows conflict frequency by time of day and person
3. **Performance Comparison**: Bar charts comparing algorithm execution time and memory usage

## Installation

### Requirements

- Python 3.8 or higher
- pip package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/ghcpd/li_test_repo.git
cd li_test_repo

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python schedule_conflict_detector.py --input test_schedule.csv --known known_conflicts.json --output report/
```

### Command-Line Options

```
Required arguments:
  --input INPUT         Input CSV file containing schedule data
  --output OUTPUT       Output directory for reports and visualizations

Optional arguments:
  --known KNOWN         Ground truth JSON file for validation
  --algorithm {brute,sweep,interval,all}
                        Algorithm to use (default: all)
  --no-viz              Disable visualization generation
  --filter-person ID    Filter visualizations for specific person
  --verbose             Enable verbose output
  --help                Show help message
```

### Examples

#### Run all algorithms with validation
```bash
python schedule_conflict_detector.py \
  --input test_schedule.csv \
  --known known_conflicts.json \
  --output report/ \
  --verbose
```

#### Run specific algorithm without visualizations
```bash
python schedule_conflict_detector.py \
  --input test_schedule.csv \
  --output report/ \
  --algorithm sweep \
  --no-viz
```

#### Filter visualizations for specific person
```bash
python schedule_conflict_detector.py \
  --input test_schedule.csv \
  --output report/ \
  --filter-person P001
```

## Input Format

### Schedule CSV Format

The input CSV must contain the following columns:

```csv
person_id,start_time,end_time,activity_name,location
P001,2025-09-08 14:30,2025-09-08 15:30,Meeting,Conference Room A
P001,2025-09-08 15:00,2025-09-08 16:00,Training,Conference Room B
```

- **person_id**: Unique identifier for the person
- **start_time**: Start datetime in format `YYYY-MM-DD HH:MM`
- **end_time**: End datetime in format `YYYY-MM-DD HH:MM`
- **activity_name**: Name of the activity
- **location**: Location of the activity

### Known Conflicts JSON Format (Optional)

For validation, provide a JSON file with known conflicts:

```json
[
  {
    "person_id": "P001",
    "original_schedule": "2025-09-08 14:30 - 2025-09-08 15:30",
    "conflict_schedule": "2025-09-08 15:00 - 2025-09-08 16:00",
    "activity_1": "Meeting",
    "activity_2": "Training"
  }
]
```

## Output

The tool generates the following outputs in the specified directory:

### Reports (CSV format)

1. **conflict_report.csv**: Detailed list of all detected conflicts
2. **performance_report.csv**: Algorithm performance comparison
3. **validation_report.csv**: Validation against known conflicts (if provided)

### Visualizations (PNG format)

1. **gantt_chart.png**: Timeline view with conflicts highlighted
2. **conflict_heatmap.png**: Frequency heatmap by time and person
3. **performance_comparison.png**: Algorithm performance charts

## Performance Benchmarks

Tested with 12,074 schedule entries across 100 people:

| Algorithm      | Execution Time | Memory Usage | Conflicts Found |
|----------------|----------------|--------------|-----------------|
| Brute Force    | 152 ms         | 1.99 MB      | 3,766           |
| **Sweep Line** | **63 ms**      | 2.06 MB      | 3,766           |
| Interval Tree  | 471 ms         | 2.05 MB      | 3,766           |

**Recommendation**: Use Sweep Line algorithm for best performance on large datasets.

## Conflict Type Classification

The system classifies conflicts into three types:

1. **Full Overlap**: Two activities have identical start and end times
2. **Partial Overlap**: Two activities overlap for part of their duration
3. **Containment**: One activity is completely contained within another

## Severity Ratings

Conflicts are rated by duration:

- **Low**: < 15 minutes overlap
- **Medium**: 15-60 minutes overlap
- **High**: > 60 minutes overlap

## Validation Metrics

When a ground truth file is provided, the system calculates:

- **Precision**: Proportion of detected conflicts that are correct
- **Recall**: Proportion of known conflicts that were detected
- **F1 Score**: Harmonic mean of precision and recall

## Architecture

The system is modular with separate components:

- `schedule_conflict_detector.py`: Main CLI entry point
- `data_loader.py`: CSV and JSON parsing
- `conflict_detector.py`: Three detection algorithms
- `metrics.py`: Validation and metrics calculation
- `report_generator.py`: CSV report generation
- `visualizer.py`: Chart and graph generation

## Troubleshooting

### Large Dataset Visualization Issues

For very large datasets (>1000 people), visualizations are automatically limited:
- Gantt charts show first 5 people only
- Heatmaps show first 20 people only
- Use `--filter-person` to visualize specific individuals

### Memory Constraints

For datasets with >100,000 entries:
- Use `--algorithm sweep` (most memory efficient)
- Consider `--no-viz` to skip visualization generation
- Process data in batches if needed

## License

This project is provided as-is for educational and research purposes.

## Contributing

For bug reports or feature requests, please open an issue on GitHub.
