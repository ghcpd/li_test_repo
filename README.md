# Multi-Person Schedule Conflict Detection System

This repository contains a reproducible command-line tool for auditing large
multi-person schedules and generating visual and statistical analyses of
conflicts.

## Usage

```bash
python schedule_conflict_detector.py \
  --input test_schedule.csv \
  --known known_conflicts.json \
  --output output/
```

The tool will:

- Run three conflict detection algorithms (Brute Force, Sweep Line, Interval Tree)
- Validate detected conflicts against the `known_conflicts.json` ground truth
- Generate reports and visualisations in the requested output directory

## Generated Reports

* `conflict_report.csv` and `conflict_report.txt`: Detailed per-conflict records
  including the overlap window, participants, and severity metadata.
* `validation_report.csv`: Row-by-row comparison of detected versus expected
  conflicts and their correctness classification.
* `performance_report.csv`: Execution time, memory footprint, and accuracy
  metrics across algorithms.
* `gantt_chart.png`: A timeline of all activities with overlaps highlighted in
  red.
* `conflict_heatmap.png`: Heatmap of conflict counts by person and calendar day.
* `algorithm_performance.png`: Side-by-side bar charts of runtime and peak
  memory utilisation for each algorithm.
* `summary.json`: Key summary statistics for quick inspection.

## Dependencies

The following Python packages are required:

- `matplotlib` (for generating charts)

Install them with:

```bash
pip install matplotlib
```

## Testing

Automated coverage is provided through `pytest`.

```bash
python -m pytest
```
