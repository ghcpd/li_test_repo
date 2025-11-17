from datetime import datetime

import pytest

from schedule_conflict_detector import (
    AlgorithmResult,
    ScheduleEntry,
    aggregate_conflicts,
    detect_conflicts_brute_force,
    detect_conflicts_interval_tree,
    detect_conflicts_sweep_line,
    evaluate_conflicts,
    known_conflict_keys,
)


@pytest.fixture
def sample_entries():
    return [
        ScheduleEntry(
            index=0,
            person_id="P1",
            activity_name="Meeting",
            location="Room A",
            start_time=datetime(2025, 1, 1, 9, 0),
            end_time=datetime(2025, 1, 1, 10, 0),
        ),
        ScheduleEntry(
            index=1,
            person_id="P1",
            activity_name="Review",
            location="Room A",
            start_time=datetime(2025, 1, 1, 9, 30),
            end_time=datetime(2025, 1, 1, 11, 0),
        ),
        ScheduleEntry(
            index=2,
            person_id="P1",
            activity_name="Break",
            location="Cafeteria",
            start_time=datetime(2025, 1, 1, 12, 0),
            end_time=datetime(2025, 1, 1, 13, 0),
        ),
        ScheduleEntry(
            index=3,
            person_id="P2",
            activity_name="Review",
            location="Room B",
            start_time=datetime(2025, 1, 1, 9, 0),
            end_time=datetime(2025, 1, 1, 9, 30),
        ),
    ]


@pytest.fixture
def ground_truth():
    return known_conflict_keys(
        [
            {
                "person_id": "P1",
                "original_schedule": "2025-01-01 09:00 - 2025-01-01 10:00",
                "conflict_schedule": "2025-01-01 09:30 - 2025-01-01 11:00",
                "activity_1": "Meeting",
                "activity_2": "Review",
            }
        ]
    )


@pytest.mark.parametrize(
    "detector",
    [
        detect_conflicts_brute_force,
        detect_conflicts_sweep_line,
        detect_conflicts_interval_tree,
    ],
)
def test_conflict_detection_algorithms(detector, sample_entries):
    conflicts = detector(sample_entries)
    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.overlap_minutes == 30
    assert conflict.conflict_type == "partial overlap"
    assert conflict.severity == "Low"
    assert conflict.entry_a.person_id == conflict.entry_b.person_id == "P1"


def test_evaluate_conflicts(ground_truth, sample_entries):
    conflicts = detect_conflicts_brute_force(sample_entries)
    precision, recall, f1, accuracy, details = evaluate_conflicts(conflicts, ground_truth)
    assert pytest.approx(precision, rel=1e-6) == 1.0
    assert pytest.approx(recall, rel=1e-6) == 1.0
    assert pytest.approx(f1, rel=1e-6) == 1.0
    assert pytest.approx(accuracy, rel=1e-6) == 1.0
    assert details and details[0][1] == "TP"


def test_aggregate_conflicts(sample_entries):
    algorithms = [
        ("Brute Force", detect_conflicts_brute_force),
        ("Sweep Line", detect_conflicts_sweep_line),
        ("Interval Tree", detect_conflicts_interval_tree),
    ]
    results = []
    for name, detector in algorithms:
        conflicts = detector(sample_entries)
        results.append(
            AlgorithmResult(
                name=name,
                conflicts=conflicts,
                time_ms=0.0,
                peak_memory_kib=0.0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
                accuracy=0.0,
            )
        )
    aggregated = aggregate_conflicts(results)
    assert len(aggregated) == 1
    conflict = aggregated[0]
    assert conflict["person_ids"] == "P1"
    assert conflict["conflict_type"] == "partial overlap"
    detected_by = set(map(str.strip, conflict["algorithms"].split(",")))
    assert detected_by == {name for name, _ in algorithms}