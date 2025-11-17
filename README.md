# Multi-Person Schedule Conflict Detection System

This repository provides a command-line tool for detecting scheduling conflicts
across multiple people and activities. The tool supports three conflict
detection algorithms, performance benchmarking, validation against a ground
truth dataset, and visualization of the resulting schedules and conflicts.

## Requirements

Install the Python dependencies before running the tool:

```
pip install matplotlib pytest
```

## Usage

Run the conflict detector with the provided sample data:

```
python schedule_conflict_detector.py --input test_schedule.csv --known known_conflicts.json --output report_output
```

The command generates:

- `conflict_report.csv` and `conflict_report.txt` summarizing detected conflicts
- `validation_report.csv` comparing detections to the ground-truth annotations
- `performance_stats.csv` capturing execution time, memory usage, and accuracy metrics
- `gantt_chart.png`, `conflict_heatmap.png`, and `algorithm_performance.png` visualizing schedules, conflicts, and algorithm performance trends

## Testing

Run the automated tests with:

```
python -m pytest
```
