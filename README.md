# li_test_repo

## Multi-Person Schedule Conflict Detection System

This repository now includes a command-line tool for detecting scheduling conflicts
across multiple people and activities. The tool analyses a schedule CSV, runs
three conflict detection algorithms (brute force, sweep line, interval tree),
validates the detected conflicts against a ground-truth JSON file, and generates
comprehensive reports and visualisations.

### Usage

```bash
python schedule_conflict_detector.py --input test_schedule.csv \
    --known known_conflicts.json --output report/
```

The output directory will contain:

- `conflict_report.csv` and `conflict_report.txt` – human-readable conflict listings.
- `validation_report.csv` – comparison against the known conflicts.
- `performance_report.csv` – execution time, memory usage, and accuracy metrics per algorithm.
- `metrics_summary.json` – aggregated precision, recall, and F1 statistics.
- `gantt_chart.png`, `conflict_heatmap.png`, and `algorithm_performance.png` – visual summaries.

Install required Python packages before running the tool:

```bash
python -m pip install matplotlib pytest
```
