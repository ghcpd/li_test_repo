import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from schedule_conflict_detector import (
    detect_conflicts_brute_force,
    detect_conflicts_interval_tree,
    detect_conflicts_sweep_line,
    read_schedule_csv,
)

DATA_DIR = Path(__file__).resolve().parent.parent


def test_conflict_detection_algorithms_consistent():
    events = read_schedule_csv(DATA_DIR / "test_schedule.csv")
    brute = detect_conflicts_brute_force(events)
    sweep = detect_conflicts_sweep_line(events)
    interval = detect_conflicts_interval_tree(events)

    brute_keys = set(brute.keys())
    assert brute_keys, "Brute force algorithm should detect at least one conflict"
    assert brute_keys == set(sweep.keys()) == set(interval.keys())


@pytest.mark.integration
def test_cli_generates_reports(tmp_path):
    output_dir = tmp_path / "reports"
    script_path = DATA_DIR / "schedule_conflict_detector.py"
    input_path = DATA_DIR / "test_schedule.csv"
    known_path = DATA_DIR / "known_conflicts.json"

    subprocess.check_call(
        [
            sys.executable,
            str(script_path),
            "--input",
            str(input_path),
            "--known",
            str(known_path),
            "--output",
            str(output_dir),
        ]
    )

    expected_files = {
        "conflict_report.csv",
        "conflict_report.txt",
        "validation_report.csv",
        "performance_report.csv",
        "gantt_chart.png",
        "conflict_heatmap.png",
        "algorithm_performance.png",
        "summary.json",
    }
    produced_files = {path.name for path in output_dir.iterdir()}
    assert expected_files.issubset(produced_files)

    with open(output_dir / "conflict_report.csv", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        assert {"conflict_id", "conflict_type", "severity"}.issubset(reader.fieldnames)
        first_row = next(reader)
        assert first_row["conflict_type"] in {"full overlap", "partial overlap", "containment"}

    with open(output_dir / "performance_report.csv", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        assert rows, "Performance report should contain algorithm statistics"
        assert {row["algorithm"] for row in rows} == {"Brute Force", "Sweep Line", "Interval Tree"}

    with open(output_dir / "summary.json", encoding="utf-8") as handle:
        summary = json.load(handle)
    assert summary["conflicts_detected"] > 0
    assert 0 <= summary["precision"] <= 1
    assert 0 <= summary["recall"] <= 1
    assert 0 <= summary["f1_score"] <= 1