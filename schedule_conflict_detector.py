#!/usr/bin/env python3
"""Multi-Person Schedule Conflict Detection System.

This command-line tool analyses schedules for multiple people and activities,
detects conflicts via multiple algorithms, validates the detections against
known ground truth data, and produces comprehensive analytical reports,
including visualisations.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
import tracemalloc
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from heapq import heappop, heappush
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

TIME_FORMAT = "%Y-%m-%d %H:%M"


@dataclass(frozen=True)
class ScheduleEvent:
    """Represents a single scheduled activity."""

    event_id: str
    person_id: str
    start: datetime
    end: datetime
    activity: str
    location: str
    metadata: Dict[str, str]


@dataclass(frozen=True)
class KnownConflict:
    """Represents a manually annotated conflict for validation purposes."""

    person_id: str
    activity_1: str
    activity_2: str
    start_1: datetime
    end_1: datetime
    start_2: datetime
    end_2: datetime


@dataclass
class ConflictDetail:
    """Encapsulates the details of a detected schedule conflict."""

    person_id: str
    event_1: ScheduleEvent
    event_2: ScheduleEvent
    overlap_start: datetime
    overlap_end: datetime
    conflict_type: str
    overlap_minutes: float
    severity: str
    conflict_id: Optional[int] = None

    def signature(self) -> Tuple[str, frozenset]:
        """Create a unique signature combining person and involved events."""

        event_signature = frozenset(
            {
                (self.event_1.activity, self.event_1.start, self.event_1.end),
                (self.event_2.activity, self.event_2.start, self.event_2.end),
            }
        )
        return self.person_id, event_signature

    def to_report_row(self) -> Dict[str, str]:
        """Convert conflict details into a flat row for reporting."""

        return {
            "conflict_id": str(self.conflict_id or ""),
            "persons": " | ".join(sorted({self.event_1.person_id, self.event_2.person_id})),
            "activity_names": f"{self.event_1.activity} | {self.event_2.activity}",
            "overlap_interval": f"{format_datetime(self.overlap_start)} - {format_datetime(self.overlap_end)}",
            "conflict_type": self.conflict_type,
            "overlap_minutes": f"{self.overlap_minutes:.2f}",
            "severity": self.severity,
            "event_1_start": format_datetime(self.event_1.start),
            "event_1_end": format_datetime(self.event_1.end),
            "event_2_start": format_datetime(self.event_2.start),
            "event_2_end": format_datetime(self.event_2.end),
            "location_1": self.event_1.location,
            "location_2": self.event_2.location,
        }


def format_datetime(value: datetime) -> str:
    """Format datetime objects consistently."""

    return value.strftime(TIME_FORMAT)


def parse_datetime(value: str) -> datetime:
    """Parse datetime strings in the expected format."""

    return datetime.strptime(value.strip(), TIME_FORMAT)


def read_schedule_csv(input_path: str) -> List[ScheduleEvent]:
    """Read schedule entries from a CSV file."""

    events: List[ScheduleEvent] = []
    required_fields = {"person_id", "start_time", "end_time", "activity_name", "location"}
    with open(input_path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = required_fields.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns in schedule CSV: {sorted(missing)}")
        for index, row in enumerate(reader):
            try:
                start = parse_datetime(row["start_time"])
                end = parse_datetime(row["end_time"])
            except Exception:
                continue
            if end <= start:
                continue
            event_id = f"E{index:05d}"
            metadata = {
                key: value
                for key, value in row.items()
                if key not in required_fields and value is not None and value != ""
            }
            events.append(
                ScheduleEvent(
                    event_id=event_id,
                    person_id=row["person_id"].strip(),
                    start=start,
                    end=end,
                    activity=row["activity_name"].strip(),
                    location=row["location"].strip(),
                    metadata=metadata,
                )
            )
    return events


def load_known_conflicts(path: str) -> List[KnownConflict]:
    """Load known conflicts from a JSON file."""

    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    known_conflicts: List[KnownConflict] = []
    for entry in data:
        start_1, end_1 = parse_range(entry.get("original_schedule", ""))
        start_2, end_2 = parse_range(entry.get("conflict_schedule", ""))
        known_conflicts.append(
            KnownConflict(
                person_id=entry.get("person_id", "").strip(),
                activity_1=entry.get("activity_1", "").strip(),
                activity_2=entry.get("activity_2", "").strip(),
                start_1=start_1,
                end_1=end_1,
                start_2=start_2,
                end_2=end_2,
            )
        )
    return known_conflicts


def parse_range(value: str) -> Tuple[datetime, datetime]:
    """Parse range strings of the form 'start - end'."""

    if " - " in value:
        start_str, end_str = [part.strip() for part in value.split(" - ", 1)]
    else:
        parts = [part.strip() for part in value.split("-") if part.strip()]
        if len(parts) < 2:
            raise ValueError(f"Invalid range value: {value}")
        midpoint = len(parts) // 2
        start_str = "-".join(parts[:midpoint])
        end_str = "-".join(parts[midpoint:])
    return parse_datetime(start_str), parse_datetime(end_str)


def calculate_overlap(event_1: ScheduleEvent, event_2: ScheduleEvent) -> Optional[Tuple[datetime, datetime]]:
    """Calculate the overlapping interval between two events."""

    overlap_start = max(event_1.start, event_2.start)
    overlap_end = min(event_1.end, event_2.end)
    if overlap_start >= overlap_end:
        return None
    return overlap_start, overlap_end


def determine_conflict_type(event_1: ScheduleEvent, event_2: ScheduleEvent) -> str:
    """Classify the type of conflict."""

    if event_1.start == event_2.start and event_1.end == event_2.end:
        return "full overlap"
    if (event_1.start <= event_2.start and event_1.end >= event_2.end) or (
        event_2.start <= event_1.start and event_2.end >= event_1.end
    ):
        return "containment"
    return "partial overlap"


def derive_severity(overlap_minutes: float) -> str:
    """Assign a severity rating based on overlap duration."""

    if overlap_minutes >= 60:
        return "High"
    if overlap_minutes >= 30:
        return "Medium"
    return "Low"


def build_conflict(event_1: ScheduleEvent, event_2: ScheduleEvent) -> Optional[ConflictDetail]:
    """Create a conflict detail object if two events overlap."""

    overlap = calculate_overlap(event_1, event_2)
    if overlap is None:
        return None
    overlap_start, overlap_end = overlap
    overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60.0
    conflict_type = determine_conflict_type(event_1, event_2)
    severity = derive_severity(overlap_minutes)
    return ConflictDetail(
        person_id=event_1.person_id,
        event_1=event_1,
        event_2=event_2,
        overlap_start=overlap_start,
        overlap_end=overlap_end,
        conflict_type=conflict_type,
        overlap_minutes=overlap_minutes,
        severity=severity,
    )


def grouped_events(events: Iterable[ScheduleEvent]) -> Dict[str, List[ScheduleEvent]]:
    """Group events by their associated person."""

    groups: Dict[str, List[ScheduleEvent]] = defaultdict(list)
    for event in events:
        groups[event.person_id].append(event)
    for collection in groups.values():
        collection.sort(key=lambda entry: entry.start)
    return groups


def detect_conflicts_brute_force(events: Iterable[ScheduleEvent]) -> Dict[Tuple[str, str], ConflictDetail]:
    """Detect conflicts using the brute force algorithm (O(n^2))."""

    conflicts: Dict[Tuple[str, str], ConflictDetail] = {}
    for person, person_events in grouped_events(events).items():
        count = len(person_events)
        for idx in range(count):
            for inner in range(idx + 1, count):
                event_1 = person_events[idx]
                event_2 = person_events[inner]
                conflict = build_conflict(event_1, event_2)
                if conflict is not None:
                    key = tuple(sorted((event_1.event_id, event_2.event_id)))
                    conflicts[key] = conflict
    return conflicts


def detect_conflicts_sweep_line(events: Iterable[ScheduleEvent]) -> Dict[Tuple[str, str], ConflictDetail]:
    """Detect conflicts using a sweep line algorithm (O(n log n))."""

    conflicts: Dict[Tuple[str, str], ConflictDetail] = {}
    for person, person_events in grouped_events(events).items():
        active: List[Tuple[datetime, str, ScheduleEvent]] = []
        for event in person_events:
            while active and active[0][0] <= event.start:
                heappop(active)
            for _, _, active_event in active:
                conflict = build_conflict(active_event, event)
                if conflict is not None:
                    key = tuple(sorted((active_event.event_id, event.event_id)))
                    conflicts[key] = conflict
            heappush(active, (event.end, event.event_id, event))
    return conflicts


class IntervalTreeNode:
    """A node within an interval tree used for conflict detection."""

    __slots__ = ("event", "max_end", "left", "right")

    def __init__(self, event: ScheduleEvent) -> None:
        self.event = event
        self.max_end = event.end
        self.left: Optional["IntervalTreeNode"] = None
        self.right: Optional["IntervalTreeNode"] = None


def interval_tree_insert(root: Optional[IntervalTreeNode], event: ScheduleEvent) -> IntervalTreeNode:
    """Insert an event into the interval tree and return the root."""

    if root is None:
        return IntervalTreeNode(event)
    if event.start < root.event.start:
        root.left = interval_tree_insert(root.left, event)
    else:
        root.right = interval_tree_insert(root.right, event)
    if root.max_end < event.end:
        root.max_end = event.end
    return root


def interval_tree_query(
    root: Optional[IntervalTreeNode],
    event: ScheduleEvent,
    conflicts: Dict[Tuple[str, str], ConflictDetail],
) -> None:
    """Query the tree for overlaps with the provided event."""

    if root is None:
        return
    if root.event.end > event.start and root.event.start < event.end:
        conflict = build_conflict(root.event, event)
        if conflict is not None:
            key = tuple(sorted((root.event.event_id, event.event_id)))
            conflicts[key] = conflict
    if root.left is not None and root.left.max_end > event.start:
        interval_tree_query(root.left, event, conflicts)
    if root.right is not None and root.event.start < event.end:
        interval_tree_query(root.right, event, conflicts)


def detect_conflicts_interval_tree(events: Iterable[ScheduleEvent]) -> Dict[Tuple[str, str], ConflictDetail]:
    """Detect conflicts using an interval tree (O(n log n))."""

    conflicts: Dict[Tuple[str, str], ConflictDetail] = {}
    for person, person_events in grouped_events(events).items():
        root: Optional[IntervalTreeNode] = None
        for event in person_events:
            if root is not None:
                interval_tree_query(root, event, conflicts)
            root = interval_tree_insert(root, event)
    return conflicts


def run_algorithm(
    func: Callable[[Iterable[ScheduleEvent]], Dict[Tuple[str, str], ConflictDetail]],
    events: Iterable[ScheduleEvent],
) -> Tuple[Dict[Tuple[str, str], ConflictDetail], float, float]:
    """Execute an algorithm and return results along with performance metrics."""

    tracemalloc.start()
    start_time = time.perf_counter()
    conflicts = func(events)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_kb = peak / 1024.0
    return conflicts, elapsed_ms, peak_kb


def ensure_consistent_results(conflict_maps: List[Dict[Tuple[str, str], ConflictDetail]]) -> None:
    """Verify that all algorithms produced identical conflict sets."""

    if not conflict_maps:
        return
    baseline_keys = set(conflict_maps[0].keys())
    for index, conflict_map in enumerate(conflict_maps[1:], start=1):
        if set(conflict_map.keys()) != baseline_keys:
            raise RuntimeError(
                "Conflict detection algorithms produced inconsistent results"
                f" between baseline and algorithm #{index + 1}."
            )


def assign_conflict_ids(conflict_map: Dict[Tuple[str, str], ConflictDetail]) -> List[ConflictDetail]:
    """Assign conflict identifiers and sort conflicts chronologically."""

    conflicts = list(conflict_map.values())
    conflicts.sort(key=lambda item: (item.event_1.person_id, item.overlap_start, item.event_1.start))
    for index, conflict in enumerate(conflicts, start=1):
        conflict.conflict_id = index
    return conflicts


def evaluate_conflicts(
    conflicts: List[ConflictDetail], known_conflicts: List[KnownConflict]
) -> Tuple[List[Dict[str, str]], Dict[str, float]]:
    """Compare detected conflicts against known ground truth and compute metrics."""

    signature_map: Dict[Tuple[str, frozenset], ConflictDetail] = {}
    for conflict in conflicts:
        signature_map[conflict.signature()] = conflict

    matched_signatures: set = set()
    validation_rows: List[Dict[str, str]] = []
    true_positive = 0

    for known in known_conflicts:
        known_signature = (
            known.person_id,
            frozenset(
                {
                    (known.activity_1, known.start_1, known.end_1),
                    (known.activity_2, known.start_2, known.end_2),
                }
            ),
        )
        conflict = signature_map.get(known_signature)
        if conflict is not None:
            matched_signatures.add(known_signature)
            true_positive += 1
            validation_rows.append(
                {
                    "status": "True Positive",
                    "person_id": known.person_id,
                    "expected_activity_1": known.activity_1,
                    "expected_start_1": format_datetime(known.start_1),
                    "expected_end_1": format_datetime(known.end_1),
                    "expected_activity_2": known.activity_2,
                    "expected_start_2": format_datetime(known.start_2),
                    "expected_end_2": format_datetime(known.end_2),
                    "detected_conflict_id": str(conflict.conflict_id or ""),
                    "detected_activity_1": conflict.event_1.activity,
                    "detected_start_1": format_datetime(conflict.event_1.start),
                    "detected_end_1": format_datetime(conflict.event_1.end),
                    "detected_activity_2": conflict.event_2.activity,
                    "detected_start_2": format_datetime(conflict.event_2.start),
                    "detected_end_2": format_datetime(conflict.event_2.end),
                    "overlap_start": format_datetime(conflict.overlap_start),
                    "overlap_end": format_datetime(conflict.overlap_end),
                    "conflict_type": conflict.conflict_type,
                    "overlap_minutes": f"{conflict.overlap_minutes:.2f}",
                    "severity": conflict.severity,
                }
            )
        else:
            validation_rows.append(
                {
                    "status": "False Negative",
                    "person_id": known.person_id,
                    "expected_activity_1": known.activity_1,
                    "expected_start_1": format_datetime(known.start_1),
                    "expected_end_1": format_datetime(known.end_1),
                    "expected_activity_2": known.activity_2,
                    "expected_start_2": format_datetime(known.start_2),
                    "expected_end_2": format_datetime(known.end_2),
                    "detected_conflict_id": "",
                    "detected_activity_1": "",
                    "detected_start_1": "",
                    "detected_end_1": "",
                    "detected_activity_2": "",
                    "detected_start_2": "",
                    "detected_end_2": "",
                    "overlap_start": "",
                    "overlap_end": "",
                    "conflict_type": "",
                    "overlap_minutes": "",
                    "severity": "",
                }
            )

    for signature, conflict in signature_map.items():
        if signature in matched_signatures:
            continue
        validation_rows.append(
            {
                "status": "False Positive",
                "person_id": conflict.person_id,
                "expected_activity_1": "",
                "expected_start_1": "",
                "expected_end_1": "",
                "expected_activity_2": "",
                "expected_start_2": "",
                "expected_end_2": "",
                "detected_conflict_id": str(conflict.conflict_id or ""),
                "detected_activity_1": conflict.event_1.activity,
                "detected_start_1": format_datetime(conflict.event_1.start),
                "detected_end_1": format_datetime(conflict.event_1.end),
                "detected_activity_2": conflict.event_2.activity,
                "detected_start_2": format_datetime(conflict.event_2.start),
                "detected_end_2": format_datetime(conflict.event_2.end),
                "overlap_start": format_datetime(conflict.overlap_start),
                "overlap_end": format_datetime(conflict.overlap_end),
                "conflict_type": conflict.conflict_type,
                "overlap_minutes": f"{conflict.overlap_minutes:.2f}",
                "severity": conflict.severity,
            }
        )

    total_predictions = len(conflicts)
    false_positive = max(0, total_predictions - true_positive)
    false_negative = max(0, len(known_conflicts) - true_positive)

    precision = true_positive / total_predictions if total_predictions else 0.0
    recall = true_positive / len(known_conflicts) if known_conflicts else 0.0
    denominator = true_positive + false_positive + false_negative
    accuracy = true_positive / denominator if denominator else 1.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0

    metrics = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
    }

    return validation_rows, metrics


def write_conflict_report(conflicts: List[ConflictDetail], output_dir: str) -> None:
    """Write the conflict report to CSV and plain text formats."""

    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "conflict_report.csv")
    text_path = os.path.join(output_dir, "conflict_report.txt")

    fieldnames = [
        "conflict_id",
        "persons",
        "activity_names",
        "overlap_interval",
        "conflict_type",
        "overlap_minutes",
        "severity",
        "event_1_start",
        "event_1_end",
        "event_2_start",
        "event_2_end",
        "location_1",
        "location_2",
    ]

    with open(csv_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for conflict in conflicts:
            writer.writerow(conflict.to_report_row())

    with open(text_path, "w", encoding="utf-8") as text_file:
        for conflict in conflicts:
            text_file.write(
                (
                    f"Conflict {conflict.conflict_id}: Persons={conflict.person_id}, "
                    f"Activities={conflict.event_1.activity} & {conflict.event_2.activity}, "
                    f"Overlap={format_datetime(conflict.overlap_start)} - {format_datetime(conflict.overlap_end)}, "
                    f"Type={conflict.conflict_type}, Duration={conflict.overlap_minutes:.2f} minutes, "
                    f"Severity={conflict.severity}\n"
                )
            )


def write_validation_report(rows: List[Dict[str, str]], output_dir: str) -> None:
    """Write the validation report to CSV."""

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "validation_report.csv")
    fieldnames = [
        "status",
        "person_id",
        "expected_activity_1",
        "expected_start_1",
        "expected_end_1",
        "expected_activity_2",
        "expected_start_2",
        "expected_end_2",
        "detected_conflict_id",
        "detected_activity_1",
        "detected_start_1",
        "detected_end_1",
        "detected_activity_2",
        "detected_start_2",
        "detected_end_2",
        "overlap_start",
        "overlap_end",
        "conflict_type",
        "overlap_minutes",
        "severity",
    ]

    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_performance_report(
    statistics: List[Tuple[str, float, float]],
    metrics: Dict[str, float],
    output_dir: str,
) -> None:
    """Write the performance statistics to a CSV file."""

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "performance_report.csv")
    fieldnames = [
        "algorithm",
        "execution_time_ms",
        "peak_memory_kb",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
    ]

    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for name, execution_time_ms, peak_memory_kb in statistics:
            writer.writerow(
                {
                    "algorithm": name,
                    "execution_time_ms": f"{execution_time_ms:.3f}",
                    "peak_memory_kb": f"{peak_memory_kb:.3f}",
                    "accuracy": f"{metrics['accuracy']:.3f}",
                    "precision": f"{metrics['precision']:.3f}",
                    "recall": f"{metrics['recall']:.3f}",
                    "f1_score": f"{metrics['f1_score']:.3f}",
                }
            )


def generate_gantt_chart(events: Iterable[ScheduleEvent], conflicts: List[ConflictDetail], output_dir: str) -> None:
    """Generate a Gantt chart visualising schedules and conflicts per person."""

    events_by_person = grouped_events(events)
    persons = sorted(events_by_person.keys())

    if not persons:
        return

    fig_height = max(6.0, len(persons) * 0.4)
    fig, ax = plt.subplots(figsize=(15, fig_height))

    y_positions = {person: index * 10 for index, person in enumerate(persons)}

    for person, person_events in events_by_person.items():
        base_y = y_positions[person]
        for event in person_events:
            start_num = mdates.date2num(event.start)
            duration = (event.end - event.start).total_seconds() / 86400.0
            ax.broken_barh(
                [(start_num, duration)],
                (base_y, 8),
                facecolors="#1f77b4",
                alpha=0.6,
            )

    for conflict in conflicts:
        base_y = y_positions.get(conflict.person_id, 0)
        start_num = mdates.date2num(conflict.overlap_start)
        duration = (conflict.overlap_end - conflict.overlap_start).total_seconds() / 86400.0
        ax.broken_barh(
            [(start_num, duration)],
            (base_y, 8),
            facecolors="#d62728",
            alpha=0.9,
        )

    ax.set_yticks([position + 4 for position in y_positions.values()])
    ax.set_yticklabels(persons)
    ax.set_xlabel("Time")
    ax.set_ylabel("Person")
    ax.set_title("Schedule Gantt Chart with Conflicts Highlighted")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    chart_path = os.path.join(output_dir, "gantt_chart.png")
    plt.savefig(chart_path, dpi=200)
    plt.close(fig)


def generate_conflict_heatmap(conflicts: List[ConflictDetail], output_dir: str) -> None:
    """Generate a heatmap of conflict frequencies by person and date."""

    if not conflicts:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, "No conflicts detected", ha="center", va="center")
        ax.axis("off")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "conflict_heatmap.png"), dpi=200)
        plt.close(fig)
        return

    persons = sorted({conflict.person_id for conflict in conflicts})
    dates = sorted({conflict.overlap_start.date() for conflict in conflicts})
    if not persons or not dates:
        return

    person_index = {person: idx for idx, person in enumerate(persons)}
    date_index = {date: idx for idx, date in enumerate(dates)}

    heatmap = [[0 for _ in dates] for _ in persons]
    for conflict in conflicts:
        row = person_index[conflict.person_id]
        column = date_index[conflict.overlap_start.date()]
        heatmap[row][column] += 1

    fig_width = max(6.0, len(dates) * 0.6)
    fig_height = max(4.0, len(persons) * 0.4)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    cax = ax.imshow(heatmap, aspect="auto", cmap="Reds")
    fig.colorbar(cax, ax=ax, label="Conflict Count")
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels([date.strftime("%m-%d") for date in dates], rotation=45, ha="right")
    ax.set_yticks(range(len(persons)))
    ax.set_yticklabels(persons)
    ax.set_xlabel("Date")
    ax.set_ylabel("Person")
    ax.set_title("Conflict Frequency Heatmap")
    plt.tight_layout()

    plt.savefig(os.path.join(output_dir, "conflict_heatmap.png"), dpi=200)
    plt.close(fig)


def generate_performance_chart(statistics: List[Tuple[str, float, float]], output_dir: str) -> None:
    """Generate charts comparing algorithm execution time and memory usage."""

    if not statistics:
        return

    algorithms = [entry[0] for entry in statistics]
    times = [entry[1] for entry in statistics]
    memories = [entry[2] for entry in statistics]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].bar(algorithms, times, color="#1f77b4")
    axes[0].set_title("Execution Time by Algorithm")
    axes[0].set_ylabel("Time (ms)")
    axes[0].tick_params(axis="x", rotation=45)

    axes[1].bar(algorithms, memories, color="#2ca02c")
    axes[1].set_title("Peak Memory Usage by Algorithm")
    axes[1].set_ylabel("Memory (KB)")
    axes[1].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "algorithm_performance.png"), dpi=200)
    plt.close(fig)


def run_pipeline(args: argparse.Namespace) -> None:
    """Execute the entire schedule conflict analysis pipeline."""

    events = read_schedule_csv(args.input)
    known_conflicts = load_known_conflicts(args.known) if args.known else []

    algorithms: List[Tuple[str, Callable[[Iterable[ScheduleEvent]], Dict[Tuple[str, str], ConflictDetail]]]] = [
        ("Brute Force", detect_conflicts_brute_force),
        ("Sweep Line", detect_conflicts_sweep_line),
        ("Interval Tree", detect_conflicts_interval_tree),
    ]

    algorithm_outputs: List[Tuple[str, Dict[Tuple[str, str], ConflictDetail], float, float]] = []
    for name, func in algorithms:
        conflicts, elapsed_ms, peak_kb = run_algorithm(func, events)
        algorithm_outputs.append((name, conflicts, elapsed_ms, peak_kb))

    conflict_maps = [entry[1] for entry in algorithm_outputs]
    ensure_consistent_results(conflict_maps)

    canonical_conflicts_map = conflict_maps[0]
    conflicts = assign_conflict_ids(canonical_conflicts_map)

    validation_rows, metrics = evaluate_conflicts(conflicts, known_conflicts)

    write_conflict_report(conflicts, args.output)
    write_validation_report(validation_rows, args.output)

    statistics = [(name, elapsed, memory) for name, _, elapsed, memory in algorithm_outputs]
    write_performance_report(statistics, metrics, args.output)

    generate_gantt_chart(events, conflicts, args.output)
    generate_conflict_heatmap(conflicts, args.output)
    generate_performance_chart(statistics, args.output)

    summary = {
        "total_events": len(events),
        "conflicts_detected": len(conflicts),
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1_score": metrics["f1_score"],
    }
    summary_path = os.path.join(args.output, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Multi-Person Schedule Conflict Detection System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="Path to the schedule CSV input file")
    parser.add_argument(
        "--known",
        required=False,
        default="",
        help="Path to the known conflicts JSON file",
    )
    parser.add_argument("--output", required=True, help="Output directory for generated reports")
    return parser


def main() -> None:
    """Entry point for command-line execution."""

    parser = build_argument_parser()
    args = parser.parse_args()
    args.input = os.path.abspath(args.input)
    args.known = os.path.abspath(args.known) if args.known else ""
    args.output = os.path.abspath(args.output)
    os.makedirs(args.output, exist_ok=True)

    run_pipeline(args)


if __name__ == "__main__":
    main()
