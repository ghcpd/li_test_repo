# Multi-Person Schedule Conflict Detection System

This repository provides a complete command-line tool for multi-person schedule
conflict detection and analysis. The system processes a schedule CSV file,
identifies conflicts using three different algorithms, and produces a suite of
reports, visualisations, and validation metrics.

## Features
- Brute Force, Sweep Line, and Interval Tree conflict detection algorithms
- Precision, recall, F1, and accuracy scoring against a ground-truth JSON file
- Comprehensive conflict reports (CSV/TXT) including severity and conflict type
- Performance statistics with execution time and memory usage comparisons
- Visualisations: Gantt chart, conflict heatmap, and performance comparison

## Requirements
Python 3.12 or later. Install the runtime dependencies with:

```bash
pip install matplotlib pytest
```

## Usage
Run the command-line interface from the repository root:

```bash
python schedule_conflict_detector.py --input test_schedule.csv \
  --known known_conflicts.json --output report
```

This generates the report directory containing:
- `conflict_report.csv` / `conflict_report.txt`
- `validation_report.csv`
- `performance_statistics.csv`
- `gantt_chart.png`
- `conflict_heatmap.png`
- `algorithm_performance.png`

Use `pytest` to execute the automated test suite:

```bash
pytest
```
