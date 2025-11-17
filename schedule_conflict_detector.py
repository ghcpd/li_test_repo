#!/usr/bin/env python3
"""Multi-Person Schedule Conflict Detection System."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import tracemalloc
import time
from collections import defaultdict

DATE_FORMAT = "%Y-%m-%d %H:%M"


@dataclass(frozen=True)
class ScheduleEntry:
    """A single scheduled activity."""

    identifier: str
    person_id: str
    start_time: datetime
    end_time: datetime
    activity_name: str
    location: str
    scenario: Optional[str] = None

    def to_display_tuple(self) -> Tuple[str, str]:
        start = self.start_time.strftime(DATE_FORMAT)
        end = self.end_time.strftime(DATE_FORMAT)
        return start, end


@dataclass
class ConflictRecord:
    """Representation of a detected conflict."""

    conflict_id: str
    person_id: str
    entry_one: ScheduleEntry
    entry_two: ScheduleEntry
    overlap_start: datetime
    overlap_end: datetime
    conflict_type: str
    overlap_minutes: float
    severity: str


class IntervalTreeNode:
    """Simple interval tree node for conflict detection."""

    def __init__(self, entry: ScheduleEntry) -> None:
        self.entry = entry
        self.max_end = entry.end_time
        self.left: Optional["IntervalTreeNode"] = None
        self.right: Optional["IntervalTreeNode"] = None

    def insert(self, entry: ScheduleEntry) -> None:
        if entry.start_time < self.entry.start_time:
            if self.left:
                self.left.insert(entry)
            else:
                self.left = IntervalTreeNode(entry)
        else:
            if self.right:
                self.right.insert(entry)
            else:
                self.right = IntervalTreeNode(entry)
        if entry.end_time > self.max_end:
            self.max_end = entry.end_time

    def search(self, entry: ScheduleEntry) -> Iterable[ScheduleEntry]:
        if self.entry.start_time < entry.end_time and entry.start_time < self.entry.end_time:
            yield self.entry
        if self.left and self.left.max_end > entry.start_time:
            yield from self.left.search(entry)
        if self.right and self.entry.start_time < entry.end_time:
            yield from self.right.search(entry)


def parse_datetime(value: str) -> datetime:
    return datetime.strptime(value.strip(), DATE_FORMAT)


def load_schedule(path: str) -> List[ScheduleEntry]:
    entries: List[ScheduleEntry] = []
    with open(path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader):
            entries.append(
                ScheduleEntry(
                    identifier=f"row-{index}",
                    person_id=row["person_id"].strip(),
                    start_time=parse_datetime(row["start_time"]),
                    end_time=parse_datetime(row["end_time"]),
                    activity_name=row["activity_name"].strip(),
                    location=row.get("location", "").strip(),
                    scenario=row.get("scenario"),
                )
            )
    return entries


def load_known_conflicts(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def overlap(entry_one: ScheduleEntry, entry_two: ScheduleEntry) -> Optional[Tuple[datetime, datetime]]:
    start = max(entry_one.start_time, entry_two.start_time)
    end = min(entry_one.end_time, entry_two.end_time)
    if start < end:
        return start, end
    return None


def classify_overlap(entry_one: ScheduleEntry, entry_two: ScheduleEntry, overlap_span: Tuple[datetime, datetime]) -> Tuple[str, str, float]:
    overlap_start, overlap_end = overlap_span
    overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60.0
    if entry_one.start_time == entry_two.start_time and entry_one.end_time == entry_two.end_time:
        conflict_type = "full overlap"
    elif (
        entry_one.start_time >= entry_two.start_time
        and entry_one.end_time <= entry_two.end_time
    ) or (
        entry_two.start_time >= entry_one.start_time
        and entry_two.end_time <= entry_one.end_time
    ):
        conflict_type = "containment"
    else:
        conflict_type = "partial overlap"
    if overlap_minutes <= 15:
        severity = "Low"
    elif overlap_minutes <= 60:
        severity = "Medium"
    else:
        severity = "High"
    return conflict_type, severity, overlap_minutes


def conflict_key(entry_one: ScheduleEntry, entry_two: ScheduleEntry) -> Tuple[str, str, str]:
    one_id, two_id = sorted([entry_one.identifier, entry_two.identifier])
    return entry_one.person_id, one_id, two_id


def make_conflict_record(key: Tuple[str, str, str], entry_one: ScheduleEntry, entry_two: ScheduleEntry) -> ConflictRecord:
    person_id = key[0]
    if entry_one.start_time > entry_two.start_time:
        entry_one, entry_two = entry_two, entry_one
    overlap_span = overlap(entry_one, entry_two)
    if not overlap_span:
        raise ValueError("Attempted to build conflict for non-overlapping entries")
    conflict_type, severity, overlap_minutes = classify_overlap(entry_one, entry_two, overlap_span)
    start, end = overlap_span
    conflict_id = f"{person_id}-{entry_one.identifier}-{entry_two.identifier}"
    return ConflictRecord(
        conflict_id=conflict_id,
        person_id=person_id,
        entry_one=entry_one,
        entry_two=entry_two,
        overlap_start=start,
        overlap_end=end,
        conflict_type=conflict_type,
        overlap_minutes=overlap_minutes,
        severity=severity,
    )


def detect_conflicts_brute_force(entries: List[ScheduleEntry]) -> Dict[Tuple[str, str, str], ConflictRecord]:
    conflicts: Dict[Tuple[str, str, str], ConflictRecord] = {}
    by_person: Dict[str, List[ScheduleEntry]] = defaultdict(list)
    for entry in entries:
        by_person[entry.person_id].append(entry)
    for person_entries in by_person.values():
        for i, entry_one in enumerate(person_entries):
            for entry_two in person_entries[i + 1 :]:
                overlap_span = overlap(entry_one, entry_two)
                if overlap_span:
                    key = conflict_key(entry_one, entry_two)
                    conflicts[key] = make_conflict_record(key, entry_one, entry_two)
    return conflicts


def detect_conflicts_sweep_line(entries: List[ScheduleEntry]) -> Dict[Tuple[str, str, str], ConflictRecord]:
    conflicts: Dict[Tuple[str, str, str], ConflictRecord] = {}
    by_person: Dict[str, List[ScheduleEntry]] = defaultdict(list)
    for entry in entries:
        by_person[entry.person_id].append(entry)
    for person_entries in by_person.values():
        sorted_entries = sorted(person_entries, key=lambda entry: entry.start_time)
        active: List[ScheduleEntry] = []
        for current in sorted_entries:
            active = [entry for entry in active if entry.end_time > current.start_time]
            for entry in active:
                overlap_span = overlap(entry, current)
                if overlap_span:
                    key = conflict_key(entry, current)
                    conflicts[key] = make_conflict_record(key, entry, current)
            active.append(current)
    return conflicts


def detect_conflicts_interval_tree(entries: List[ScheduleEntry]) -> Dict[Tuple[str, str, str], ConflictRecord]:
    conflicts: Dict[Tuple[str, str, str], ConflictRecord] = {}
    by_person: Dict[str, List[ScheduleEntry]] = defaultdict(list)
    for entry in entries:
        by_person[entry.person_id].append(entry)
    for person_entries in by_person.values():
        sorted_entries = sorted(person_entries, key=lambda entry: entry.start_time)
        tree: Optional[IntervalTreeNode] = None
        for entry in sorted_entries:
            if tree is not None:
                for overlapping in tree.search(entry):
                    key = conflict_key(overlapping, entry)
                    conflicts[key] = make_conflict_record(key, overlapping, entry)
            if tree is None:
                tree = IntervalTreeNode(entry)
            else:
                tree.insert(entry)
    return conflicts


def track_performance(func, entries: List[ScheduleEntry]) -> Tuple[Dict[Tuple[str, str, str], ConflictRecord], float, float]:
    tracemalloc.start()
    start_time = time.perf_counter()
    conflicts = func(entries)
    elapsed = (time.perf_counter() - start_time) * 1000.0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return conflicts, elapsed, peak / 1024.0


def parse_known_conflict_time(value: str) -> Tuple[datetime, datetime]:
    start_str, end_str = [segment.strip() for segment in value.split(" - ", 1)]
    return parse_datetime(start_str), parse_datetime(end_str)


def known_conflict_key(conflict: Dict[str, str]) -> Tuple[str, datetime, datetime, datetime, datetime]:
    original_start, original_end = parse_known_conflict_time(conflict["original_schedule"])
    conflict_start, conflict_end = parse_known_conflict_time(conflict["conflict_schedule"])
    return (
        conflict["person_id"],
        original_start,
        original_end,
        conflict_start,
        conflict_end,
    )


def build_known_lookup(known_conflicts: List[Dict[str, str]]) -> Dict[Tuple[str, datetime, datetime, datetime, datetime], Dict[str, str]]:
    lookup: Dict[Tuple[str, datetime, datetime, datetime, datetime], Dict[str, str]] = {}
    for conflict in known_conflicts:
        key = known_conflict_key(conflict)
        lookup[key] = conflict
        swapped_key = (
            key[0],
            key[3],
            key[4],
            key[1],
            key[2],
        )
        lookup[swapped_key] = conflict
    return lookup


def compute_validation(detected: Dict[Tuple[str, str, str], ConflictRecord], known_conflicts: List[Dict[str, str]]):
    lookup = build_known_lookup(known_conflicts)
    report_rows = []
    true_positive = 0
    for conflict in detected.values():
        key = (
            conflict.person_id,
            conflict.entry_one.start_time,
            conflict.entry_one.end_time,
            conflict.entry_two.start_time,
            conflict.entry_two.end_time,
        )
        matched = key in lookup
        if matched:
            true_positive += 1
        report_rows.append(
            {
                "conflict_id": conflict.conflict_id,
                "person_id": conflict.person_id,
                "activity_1": conflict.entry_one.activity_name,
                "activity_2": conflict.entry_two.activity_name,
                "schedule_1": f"{conflict.entry_one.start_time.strftime(DATE_FORMAT)} - {conflict.entry_one.end_time.strftime(DATE_FORMAT)}",
                "schedule_2": f"{conflict.entry_two.start_time.strftime(DATE_FORMAT)} - {conflict.entry_two.end_time.strftime(DATE_FORMAT)}",
                "conflict_type": conflict.conflict_type,
                "overlap_minutes": f"{conflict.overlap_minutes:.2f}",
                "severity": conflict.severity,
                "correct": matched,
            }
        )
    false_positive = len(detected) - true_positive
    false_negative = len(known_conflicts) - true_positive
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1_score = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    metrics = {
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
    }
    return report_rows, metrics


def ensure_output_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def export_conflict_report(conflicts: Iterable[ConflictRecord], output_dir: str) -> None:
    ensure_output_directory(output_dir)
    path = os.path.join(output_dir, "conflict_report.csv")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "conflict_id",
            "person_id",
            "activity_1",
            "activity_2",
            "start_1",
            "end_1",
            "start_2",
            "end_2",
            "conflict_type",
            "overlap_minutes",
            "severity",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for conflict in conflicts:
            writer.writerow(
                {
                    "conflict_id": conflict.conflict_id,
                    "person_id": conflict.person_id,
                    "activity_1": conflict.entry_one.activity_name,
                    "activity_2": conflict.entry_two.activity_name,
                    "start_1": conflict.entry_one.start_time.strftime(DATE_FORMAT),
                    "end_1": conflict.entry_one.end_time.strftime(DATE_FORMAT),
                    "start_2": conflict.entry_two.start_time.strftime(DATE_FORMAT),
                    "end_2": conflict.entry_two.end_time.strftime(DATE_FORMAT),
                    "conflict_type": conflict.conflict_type,
                    "overlap_minutes": f"{conflict.overlap_minutes:.2f}",
                    "severity": conflict.severity,
                }
            )


def export_validation_report(rows: List[Dict[str, object]], output_dir: str) -> None:
    ensure_output_directory(output_dir)
    path = os.path.join(output_dir, "validation_report.csv")
    if not rows:
        headers = [
            "conflict_id",
            "person_id",
            "activity_1",
            "activity_2",
            "schedule_1",
            "schedule_2",
            "conflict_type",
            "overlap_minutes",
            "severity",
            "correct",
        ]
    else:
        headers = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def export_performance_report(performance_data: Dict[str, Tuple[float, float]], metrics: Dict[str, float], output_dir: str) -> None:
    ensure_output_directory(output_dir)
    path = os.path.join(output_dir, "performance_report.csv")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "algorithm",
            "execution_time_ms",
            "peak_memory_kb",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for algorithm, data in performance_data.items():
            writer.writerow(
                {
                    "algorithm": algorithm,
                    "execution_time_ms": f"{data[0]:.3f}",
                    "peak_memory_kb": f"{data[1]:.3f}",
                }
            )
    metrics_path = os.path.join(output_dir, "validation_metrics.txt")
    with open(metrics_path, "w", encoding="utf-8") as handle:
        handle.write("Validation Metrics\n")
        handle.write(f"Precision: {metrics['precision']:.4f}\n")
        handle.write(f"Recall: {metrics['recall']:.4f}\n")
        handle.write(f"F1 Score: {metrics['f1_score']:.4f}\n")
        handle.write(f"True Positive: {metrics['true_positive']}\n")
        handle.write(f"False Positive: {metrics['false_positive']}\n")
        handle.write(f"False Negative: {metrics['false_negative']}\n")


def build_conflict_lookup(conflicts: Iterable[ConflictRecord]) -> Dict[str, List[ConflictRecord]]:
    lookup: Dict[str, List[ConflictRecord]] = defaultdict(list)
    for conflict in conflicts:
        lookup[conflict.person_id].append(conflict)
    return lookup


def generate_gantt_chart(entries: List[ScheduleEntry], conflicts: Dict[Tuple[str, str, str], ConflictRecord], output_dir: str) -> None:
    ensure_output_directory(output_dir)
    conflict_lookup = build_conflict_lookup(conflicts.values())
    conflicting_ids = {conflict.entry_one.identifier for conflict in conflicts.values()}
    conflicting_ids.update(conflict.entry_two.identifier for conflict in conflicts.values())
    persons = sorted({entry.person_id for entry in entries})
    if not persons:
        return
    figure, axis = plt.subplots(figsize=(12, max(6, len(persons) * 0.3)))
    y_ticks = []
    y_labels = []
    y_position = 10
    height = 8
    for person in persons:
        person_entries = [entry for entry in entries if entry.person_id == person]
        for entry in person_entries:
            color = "#d95f02" if entry.identifier in conflicting_ids else "#1b9e77"
            axis.broken_barh(
                [(matplotlib.dates.date2num(entry.start_time), (entry.end_time - entry.start_time).total_seconds() / 86400)],
                (y_position, height),
                facecolors=color,
            )
        y_ticks.append(y_position + height / 2)
        y_labels.append(person)
        y_position += height + 4
    axis.set_xlabel("Time")
    axis.set_ylabel("Person")
    axis.set_yticks(y_ticks)
    axis.set_yticklabels(y_labels)
    axis.set_title("Schedule Gantt Chart with Conflicts Highlighted")
    axis.grid(True)
    figure.autofmt_xdate()
    plt.tight_layout()
    figure.savefig(os.path.join(output_dir, "gantt_chart.png"))
    plt.close(figure)


def generate_conflict_heatmap(conflicts: Dict[Tuple[str, str, str], ConflictRecord], output_dir: str) -> None:
    ensure_output_directory(output_dir)
    conflict_lookup = build_conflict_lookup(conflicts.values())
    persons = sorted(conflict_lookup.keys())
    if not persons:
        return
    hour_bins = list(range(24))
    heatmap = []
    for person in persons:
        counts = [0 for _ in hour_bins]
        for conflict in conflict_lookup[person]:
            hour = conflict.overlap_start.hour
            counts[hour] += 1
        heatmap.append(counts)
    figure, axis = plt.subplots(figsize=(12, max(6, len(persons) * 0.3)))
    mesh = axis.imshow(heatmap, aspect="auto", cmap="Reds")
    axis.set_xticks(range(len(hour_bins)))
    axis.set_xticklabels(hour_bins)
    axis.set_yticks(range(len(persons)))
    axis.set_yticklabels(persons)
    axis.set_xlabel("Hour of Day")
    axis.set_ylabel("Person")
    axis.set_title("Conflict Frequency Heatmap")
    figure.colorbar(mesh, ax=axis, label="Conflict Count")
    plt.tight_layout()
    figure.savefig(os.path.join(output_dir, "conflict_heatmap.png"))
    plt.close(figure)


def generate_performance_chart(performance_data: Dict[str, Tuple[float, float]], output_dir: str) -> None:
    ensure_output_directory(output_dir)
    algorithms = list(performance_data.keys())
    times = [data[0] for data in performance_data.values()]
    memories = [data[1] for data in performance_data.values()]
    x_positions = range(len(algorithms))
    figure, (axis_time, axis_memory) = plt.subplots(2, 1, figsize=(12, 8))
    axis_time.bar(x_positions, times, color="#1f77b4")
    axis_time.set_xticks(list(x_positions))
    axis_time.set_xticklabels(algorithms)
    axis_time.set_ylabel("Execution Time (ms)")
    axis_time.set_title("Algorithm Execution Time Comparison")
    axis_memory.bar(x_positions, memories, color="#ff7f0e")
    axis_memory.set_xticks(list(x_positions))
    axis_memory.set_xticklabels(algorithms)
    axis_memory.set_ylabel("Peak Memory (KB)")
    axis_memory.set_title("Algorithm Peak Memory Usage")
    plt.tight_layout()
    figure.savefig(os.path.join(output_dir, "performance_comparison.png"))
    plt.close(figure)


def run_algorithms(entries: List[ScheduleEntry]) -> Tuple[Dict[Tuple[str, str, str], ConflictRecord], Dict[str, Tuple[float, float]]]:
    algorithms = {
        "Brute Force": detect_conflicts_brute_force,
        "Sweep Line": detect_conflicts_sweep_line,
        "Interval Tree": detect_conflicts_interval_tree,
    }
    reference_conflicts: Optional[Dict[Tuple[str, str, str], ConflictRecord]] = None
    performance: Dict[str, Tuple[float, float]] = {}
    for name, func in algorithms.items():
        conflicts, elapsed, memory = track_performance(func, entries)
        performance[name] = (elapsed, memory)
        if reference_conflicts is None:
            reference_conflicts = conflicts
        else:
            if set(reference_conflicts.keys()) != set(conflicts.keys()):
                raise RuntimeError(f"Algorithm {name} produced results inconsistent with others")
    if reference_conflicts is None:
        reference_conflicts = {}
    return reference_conflicts, performance


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-Person Schedule Conflict Detection System")
    parser.add_argument("--input", required=True, help="Path to schedule CSV file")
    parser.add_argument("--known", required=True, help="Path to known conflicts JSON file")
    parser.add_argument("--output", required=True, help="Directory for generated reports")
    args = parser.parse_args()

    entries = load_schedule(args.input)
    known_conflicts = load_known_conflicts(args.known)
    conflicts, performance_data = run_algorithms(entries)
    validation_rows, metrics = compute_validation(conflicts, known_conflicts)
    export_conflict_report(conflicts.values(), args.output)
    export_validation_report(validation_rows, args.output)
    export_performance_report(performance_data, metrics, args.output)
    generate_gantt_chart(entries, conflicts, args.output)
    generate_conflict_heatmap(conflicts, args.output)
    generate_performance_chart(performance_data, args.output)


if __name__ == "__main__":
    main()
