import csv
import json
import os
import sys
from pathlib import Path

import pytest

# Ensure the repository root is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from schedule_conflict_detector import (  # noqa: E402
    ScheduleEntry,
    detect_conflicts_brute_force,
    detect_conflicts_interval_tree,
    detect_conflicts_sweep_line,
    parse_datetime,
    run_pipeline,
)


def sample_entries():
    return [
        ScheduleEntry(
            person_id="P1",
            start_time=parse_datetime("2025-09-01 10:00"),
            end_time=parse_datetime("2025-09-01 11:00"),
            activity_name="Meeting",
            location="Room A",
            scenario="example",
        ),
        ScheduleEntry(
            person_id="P1",
            start_time=parse_datetime("2025-09-01 10:30"),
            end_time=parse_datetime("2025-09-01 11:30"),
            activity_name="Review",
            location="Room B",
            scenario="example",
        ),
        ScheduleEntry(
            person_id="P1",
            start_time=parse_datetime("2025-09-01 12:00"),
            end_time=parse_datetime("2025-09-01 13:00"),
            activity_name="Lunch",
            location="Cafeteria",
            scenario="example",
        ),
        ScheduleEntry(
            person_id="P2",
            start_time=parse_datetime("2025-09-01 10:15"),
            end_time=parse_datetime("2025-09-01 10:45"),
            activity_name="Sync",
            location="Room C",
            scenario="example",
        ),
        ScheduleEntry(
            person_id="P2",
            start_time=parse_datetime("2025-09-01 10:30"),
            end_time=parse_datetime("2025-09-01 11:00"),
            activity_name="Workshop",
            location="Room C",
            scenario="example",
        ),
    ]


def test_conflict_detection_consistency():
    entries = sample_entries()
    brute_force = detect_conflicts_brute_force(entries)
    sweep_line = detect_conflicts_sweep_line(entries)
    interval_tree = detect_conflicts_interval_tree(entries)

    assert len(brute_force) == len(sweep_line) == len(interval_tree) == 2

    expected_signatures = {
        brute_force[0].signature,
        brute_force[1].signature,
    }
    assert {record.signature for record in sweep_line} == expected_signatures
    assert {record.signature for record in interval_tree} == expected_signatures

    severities = {record.severity for record in brute_force}
    assert severities == {"Low", "Medium"}


def test_pipeline_generates_reports(tmp_path: Path):
    schedule_path = tmp_path / "schedules.csv"
    known_path = tmp_path / "known.json"
    output_dir = tmp_path / "output"

    rows = [
        [
            "person_id",
            "start_time",
            "end_time",
            "activity_name",
            "location",
            "scenario",
        ],
        [
            "P1",
            "2025-10-01 09:00",
            "2025-10-01 09:45",
            "Daily Standup",
            "Room A",
            "demo",
        ],
        [
            "P1",
            "2025-10-01 09:30",
            "2025-10-01 10:30",
            "Project Update",
            "Room B",
            "demo",
        ],
        [
            "P2",
            "2025-10-01 11:00",
            "2025-10-01 12:00",
            "Planning",
            "Room C",
            "demo",
        ],
        [
            "P2",
            "2025-10-01 11:20",
            "2025-10-01 11:45",
            "Client Call",
            "Room C",
            "demo",
        ],
    ]
    with open(schedule_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)

    known_conflicts = [
        {
            "person_id": "P1",
            "original_schedule": "2025-10-01 09:00 - 2025-10-01 09:45",
            "conflict_schedule": "2025-10-01 09:30 - 2025-10-01 10:30",
            "activity_1": "Daily Standup",
            "activity_2": "Project Update",
        },
        {
            "person_id": "P2",
            "original_schedule": "2025-10-01 11:00 - 2025-10-01 12:00",
            "conflict_schedule": "2025-10-01 11:20 - 2025-10-01 11:45",
            "activity_1": "Planning",
            "activity_2": "Client Call",
        },
    ]
    with open(known_path, "w", encoding="utf-8") as handle:
        json.dump(known_conflicts, handle)

    result = run_pipeline(str(schedule_path), str(known_path), str(output_dir))

    assert result["aggregated"]
    assert len(result["aggregated"]) == 2

    for algorithm_stats in result["algorithm_stats"].values():
        assert 0.0 <= algorithm_stats["precision"] <= 1.0
        assert 0.0 <= algorithm_stats["recall"] <= 1.0
        assert 0.0 <= algorithm_stats["f1_score"] <= 1.0
        assert algorithm_stats["time_ms"] >= 0.0
        assert algorithm_stats["memory_kb"] >= 0.0

    files = [
        "conflict_report.csv",
        "conflict_report.txt",
        "validation_report.csv",
        "performance_statistics.csv",
        "gantt_chart.png",
        "conflict_heatmap.png",
        "algorithm_performance.png",
    ]
    for filename in files:
        assert (output_dir / filename).exists(), f"Missing {filename}"

    with open(output_dir / "validation_report.csv", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        assert any(row["status"] == "True Positive" for row in rows)

    stats_path = output_dir / "performance_statistics.csv"
    with open(stats_path, encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        stats_rows = list(reader)
        assert {row["Algorithm"] for row in stats_rows} == {
            "Brute Force",
            "Sweep Line",
            "Interval Tree",
        }
        for row in stats_rows:
            assert float(row["Execution Time (ms)"]) >= 0.0
            assert float(row["Memory Usage (KB)"]) >= 0.0
            assert 0.0 <= float(row["Precision"]) <= 1.0
            assert 0.0 <= float(row["Recall"]) <= 1.0
            assert 0.0 <= float(row["F1 Score"]) <= 1.0
            assert 0.0 <= float(row["Accuracy"]) <= 1.0