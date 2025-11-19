import csv
import os

import pytest

from schedule_conflict_detector import (
    conflict_to_tuple,
    detect_conflicts_bruteforce,
    detect_conflicts_interval_tree,
    detect_conflicts_sweep_line,
    load_schedule,
    run_conflict_detection,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SCHEDULE_FILE = os.path.join(DATA_DIR, "sample_schedule.csv")
KNOWN_CONFLICTS_FILE = os.path.join(DATA_DIR, "sample_known_conflicts.json")


def _collect_keys(conflicts):
    return {conflict_to_tuple(conflict) for conflict in conflicts}


def test_algorithms_return_identical_conflicts():
    entries = load_schedule(SCHEDULE_FILE)
    brute = _collect_keys(detect_conflicts_bruteforce(entries))
    sweep = _collect_keys(detect_conflicts_sweep_line(entries))
    tree = _collect_keys(detect_conflicts_interval_tree(entries))
    assert brute == sweep == tree
    assert len(brute) == 2


def test_run_conflict_detection_generates_reports(tmp_path):
    output_dir = tmp_path / "reports"
    summary = run_conflict_detection(SCHEDULE_FILE, KNOWN_CONFLICTS_FILE, str(output_dir))
    expected_files = [
        "conflict_report.csv",
        "performance_metrics.csv",
        "validation_report.csv",
        "schedule_gantt.png",
        "conflict_heatmap.png",
        "algorithm_performance.png",
    ]
    for filename in expected_files:
        assert (output_dir / filename).exists(), f"Missing {filename}"
    assert pytest.approx(1.0, rel=1e-4) == summary["precision"]
    assert pytest.approx(1.0, rel=1e-4) == summary["recall"]
    assert pytest.approx(1.0, rel=1e-4) == summary["f1"]
    with open(output_dir / "performance_metrics.csv", "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert len(rows) == 3
    with open(output_dir / "conflict_report.csv", "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        conflict_rows = list(reader)
    assert len(conflict_rows) == 2