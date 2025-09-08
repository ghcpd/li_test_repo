# li_test_repo

Schedule Conflict Detection CLI

Usage:

- Install dependencies (optional for visualization):
  pip install -r requirements.txt

- Run conflict detection:
  python schedule_conflict_detector.py --input test_schedule.csv --known known_conflicts.json --output report/

Outputs will include:
- conflict_report_[algorithm].csv
- validation_report_[algorithm].csv
- performance.csv
- If matplotlib is installed: gantt_chart.png, conflict_heatmap.png, performance.png
