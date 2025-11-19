"""Command-line utility for multi-person schedule conflict detection.

This module loads schedule data from CSV files, identifies double-booked
appointments using multiple algorithms, validates the detected conflicts
against a ground-truth JSON file and produces analytical reports together
with visualisations summarising the findings.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import tracemalloc
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

ISO_FORMAT = "%Y-%m-%d %H:%M"


@dataclass(frozen=True)
class ScheduleEntry:
    """Represents a single calendar entry."""

    entry_id: str
    person_id: str
    start_time: datetime
    end_time: datetime
    activity: str
    location: str
    scenario: str

    @property
    def duration(self) -> timedelta:
        return self.end_time - self.start_time


@dataclass
class ConflictRecord:
    """Stores the metadata for a detected conflict."""

    key: Tuple[str, str]
    person_id: str
    event_a: ScheduleEntry
    event_b: ScheduleEntry
    overlap_start: datetime
    overlap_end: datetime

    def overlap_minutes(self) -> float:
        return (self.overlap_end - self.overlap_start).total_seconds() / 60.0

    def conflict_type(self) -> str:
        a, b = self.event_a, self.event_b
        if a.start_time == b.start_time and a.end_time == b.end_time:
            return "full overlap"
        if (a.start_time <= b.start_time and a.end_time >= b.end_time) or (
            b.start_time <= a.start_time and b.end_time >= a.end_time
        ):
            return "containment"
        return "partial overlap"

    def severity(self) -> str:
        minutes = self.overlap_minutes()
        if minutes >= 60:
            return "High"
        if minutes >= 30:
            return "Medium"
        return "Low"


def parse_datetime(value: str) -> datetime:
    """Parse a datetime string in ISO format."""

    return datetime.strptime(value.strip(), ISO_FORMAT)


def load_schedule(csv_path: str) -> List[ScheduleEntry]:
    """Load schedule entries from the CSV file."""

    entries: List[ScheduleEntry] = []
    with open(csv_path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required_fields = {
            "person_id",
            "start_time",
            "end_time",
            "activity_name",
            "location",
        }
        missing = required_fields - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        scenario_present = "scenario" in (reader.fieldnames or [])
        for index, row in enumerate(reader):
            entries.append(
                ScheduleEntry(
                    entry_id=f"E{index:05d}",
                    person_id=row["person_id"].strip(),
                    start_time=parse_datetime(row["start_time"]),
                    end_time=parse_datetime(row["end_time"]),
                    activity=row["activity_name"].strip(),
                    location=row["location"].strip(),
                    scenario=row["scenario"].strip()
                    if scenario_present and row["scenario"]
                    else "",
                )
            )
    return entries


def load_known_conflicts(json_path: str) -> List[Dict[str, object]]:
    """Load ground-truth conflicts from JSON file."""

    with open(json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    formatted: List[Dict[str, object]] = []
    for row in data:
        original_start, original_end = [
            parse_datetime(part.strip())
            for part in row["original_schedule"].split(" - ")
        ]
        conflict_start, conflict_end = [
            parse_datetime(part.strip())
            for part in row["conflict_schedule"].split(" - ")
        ]
        formatted.append(
            {
                "person_id": row["person_id"],
                "activity_1": row["activity_1"],
                "activity_2": row["activity_2"],
                "event_a_start": original_start,
                "event_a_end": original_end,
                "event_b_start": conflict_start,
                "event_b_end": conflict_end,
            }
        )
    return formatted


def overlaps(a: ScheduleEntry, b: ScheduleEntry) -> Optional[Tuple[datetime, datetime]]:
    """Return the overlap interval between entries if they conflict."""

    if a.person_id != b.person_id:
        return None
    start = max(a.start_time, b.start_time)
    end = min(a.end_time, b.end_time)
    if start < end:
        return start, end
    return None


def _register_conflict(
    container: Dict[Tuple[str, str], ConflictRecord],
    entry_a: ScheduleEntry,
    entry_b: ScheduleEntry,
) -> None:
    key = tuple(sorted((entry_a.entry_id, entry_b.entry_id)))
    if key in container:
        return
    interval = overlaps(entry_a, entry_b)
    if not interval:
        return
    overlap_start, overlap_end = interval
    container[key] = ConflictRecord(
        key=key,
        person_id=entry_a.person_id,
        event_a=entry_a,
        event_b=entry_b,
        overlap_start=overlap_start,
        overlap_end=overlap_end,
    )


def detect_conflicts_bruteforce(entries: Sequence[ScheduleEntry]) -> List[ConflictRecord]:
    conflicts: Dict[Tuple[str, str], ConflictRecord] = {}
    for idx, entry in enumerate(entries):
        for sibling in entries[idx + 1 :]:
            _register_conflict(conflicts, entry, sibling)
    return list(conflicts.values())


def detect_conflicts_sweep_line(entries: Sequence[ScheduleEntry]) -> List[ConflictRecord]:
    conflicts: Dict[Tuple[str, str], ConflictRecord] = {}
    grouped: Dict[str, List[ScheduleEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.person_id].append(entry)
    for items in grouped.values():
        active: List[ScheduleEntry] = []
        for item in sorted(items, key=lambda e: e.start_time):
            active = [act for act in active if act.end_time > item.start_time]
            for act in active:
                _register_conflict(conflicts, item, act)
            active.append(item)
    return list(conflicts.values())


class IntervalNode:
    __slots__ = ("entry", "max_end", "left", "right")

    def __init__(self, entry: ScheduleEntry) -> None:
        self.entry = entry
        self.max_end = entry.end_time
        self.left: Optional["IntervalNode"] = None
        self.right: Optional["IntervalNode"] = None


class IntervalTree:
    def __init__(self) -> None:
        self.root: Optional[IntervalNode] = None

    def insert(
        self,
        entry: ScheduleEntry,
        callback: Callable[[ScheduleEntry, ScheduleEntry], None],
    ) -> None:
        self.root = self._insert(self.root, entry, callback)

    def _insert(
        self,
        node: Optional[IntervalNode],
        entry: ScheduleEntry,
        callback: Callable[[ScheduleEntry, ScheduleEntry], None],
    ) -> IntervalNode:
        if node is None:
            return IntervalNode(entry)
        if overlaps(node.entry, entry):
            callback(node.entry, entry)
        if node.left and node.left.max_end > entry.start_time:
            self._search(node.left, entry, callback)
        if node.right and node.entry.start_time <= entry.end_time:
            self._search(node.right, entry, callback)
        if entry.start_time < node.entry.start_time:
            node.left = self._insert(node.left, entry, callback)
        else:
            node.right = self._insert(node.right, entry, callback)
        left_max = node.left.max_end if node.left else node.entry.end_time
        right_max = node.right.max_end if node.right else node.entry.end_time
        node.max_end = max(node.entry.end_time, left_max, right_max)
        return node

    def _search(
        self,
        node: Optional[IntervalNode],
        entry: ScheduleEntry,
        callback: Callable[[ScheduleEntry, ScheduleEntry], None],
    ) -> None:
        if node is None:
            return
        if overlaps(node.entry, entry):
            callback(node.entry, entry)
        if node.left and node.left.max_end > entry.start_time:
            self._search(node.left, entry, callback)
        if node.right and node.entry.start_time <= entry.end_time:
            self._search(node.right, entry, callback)


def detect_conflicts_interval_tree(entries: Sequence[ScheduleEntry]) -> List[ConflictRecord]:
    conflicts: Dict[Tuple[str, str], ConflictRecord] = {}
    grouped: Dict[str, List[ScheduleEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.person_id].append(entry)
    for items in grouped.values():
        tree = IntervalTree()
        for item in sorted(items, key=lambda e: e.start_time):
            tree.insert(item, lambda a, b, c=conflicts: _register_conflict(c, a, b))
    return list(conflicts.values())


def conflict_to_tuple(conflict: ConflictRecord) -> Tuple:
    items = sorted([conflict.event_a, conflict.event_b], key=lambda e: (e.start_time, e.activity))
    a, b = items
    return (
        conflict.person_id,
        a.start_time,
        a.end_time,
        a.activity,
        b.start_time,
        b.end_time,
        b.activity,
    )


def known_conflict_to_tuple(row: Dict[str, object]) -> Tuple:
    return (
        row["person_id"],
        row["event_a_start"],
        row["event_a_end"],
        row["activity_1"],
        row["event_b_start"],
        row["event_b_end"],
        row["activity_2"],
    )


def evaluate_conflicts(
    detected: Sequence[ConflictRecord],
    known: Sequence[Dict[str, object]],
) -> Tuple[float, float, float, List[Dict[str, object]]]:
    detected_map = {conflict_to_tuple(c): c for c in detected}
    known_tuples = [known_conflict_to_tuple(row) for row in known]
    true_positives = 0
    validation_rows: List[Dict[str, object]] = []
    for original, row in zip(known_tuples, known):
        detected_conflict = detected_map.get(original)
        is_found = detected_conflict is not None
        validation_rows.append(
            {
                "person_id": original[0],
                "activity_1": original[3],
                "activity_2": original[6],
                "known_start": original[1].strftime(ISO_FORMAT),
                "known_end": original[2].strftime(ISO_FORMAT),
                "known_conflict_start": original[4].strftime(ISO_FORMAT),
                "known_conflict_end": original[5].strftime(ISO_FORMAT),
                "detected": is_found,
                "conflict_id": detected_conflict.key[0] + "-" + detected_conflict.key[1]
                if detected_conflict
                else "",
            }
        )
        if is_found:
            true_positives += 1
    false_positive_conflicts = [c for t, c in detected_map.items() if t not in known_tuples]
    precision = true_positives / max(1, len(detected_map))
    recall = true_positives / max(1, len(known_tuples))
    if precision + recall == 0:
        f1_score = 0.0
    else:
        f1_score = 2 * precision * recall / (precision + recall)
    if false_positive_conflicts:
        for item in false_positive_conflicts:
            validation_rows.append(
                {
                    "person_id": item.person_id,
                    "activity_1": item.event_a.activity,
                    "activity_2": item.event_b.activity,
                    "known_start": "",
                    "known_end": "",
                    "known_conflict_start": "",
                    "known_conflict_end": "",
                    "detected": True,
                    "conflict_id": item.key[0] + "-" + item.key[1],
                }
            )
    return precision, recall, f1_score, validation_rows


def validate_conflicts(
    detected: Sequence[ConflictRecord],
    known: Sequence[Dict[str, object]],
    output_path: str,
) -> Tuple[float, float, float]:
    precision, recall, f1_score, validation_rows = evaluate_conflicts(detected, known)
    save_csv(
        os.path.join(output_path, "validation_report.csv"),
        [
            "person_id",
            "activity_1",
            "activity_2",
            "known_start",
            "known_end",
            "known_conflict_start",
            "known_conflict_end",
            "detected",
            "conflict_id",
        ],
        validation_rows,
    )
    return precision, recall, f1_score


def save_csv(path: str, headers: Sequence[str], rows: Iterable[Dict[str, object]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def generate_conflict_report(conflicts: Sequence[ConflictRecord], output_path: str) -> None:
    sorted_conflicts = sorted(
        conflicts,
        key=lambda c: (c.person_id, c.overlap_start, c.event_a.activity, c.event_b.activity),
    )
    rows = []
    for index, conflict in enumerate(sorted_conflicts, start=1):
        items = sorted(
            [conflict.event_a, conflict.event_b], key=lambda e: (e.start_time, e.activity)
        )
        first, second = items
        conflict_id = f"C{index:04d}"
        rows.append(
            {
                "conflict_id": conflict_id,
                "person_id": conflict.person_id,
                "persons": conflict.person_id,
                "activities": f"{first.activity} | {second.activity}",
                "locations": f"{first.location} | {second.location}",
                "start_time": conflict.overlap_start.strftime(ISO_FORMAT),
                "end_time": conflict.overlap_end.strftime(ISO_FORMAT),
                "conflict_type": conflict.conflict_type(),
                "overlap_minutes": round(conflict.overlap_minutes(), 2),
                "severity": conflict.severity(),
            }
        )
    save_csv(
        os.path.join(output_path, "conflict_report.csv"),
        [
            "conflict_id",
            "person_id",
            "persons",
            "activities",
            "locations",
            "start_time",
            "end_time",
            "conflict_type",
            "overlap_minutes",
            "severity",
        ],
        rows,
    )


def generate_performance_report(
    metrics: List[Dict[str, object]], output_path: str
) -> None:
    save_csv(
        os.path.join(output_path, "performance_metrics.csv"),
        ["algorithm", "execution_ms", "peak_memory_mb", "precision", "recall", "f1_score"],
        metrics,
    )


def measure_algorithm(
    name: str,
    detector: Callable[[Sequence[ScheduleEntry]], Sequence[ConflictRecord]],
    entries: Sequence[ScheduleEntry],
) -> Tuple[List[ConflictRecord], float, float]:
    tracemalloc.start()
    start = datetime.now()
    result = detector(entries)
    duration_ms = (datetime.now() - start).total_seconds() * 1000
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_memory_mb = peak_memory / (1024 * 1024)
    return list(result), duration_ms, peak_memory_mb


def generate_gantt_chart(
    entries: Sequence[ScheduleEntry],
    conflicts: Sequence[ConflictRecord],
    output_path: str,
) -> None:
    if not entries:
        return
    persons = sorted({entry.person_id for entry in entries})
    conflict_entries = {item.event_a.entry_id for item in conflicts} | {
        item.event_b.entry_id for item in conflicts
    }
    fig, ax = plt.subplots(figsize=(14, max(6, len(persons) * 0.3)))
    person_to_y = {person: idx for idx, person in enumerate(persons)}
    for entry in sorted(entries, key=lambda e: (e.person_id, e.start_time)):
        y = person_to_y[entry.person_id]
        color = "tab:red" if entry.entry_id in conflict_entries else "tab:blue"
        ax.barh(
            y,
            (entry.end_time - entry.start_time).total_seconds() / 60,
            left=entry.start_time,
            height=0.4,
            color=color,
            edgecolor="black",
        )
    ax.set_yticks(range(len(persons)))
    ax.set_yticklabels(persons)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    ax.set_xlabel("Time")
    ax.set_title("Schedule Gantt Chart")
    fig.autofmt_xdate()
    plt.tight_layout()
    fig.savefig(os.path.join(output_path, "schedule_gantt.png"))
    plt.close(fig)


def generate_conflict_heatmap(conflicts: Sequence[ConflictRecord], output_path: str) -> None:
    if not conflicts:
        return
    persons = sorted({conflict.person_id for conflict in conflicts})
    counts: Dict[str, Counter[int]] = {person: Counter() for person in persons}
    for conflict in conflicts:
        start_hour = conflict.overlap_start.hour
        end_hour = conflict.overlap_end.hour
        for hour in range(start_hour, end_hour + 1):
            counts[conflict.person_id][hour % 24] += 1
    import numpy as np

    data = np.zeros((len(persons), 24), dtype=float)
    for person_idx, person in enumerate(persons):
        for hour, value in counts[person].items():
            data[person_idx, hour] = value
    fig, ax = plt.subplots(figsize=(12, max(4, len(persons) * 0.3)))
    heatmap = ax.imshow(data, aspect="auto", cmap="Reds")
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{hour:02d}" for hour in range(24)])
    ax.set_yticks(range(len(persons)))
    ax.set_yticklabels(persons)
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Person")
    ax.set_title("Conflict Heatmap")
    fig.colorbar(heatmap, ax=ax, label="Conflicts")
    plt.tight_layout()
    fig.savefig(os.path.join(output_path, "conflict_heatmap.png"))
    plt.close(fig)


def generate_performance_chart(metrics: List[Dict[str, object]], output_path: str) -> None:
    if not metrics:
        return
    algorithms = [item["algorithm"] for item in metrics]
    execution = [item["execution_ms"] for item in metrics]
    memory = [item["peak_memory_mb"] for item in metrics]
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()
    positions = range(len(algorithms))
    ax1.bar([i - 0.2 for i in positions], execution, width=0.4, color="tab:blue", label="Execution (ms)")
    ax2.bar([i + 0.2 for i in positions], memory, width=0.4, color="tab:orange", label="Peak Memory (MB)")
    ax1.set_xticks(list(positions))
    ax1.set_xticklabels(algorithms)
    ax1.set_ylabel("Execution Time (ms)")
    ax2.set_ylabel("Peak Memory (MB)")
    ax1.set_title("Algorithm Performance Comparison")
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")
    plt.tight_layout()
    fig.savefig(os.path.join(output_path, "algorithm_performance.png"))
    plt.close(fig)


def run_conflict_detection(input_csv: str, known_json: str, output_dir: str) -> Dict[str, object]:
    os.makedirs(output_dir, exist_ok=True)
    entries = load_schedule(input_csv)
    algorithms = [
        ("Brute Force", detect_conflicts_bruteforce),
        ("Sweep Line", detect_conflicts_sweep_line),
        ("Interval Tree", detect_conflicts_interval_tree),
    ]
    all_conflicts: Dict[Tuple[str, str], ConflictRecord] = {}
    metrics_summary: List[Dict[str, object]] = []
    reference_conflicts = load_known_conflicts(known_json)
    overall_precision = overall_recall = overall_f1 = 0.0
    for name, detector in algorithms:
        detected, duration, memory = measure_algorithm(name, detector, entries)
        for conflict in detected:
            all_conflicts[conflict.key] = conflict
        precision, recall, f1_score, _ = evaluate_conflicts(detected, reference_conflicts)
        metrics_summary.append(
            {
                "algorithm": name,
                "execution_ms": round(duration, 3),
                "peak_memory_mb": round(memory, 3),
                "precision": round(precision, 3),
                "recall": round(recall, 3),
                "f1_score": round(f1_score, 3),
            }
        )
    unique_conflicts = list(all_conflicts.values())
    overall_precision, overall_recall, overall_f1 = validate_conflicts(
        unique_conflicts, reference_conflicts, output_dir
    )
    generate_conflict_report(unique_conflicts, output_dir)
    generate_performance_report(metrics_summary, output_dir)
    generate_gantt_chart(entries, unique_conflicts, output_dir)
    generate_conflict_heatmap(unique_conflicts, output_dir)
    generate_performance_chart(metrics_summary, output_dir)
    return {
        "conflicts": unique_conflicts,
        "metrics": metrics_summary,
        "precision": overall_precision,
        "recall": overall_recall,
        "f1": overall_f1,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Multi-Person Schedule Conflict Detection System",
    )
    parser.add_argument("--input", required=True, help="Path to input schedule CSV file")
    parser.add_argument(
        "--known", required=True, help="Path to JSON file with known conflicts"
    )
    parser.add_argument(
        "--output", required=True, help="Directory to store generated reports"
    )
    return parser


def main(args: Optional[Sequence[str]] = None) -> None:
    parser = build_argument_parser()
    parsed = parser.parse_args(args=args)
    run_conflict_detection(parsed.input, parsed.known, parsed.output)


if __name__ == "__main__":
    main()

