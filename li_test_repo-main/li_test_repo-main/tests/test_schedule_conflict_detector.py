import csv
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from schedule_conflict_detector import (
    build_events_by_person,
    detect_conflicts_brute_force,
    detect_conflicts_interval_tree,
    detect_conflicts_sweep_line,
    load_known_conflicts,
    load_schedule,
    run_detection_pipeline,
)


@pytest.fixture()
def sample_paths() -> dict:
    base = Path(__file__).resolve().parent
    return {
        "schedule": base / "sample_schedule.csv",
        "known": base / "sample_known_conflicts.json",
    }


def _conflict_keys(conflicts):
    return {conflict.canonical_key() for conflict in conflicts}


def test_algorithms_detect_consistent_conflicts(sample_paths):
    entries = load_schedule(str(sample_paths["schedule"]))
    events_by_person = build_events_by_person(entries)

    conflicts_brute = detect_conflicts_brute_force(events_by_person)
    conflicts_sweep = detect_conflicts_sweep_line(events_by_person)
    conflicts_tree = detect_conflicts_interval_tree(events_by_person)

    assert len(conflicts_brute) == 2
    assert _conflict_keys(conflicts_brute) == _conflict_keys(conflicts_sweep) == _conflict_keys(conflicts_tree)

    conflicts_by_person = {tuple(sorted(conflict.person_ids)): conflict for conflict in conflicts_brute}
    p001_conflict = conflicts_by_person[("P001", "P001")]
    assert p001_conflict.overlap_minutes == pytest.approx(30.0)
    assert p001_conflict.conflict_type == "partial overlap"
    assert p001_conflict.severity == "Medium"

    p002_conflict = conflicts_by_person[("P002", "P002")]
    assert p002_conflict.overlap_minutes == pytest.approx(15.0)
    assert p002_conflict.severity == "Low"


def test_cli_generates_reports(tmp_path, sample_paths):
    output_dir = tmp_path / "reports"
    script_path = Path(__file__).resolve().parents[1] / "schedule_conflict_detector.py"

    subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--input",
            str(sample_paths["schedule"]),
            "--known",
            str(sample_paths["known"]),
            "--output",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    expected_files = {
        "conflicts_brute_force.csv",
        "conflicts_sweep_line.csv",
        "conflicts_interval_tree.csv",
        "validation_report.csv",
        "performance_summary.csv",
        "gantt_chart.png",
        "conflict_heatmap.png",
        "algorithm_performance.png",
    }

    generated_files = {path.name for path in output_dir.iterdir()}
    assert expected_files.issubset(generated_files)

    performance_path = output_dir / "performance_summary.csv"
    with performance_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3
    assert all(float(row["precision"]) == pytest.approx(1.0) for row in rows)
    assert all(float(row["recall"]) == pytest.approx(1.0) for row in rows)

    validation_path = output_dir / "validation_report.csv"
    with validation_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        statuses = [row["status"] for row in reader if row["status"]]

    assert "false_negative" not in statuses
    assert statuses.count("true_positive") >= 6  # 3 algorithms * 2 conflicts


def test_pipeline_returns_metrics(sample_paths, tmp_path):
    result = run_detection_pipeline(
        str(sample_paths["schedule"]),
        str(sample_paths["known"]),
        str(tmp_path / "pipeline_reports"),
    )

    metrics = result["metrics"]
    assert set(metrics.keys()) == {"brute_force", "sweep_line", "interval_tree"}
    for values in metrics.values():
        precision = values[3]
        recall = values[4]
        f1_score = values[5]
        assert precision == pytest.approx(1.0)
        assert recall == pytest.approx(1.0)
        assert f1_score == pytest.approx(1.0)