"""Multi-Person Schedule Conflict Detection System.

This module provides a command-line interface for detecting schedule conflicts
using multiple algorithms, validating them against a ground-truth dataset,
and generating reports with performance statistics and visualizations.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import tracemalloc
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib

# Use a non-interactive backend suitable for headless environments.
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

import time


@dataclass(frozen=True)
class ScheduleEntry:
    """Represents a scheduled activity."""

    index: int
    person_id: str
    activity_name: str
    location: str
    start_time: datetime
    end_time: datetime


@dataclass
class ConflictRecord:
    """Represents a detected conflict between two schedule entries."""

    algorithm: str
    entry_a: ScheduleEntry
    entry_b: ScheduleEntry
    overlap_start: datetime
    overlap_end: datetime
    overlap_minutes: int
    conflict_type: str
    severity: str

    def canonical_key(self) -> Tuple:
        """Return an order-independent key used for deduplication and evaluation."""
        e1, e2 = order_entries(self.entry_a, self.entry_b)
        return (
            e1.person_id,
            e1.activity_name,
            e1.start_time.isoformat(sep=" "),
            e1.end_time.isoformat(sep=" "),
            e2.person_id,
            e2.activity_name,
            e2.start_time.isoformat(sep=" "),
            e2.end_time.isoformat(sep=" "),
        )


@dataclass
class AlgorithmResult:
    """Stores conflicts and performance statistics for an algorithm."""

    name: str
    conflicts: List[ConflictRecord]
    time_ms: float
    peak_memory_kib: float
    precision: float
    recall: float
    f1_score: float
    accuracy: float


def format_datetime(dt: datetime) -> str:
    """Format datetime without seconds for human readability."""

    return dt.strftime("%Y-%m-%d %H:%M")


def parse_datetime(value: str) -> datetime:
    """Parse an ISO datetime string into a datetime object."""

    value = value.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unsupported datetime format: {value}")


def parse_schedule(csv_path: str) -> List[ScheduleEntry]:
    """Load the schedule CSV file into a list of ScheduleEntry objects."""

    entries: List[ScheduleEntry] = []
    with open(csv_path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader):
            entry = ScheduleEntry(
                index=idx,
                person_id=row["person_id"].strip(),
                activity_name=row["activity_name"].strip(),
                location=row.get("location", "").strip(),
                start_time=parse_datetime(row["start_time"]),
                end_time=parse_datetime(row["end_time"]),
            )
            entries.append(entry)
    return entries


def load_known_conflicts(json_path: str) -> List[Dict[str, str]]:
    """Load ground-truth conflicts from a JSON file."""

    with open(json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data


def known_conflict_keys(known_conflicts: Iterable[Dict[str, str]]) -> Dict[Tuple, Dict[str, str]]:
    """Convert known conflicts to canonical keys for validation.

    Returns a mapping of key -> original record for quick lookup.
    """

    mapping: Dict[Tuple, Dict[str, str]] = {}
    for record in known_conflicts:
        start_a, end_a = [parse_datetime(x) for x in record["original_schedule"].split(" - ")]
        start_b, end_b = [parse_datetime(x) for x in record["conflict_schedule"].split(" - ")]
        first = (record["activity_1"], start_a, end_a)
        second = (record["activity_2"], start_b, end_b)
        if (start_a, end_a, record["activity_1"]) <= (start_b, end_b, record["activity_2"]):
            ordered = (first, second)
        else:
            ordered = (second, first)
        key = (
            record["person_id"],
            ordered[0][0],
            ordered[0][1].isoformat(sep=" "),
            ordered[0][2].isoformat(sep=" "),
            record["person_id"],
            ordered[1][0],
            ordered[1][1].isoformat(sep=" "),
            ordered[1][2].isoformat(sep=" "),
        )
        mapping[key] = record
    return mapping


def order_entries(entry_a: ScheduleEntry, entry_b: ScheduleEntry) -> Tuple[ScheduleEntry, ScheduleEntry]:
    """Return entries ordered deterministically for canonicalization."""

    if entry_a.start_time < entry_b.start_time:
        return entry_a, entry_b
    if entry_a.start_time > entry_b.start_time:
        return entry_b, entry_a
    if entry_a.end_time < entry_b.end_time:
        return entry_a, entry_b
    if entry_a.end_time > entry_b.end_time:
        return entry_b, entry_a
    if entry_a.activity_name <= entry_b.activity_name:
        return entry_a, entry_b
    return entry_b, entry_a


def compute_overlap(entry_a: ScheduleEntry, entry_b: ScheduleEntry) -> Optional[Tuple[datetime, datetime]]:
    """Compute the overlap interval between two schedule entries."""

    latest_start = max(entry_a.start_time, entry_b.start_time)
    earliest_end = min(entry_a.end_time, entry_b.end_time)
    if latest_start >= earliest_end:
        return None
    return latest_start, earliest_end


def classify_conflict(entry_a: ScheduleEntry, entry_b: ScheduleEntry, overlap_start: datetime, overlap_end: datetime) -> Tuple[str, str]:
    """Determine the conflict type and severity."""

    overlap_minutes = int((overlap_end - overlap_start).total_seconds() // 60)

    if (
        entry_a.start_time == entry_b.start_time
        and entry_a.end_time == entry_b.end_time
    ):
        conflict_type = "full overlap"
    elif (
        entry_a.start_time <= entry_b.start_time
        and entry_a.end_time >= entry_b.end_time
    ) or (
        entry_b.start_time <= entry_a.start_time
        and entry_b.end_time >= entry_a.end_time
    ):
        conflict_type = "containment"
    else:
        conflict_type = "partial overlap"

    if overlap_minutes >= 90:
        severity = "High"
    elif overlap_minutes >= 45:
        severity = "Medium"
    else:
        severity = "Low"

    return conflict_type, severity


def record_conflict(algorithm: str, entry_a: ScheduleEntry, entry_b: ScheduleEntry) -> Optional[ConflictRecord]:
    """Create a conflict record when entries overlap."""

    if entry_a.person_id != entry_b.person_id:
        return None

    overlap = compute_overlap(entry_a, entry_b)
    if overlap is None:
        return None

    overlap_start, overlap_end = overlap
    overlap_minutes = int((overlap_end - overlap_start).total_seconds() // 60)
    if overlap_minutes <= 0:
        return None

    conflict_type, severity = classify_conflict(entry_a, entry_b, overlap_start, overlap_end)
    return ConflictRecord(
        algorithm=algorithm,
        entry_a=entry_a,
        entry_b=entry_b,
        overlap_start=overlap_start,
        overlap_end=overlap_end,
        overlap_minutes=overlap_minutes,
        conflict_type=conflict_type,
        severity=severity,
    )


def detect_conflicts_brute_force(entries: Sequence[ScheduleEntry]) -> List[ConflictRecord]:
    """Detect conflicts using a brute-force approach."""

    conflicts: List[ConflictRecord] = []
    for i, entry_a in enumerate(entries):
        for j in range(i + 1, len(entries)):
            conflict = record_conflict("Brute Force", entry_a, entries[j])
            if conflict:
                conflicts.append(conflict)
    return conflicts


def detect_conflicts_sweep_line(entries: Sequence[ScheduleEntry]) -> List[ConflictRecord]:
    """Detect conflicts using a sweep-line algorithm."""

    sorted_entries = sorted(entries, key=lambda e: e.start_time)
    active_by_person: Dict[str, List[ScheduleEntry]] = defaultdict(list)
    conflicts: List[ConflictRecord] = []

    for entry in sorted_entries:
        active = active_by_person[entry.person_id]
        active[:] = [item for item in active if item.end_time > entry.start_time]
        for active_entry in active:
            conflict = record_conflict("Sweep Line", entry, active_entry)
            if conflict:
                conflicts.append(conflict)
        active.append(entry)
    return conflicts


class IntervalTreeNode:
    """Simple interval tree node for conflict detection."""

    def __init__(self, entries: Sequence[ScheduleEntry]):
        timestamps = []
        for entry in entries:
            timestamps.append(entry.start_time.timestamp())
            timestamps.append(entry.end_time.timestamp())
        self.center = sum(timestamps) / len(timestamps)
        self.center_entries: List[ScheduleEntry] = []
        left_entries: List[ScheduleEntry] = []
        right_entries: List[ScheduleEntry] = []
        center_start = datetime.fromtimestamp(self.center)

        for entry in entries:
            if entry.end_time.timestamp() < self.center:
                left_entries.append(entry)
            elif entry.start_time.timestamp() > self.center:
                right_entries.append(entry)
            else:
                self.center_entries.append(entry)

        self.left: Optional[IntervalTreeNode] = (
            IntervalTreeNode(left_entries) if left_entries else None
        )
        self.right: Optional[IntervalTreeNode] = (
            IntervalTreeNode(right_entries) if right_entries else None
        )
        self.center_point = center_start

    def query(self, entry: ScheduleEntry) -> Iterable[ScheduleEntry]:
        results: List[ScheduleEntry] = []
        center_timestamp = self.center
        if entry.end_time.timestamp() < center_timestamp:
            if self.left:
                results.extend(self.left.query(entry))
            return results
        if entry.start_time.timestamp() > center_timestamp:
            if self.right:
                results.extend(self.right.query(entry))
            return results

        for candidate in self.center_entries:
            if candidate is entry:
                continue
            if compute_overlap(entry, candidate):
                results.append(candidate)
        if self.left:
            results.extend(self.left.query(entry))
        if self.right:
            results.extend(self.right.query(entry))
        return results


def build_interval_tree(entries: Sequence[ScheduleEntry]) -> Optional[IntervalTreeNode]:
    if not entries:
        return None
    return IntervalTreeNode(entries)


def detect_conflicts_interval_tree(entries: Sequence[ScheduleEntry]) -> List[ConflictRecord]:
    """Detect conflicts using an interval-tree-based approach."""

    conflicts: List[ConflictRecord] = []
    by_person: Dict[str, List[ScheduleEntry]] = defaultdict(list)
    for entry in entries:
        by_person[entry.person_id].append(entry)

    for person_entries in by_person.values():
        tree = build_interval_tree(person_entries)
        if tree is None:
            continue
        seen_pairs: set[Tuple[int, int]] = set()
        for entry in person_entries:
            for candidate in tree.query(entry):
                idx_pair = tuple(sorted((entry.index, candidate.index)))
                if idx_pair in seen_pairs:
                    continue
                conflict = record_conflict("Interval Tree", entry, candidate)
                if conflict:
                    conflicts.append(conflict)
                    seen_pairs.add(idx_pair)
    return conflicts


def evaluate_conflicts(conflicts: Sequence[ConflictRecord], known_lookup: Dict[Tuple, Dict[str, str]]) -> Tuple[float, float, float, float, List[Tuple[ConflictRecord, str]]]:
    """Compute precision, recall, F1, and accuracy for detected conflicts.

    Returns metrics and detailed per-conflict classifications (TP/FP/FN).
    """

    conflict_keys = {conflict.canonical_key() for conflict in conflicts}
    known_keys = set(known_lookup.keys())

    true_positive_keys = conflict_keys & known_keys
    false_positive_keys = conflict_keys - known_keys
    false_negative_keys = known_keys - conflict_keys

    tp = len(true_positive_keys)
    fp = len(false_positive_keys)
    fn = len(false_negative_keys)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    total_decisions = tp + fp + fn
    accuracy = tp / total_decisions if total_decisions else 1.0

    details: List[Tuple[ConflictRecord, str]] = []
    for conflict in conflicts:
        key = conflict.canonical_key()
        if key in true_positive_keys:
            details.append((conflict, "TP"))
        elif key in false_positive_keys:
            details.append((conflict, "FP"))

    for key in false_negative_keys:
        record = known_lookup[key]
        start_a, end_a = record["original_schedule"].split(" - ")
        start_b, end_b = record["conflict_schedule"].split(" - ")
        dummy_entry_a = ScheduleEntry(
            index=-1,
            person_id=record["person_id"],
            activity_name=record["activity_1"],
            location="",
            start_time=parse_datetime(start_a),
            end_time=parse_datetime(end_a),
        )
        dummy_entry_b = ScheduleEntry(
            index=-1,
            person_id=record["person_id"],
            activity_name=record["activity_2"],
            location="",
            start_time=parse_datetime(start_b),
            end_time=parse_datetime(end_b),
        )
        overlap = compute_overlap(dummy_entry_a, dummy_entry_b)
        if overlap is None:
            continue
        overlap_start, overlap_end = overlap
        overlap_minutes = int((overlap_end - overlap_start).total_seconds() // 60)
        conflict_type, severity = classify_conflict(dummy_entry_a, dummy_entry_b, overlap_start, overlap_end)
        details.append(
            (
                ConflictRecord(
                    algorithm="Ground Truth",
                    entry_a=dummy_entry_a,
                    entry_b=dummy_entry_b,
                    overlap_start=overlap_start,
                    overlap_end=overlap_end,
                    overlap_minutes=overlap_minutes,
                    conflict_type=conflict_type,
                    severity=severity,
                ),
                "FN",
            )
        )

    return precision, recall, f1, accuracy, details


def measure_performance(detector, entries: Sequence[ScheduleEntry]) -> Tuple[List[ConflictRecord], float, float]:
    """Measure execution time and peak memory for a detector function."""

    tracemalloc.start()
    start_time = time.perf_counter()
    conflicts = detector(entries)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_kib = peak / 1024.0
    return conflicts, elapsed_ms, peak_kib


def aggregate_conflicts(results: Sequence[AlgorithmResult]) -> List[Dict[str, object]]:
    """Combine conflicts detected by all algorithms into a single list."""

    aggregated: Dict[Tuple, Dict[str, object]] = {}
    for result in results:
        for conflict in result.conflicts:
            key = conflict.canonical_key()
            if key not in aggregated:
                aggregated[key] = {
                    "entries": order_entries(conflict.entry_a, conflict.entry_b),
                    "overlap_start": conflict.overlap_start,
                    "overlap_end": conflict.overlap_end,
                    "overlap_minutes": conflict.overlap_minutes,
                    "conflict_type": conflict.conflict_type,
                    "severity": conflict.severity,
                    "algorithms": set(),
                }
            aggregated[key]["algorithms"].add(result.name)
    combined = []
    for key, data in sorted(aggregated.items(), key=lambda item: item[0]):
        entry_a, entry_b = data["entries"]
        combined.append(
            {
                "person_ids": ";".join(sorted({entry_a.person_id, entry_b.person_id})),
                "activities": f"{entry_a.activity_name} | {entry_b.activity_name}",
                "locations": f"{entry_a.location} | {entry_b.location}",
                "start_time": format_datetime(data["overlap_start"]),
                "end_time": format_datetime(data["overlap_end"]),
                "overlap_minutes": data["overlap_minutes"],
                "conflict_type": data["conflict_type"],
                "severity": data["severity"],
                "algorithms": ", ".join(sorted(data["algorithms"])),
                "key": key,
            }
        )
    return combined


def write_conflict_reports(conflicts: List[Dict[str, object]], output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "conflict_report.csv")
    txt_path = os.path.join(output_dir, "conflict_report.txt")

    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "conflict_id",
                "person_ids",
                "activities",
                "locations",
                "start_time",
                "end_time",
                "conflict_type",
                "overlap_minutes",
                "severity",
                "algorithms",
            ]
        )
        for idx, conflict in enumerate(conflicts, start=1):
            conflict_id = f"C{idx:04d}"
            writer.writerow(
                [
                    conflict_id,
                    conflict["person_ids"],
                    conflict["activities"],
                    conflict["locations"],
                    conflict["start_time"],
                    conflict["end_time"],
                    conflict["conflict_type"],
                    conflict["overlap_minutes"],
                    conflict["severity"],
                    conflict["algorithms"],
                ]
            )

    with open(txt_path, "w", encoding="utf-8") as handle:
        for idx, conflict in enumerate(conflicts, start=1):
            conflict_id = f"C{idx:04d}"
            handle.write(f"Conflict {conflict_id}\n")
            handle.write(f"  Persons: {conflict['person_ids']}\n")
            handle.write(f"  Activities: {conflict['activities']}\n")
            handle.write(f"  Locations: {conflict['locations']}\n")
            handle.write(f"  Time: {conflict['start_time']} to {conflict['end_time']}\n")
            handle.write(f"  Type: {conflict['conflict_type']}\n")
            handle.write(f"  Overlap (minutes): {conflict['overlap_minutes']}\n")
            handle.write(f"  Severity: {conflict['severity']}\n")
            handle.write(f"  Algorithms: {conflict['algorithms']}\n\n")


def write_validation_report(
    algorithm_details: Sequence[Tuple[str, List[Tuple[ConflictRecord, str]]]],
    output_dir: str,
) -> None:
    path = os.path.join(output_dir, "validation_report.csv")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "algorithm",
                "match_type",
                "person_id",
                "activity_1",
                "start_1",
                "end_1",
                "activity_2",
                "start_2",
                "end_2",
                "conflict_type",
                "overlap_minutes",
                "severity",
            ]
        )
        for algorithm, details in algorithm_details:
            for conflict, match_type in details:
                entry_a, entry_b = order_entries(conflict.entry_a, conflict.entry_b)
                writer.writerow(
                    [
                        algorithm,
                        match_type,
                        entry_a.person_id,
                        entry_a.activity_name,
                        format_datetime(entry_a.start_time),
                        format_datetime(entry_a.end_time),
                        entry_b.activity_name,
                        format_datetime(entry_b.start_time),
                        format_datetime(entry_b.end_time),
                        conflict.conflict_type,
                        conflict.overlap_minutes,
                        conflict.severity,
                    ]
                )


def write_performance_summary(results: Sequence[AlgorithmResult], output_dir: str) -> None:
    path = os.path.join(output_dir, "performance_stats.csv")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "algorithm",
                "num_conflicts",
                "execution_time_ms",
                "peak_memory_kib",
                "precision",
                "recall",
                "f1_score",
                "accuracy",
            ]
        )
        for result in results:
            writer.writerow(
                [
                    result.name,
                    len(result.conflicts),
                    f"{result.time_ms:.3f}",
                    f"{result.peak_memory_kib:.2f}",
                    f"{result.precision:.4f}",
                    f"{result.recall:.4f}",
                    f"{result.f1_score:.4f}",
                    f"{result.accuracy:.4f}",
                ]
            )


def generate_gantt_chart(entries: Sequence[ScheduleEntry], conflicts: Sequence[Dict[str, object]], output_dir: str) -> None:
    fig, ax = plt.subplots(figsize=(14, 8))
    persons = sorted({entry.person_id for entry in entries})
    person_indices = {person: idx for idx, person in enumerate(persons)}

    for entry in entries:
        start = mdates.date2num(entry.start_time)
        duration = (entry.end_time - entry.start_time).total_seconds() / (60 * 60 * 24)
        ax.barh(
            person_indices[entry.person_id],
            duration,
            left=start,
            height=0.4,
            align="center",
            color="#4C72B0",
            edgecolor="black",
        )

    for conflict in conflicts:
        start_dt = parse_datetime(conflict["start_time"])
        end_dt = parse_datetime(conflict["end_time"])
        persons_involved = conflict["person_ids"].split(";")
        color = {"Low": "#55A868", "Medium": "#C44E52", "High": "#DD8452"}[conflict["severity"]]
        for person in persons_involved:
            if person not in person_indices:
                continue
            start_num = mdates.date2num(start_dt)
            duration = (end_dt - start_dt).total_seconds() / (60 * 60 * 24)
            ax.barh(
                person_indices[person],
                duration,
                left=start_num,
                height=0.4,
                align="center",
                color=color,
                alpha=0.6,
            )

    ax.set_yticks(list(person_indices.values()))
    ax.set_yticklabels(persons)
    ax.set_xlabel("Time")
    ax.set_ylabel("Persons")
    ax.set_title("Schedule with Conflicts Highlighted")
    ax.xaxis_date()
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "gantt_chart.png"))
    plt.close(fig)


def generate_conflict_heatmap(conflicts: Sequence[Dict[str, object]], output_dir: str) -> None:
    if not conflicts:
        return

    persons = sorted({person for conflict in conflicts for person in conflict["person_ids"].split(";")})
    hours = list(range(24))
    heatmap = [[0 for _ in hours] for _ in persons]

    for conflict in conflicts:
        start_dt = parse_datetime(conflict["start_time"])
        end_dt = parse_datetime(conflict["end_time"])
        duration_hours = int((end_dt - start_dt).total_seconds() // 3600) + 1
        for person in conflict["person_ids"].split(";"):
            for hour_offset in range(duration_hours):
                hour = (start_dt.hour + hour_offset) % 24
                heatmap[persons.index(person)][hour] += 1

    fig, ax = plt.subplots(figsize=(12, max(6, len(persons) * 0.5)))
    cax = ax.imshow(heatmap, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(hours)))
    ax.set_xticklabels(hours)
    ax.set_yticks(range(len(persons)))
    ax.set_yticklabels(persons)
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Person")
    ax.set_title("Conflict Frequency Heatmap")
    fig.colorbar(cax, ax=ax, label="Conflict Count")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "conflict_heatmap.png"))
    plt.close(fig)


def generate_performance_chart(results: Sequence[AlgorithmResult], output_dir: str) -> None:
    fig, ax1 = plt.subplots(figsize=(10, 6))

    algorithms = [result.name for result in results]
    times = [result.time_ms for result in results]
    memory = [result.peak_memory_kib for result in results]

    ax1.bar(algorithms, times, color="#4C72B0", alpha=0.7)
    ax1.set_ylabel("Execution Time (ms)", color="#4C72B0")
    ax1.tick_params(axis="y", labelcolor="#4C72B0")

    ax2 = ax1.twinx()
    ax2.plot(algorithms, memory, color="#C44E52", marker="o", linewidth=2)
    ax2.set_ylabel("Peak Memory (KiB)", color="#C44E52")
    ax2.tick_params(axis="y", labelcolor="#C44E52")

    ax1.set_title("Algorithm Performance Comparison")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "algorithm_performance.png"))
    plt.close(fig)


def run_cli(input_path: str, known_path: str, output_dir: str) -> None:
    entries = parse_schedule(input_path)
    known = load_known_conflicts(known_path)
    known_lookup = known_conflict_keys(known)

    algorithms = [
        ("Brute Force", detect_conflicts_brute_force),
        ("Sweep Line", detect_conflicts_sweep_line),
        ("Interval Tree", detect_conflicts_interval_tree),
    ]

    results: List[AlgorithmResult] = []
    algorithm_validation: List[Tuple[str, List[Tuple[ConflictRecord, str]]]] = []

    for name, detector in algorithms:
        conflicts, time_ms, memory_kib = measure_performance(detector, entries)
        precision, recall, f1, accuracy, details = evaluate_conflicts(conflicts, known_lookup)
        results.append(
            AlgorithmResult(
                name=name,
                conflicts=conflicts,
                time_ms=time_ms,
                peak_memory_kib=memory_kib,
                precision=precision,
                recall=recall,
                f1_score=f1,
                accuracy=accuracy,
            )
        )
        algorithm_validation.append((name, details))

    aggregated = aggregate_conflicts(results)
    write_conflict_reports(aggregated, output_dir)
    write_validation_report(algorithm_validation, output_dir)
    write_performance_summary(results, output_dir)

    generate_gantt_chart(entries, aggregated, output_dir)
    generate_conflict_heatmap(aggregated, output_dir)
    generate_performance_chart(results, output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-Person Schedule Conflict Detection System",
    )
    parser.add_argument("--input", required=True, help="Path to the schedule CSV file")
    parser.add_argument("--known", required=True, help="Path to the known conflicts JSON file")
    parser.add_argument("--output", required=True, help="Directory to write reports")
    args = parser.parse_args()

    run_cli(args.input, args.known, args.output)


if __name__ == "__main__":
    main()
