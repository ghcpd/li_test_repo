import csv
import json
import subprocess
import sys
from pathlib import Path


def test_cli_generates_reports(tmp_path):
    repo_root = Path(__file__).resolve().parent
    schedule_path = repo_root / "test_schedule.csv"
    known_conflicts_path = repo_root / "known_conflicts.json"
    output_dir = tmp_path / "reports"

    cmd = [
        sys.executable,
        str(repo_root / "schedule_conflict_detector.py"),
        "--input",
        str(schedule_path),
        "--known",
        str(known_conflicts_path),
        "--output",
        str(output_dir),
    ]
    result = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)

    expected_files = [
        "conflict_report.csv",
        "conflict_report.txt",
        "validation_report.csv",
        "performance_report.csv",
        "metrics_summary.json",
        "gantt_chart.png",
        "conflict_heatmap.png",
        "algorithm_performance.png",
    ]
    for filename in expected_files:
        file_path = output_dir / filename
        assert file_path.exists(), f"Missing output file {filename}"
        assert file_path.stat().st_size > 0, f"Output file {filename} is empty"

    with open(output_dir / "performance_report.csv", "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        algorithms = {row["Algorithm"] for row in reader}
    assert {"Brute Force", "Sweep Line", "Interval Tree"} <= algorithms

    with open(output_dir / "metrics_summary.json", "r", encoding="utf-8") as handle:
        metrics = json.load(handle)
    assert "precision" in metrics and "recall" in metrics and "f1_score" in metrics
    assert metrics.get("conflict_count", 0) >= 0