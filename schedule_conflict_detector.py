#!/usr/bin/env python3
"""Multi-Person Schedule Conflict Detection System.

This module implements a complete command-line tool for detecting schedule
conflicts using three different algorithms (Brute Force, Sweep Line, Interval
Tree). It generates analytical reports, validation metrics, and visualisations
based on the detected conflicts and an optional ground-truth file.
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
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

TIME_FORMAT = "%Y-%m-%d %H:%M"


@dataclass(frozen=True)
class ScheduleEntry:
    """Represents a single schedule entry for a person."""

    person_id: str
    start_time: datetime
    end_time: datetime
    activity_name: str
    location: str
    scenario: str = ""

    @property
    def entry_id(self) -> Tuple[str, str, str, str]:
        return (
            self.person_id,
            self.start_time.strftime(TIME_FORMAT),
            self.end_time.strftime(TIME_FORMAT),
            self.activity_name,
        )

    def duration_minutes(self) -> float:
        return (self.end_time - self.start_time).total_seconds() / 60.0


@dataclass
class ConflictRecord:
    signature: Tuple[Tuple[str, str, str, str], ...]
    involved_persons: Tuple[str, ...]
    activities: Tuple[str, ...]
    locations: Tuple[str, ...]
    scenario: str
    overlap_start: datetime
    overlap_end: datetime
    conflict_type: str
    overlap_minutes: float
    severity: str
    algorithm: str
    entries: Tuple[ScheduleEntry, ScheduleEntry]


class Interval:
    def __init__(self, entry: ScheduleEntry) -> None:
        self.entry = entry
        self.start = entry.start_time.timestamp()
        self.end = entry.end_time.timestamp()


class IntervalTreeNode:
    def __init__(self, intervals: Sequence[Interval]) -> None:
        if not intervals:
            raise ValueError("Intervals must not be empty")
        endpoints = sorted([iv.start for iv in intervals] + [iv.end for iv in intervals])
        self.center = endpoints[len(endpoints) // 2]
        self.intervals: List[Interval] = []
        left_list: List[Interval] = []
        right_list: List[Interval] = []
        for interval in intervals:
            if interval.end < self.center:
                left_list.append(interval)
            elif interval.start > self.center:
                right_list.append(interval)
            else:
                self.intervals.append(interval)
        self.left: Optional[IntervalTreeNode] = (
            IntervalTreeNode(left_list) if left_list else None
        )
        self.right: Optional[IntervalTreeNode] = (
            IntervalTreeNode(right_list) if right_list else None
        )

    def query(self, start: float, end: float, results: List[ScheduleEntry]) -> None:
        for interval in self.intervals:
            if interval.start <= end and interval.end >= start:
                results.append(interval.entry)
        if self.left and start <= self.center:
            self.left.query(start, end, results)
        if self.right and end >= self.center:
            self.right.query(start, end, results)


class IntervalTree:
    def __init__(self, entries: Sequence[ScheduleEntry]) -> None:
        intervals = [Interval(entry) for entry in entries]
        self.root: Optional[IntervalTreeNode] = (
            IntervalTreeNode(intervals) if intervals else None
        )

    def search(self, entry: ScheduleEntry) -> List[ScheduleEntry]:
        if not self.root:
            return []
        results: List[ScheduleEntry] = []
        self.root.query(entry.start_time.timestamp(), entry.end_time.timestamp(), results)
        return results


def parse_datetime(raw: str) -> datetime:
    return datetime.strptime(raw.strip(), TIME_FORMAT)


def load_schedules(path: str) -> List[ScheduleEntry]:
    entries: List[ScheduleEntry] = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            entries.append(
                ScheduleEntry(
                    person_id=row["person_id"],
                    start_time=parse_datetime(row["start_time"]),
                    end_time=parse_datetime(row["end_time"]),
                    activity_name=row["activity_name"],
                    location=row.get("location", ""),
                    scenario=row.get("scenario", ""),
                )
            )
    return entries


def create_signature(entry_a: ScheduleEntry, entry_b: ScheduleEntry) -> Tuple[Tuple[str, str, str, str], ...]:
    participants = sorted([entry_a.entry_id, entry_b.entry_id])
    return tuple(participants)


def create_signature_from_details(
    person_id: str,
    start_a: datetime,
    end_a: datetime,
    activity_a: str,
    start_b: datetime,
    end_b: datetime,
    activity_b: str,
) -> Tuple[Tuple[str, str, str, str], ...]:
    placeholder_a = (
        person_id,
        start_a.strftime(TIME_FORMAT),
        end_a.strftime(TIME_FORMAT),
        activity_a,
    )
    placeholder_b = (
        person_id,
        start_b.strftime(TIME_FORMAT),
        end_b.strftime(TIME_FORMAT),
        activity_b,
    )
    return tuple(sorted([placeholder_a, placeholder_b]))


def classify_conflict(entry_a: ScheduleEntry, entry_b: ScheduleEntry) -> Optional[ConflictRecord]:
    overlap_start = max(entry_a.start_time, entry_b.start_time)
    overlap_end = min(entry_a.end_time, entry_b.end_time)
    if overlap_start >= overlap_end:
        return None
    conflict_type: str
    if entry_a.start_time == entry_b.start_time and entry_a.end_time == entry_b.end_time:
        conflict_type = "full overlap"
    elif (
        entry_a.start_time <= entry_b.start_time <= entry_a.end_time
        and entry_a.end_time >= entry_b.end_time
    ) or (
        entry_b.start_time <= entry_a.start_time <= entry_b.end_time
        and entry_b.end_time >= entry_a.end_time
    ):
        conflict_type = "containment"
    else:
        conflict_type = "partial overlap"
    overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60.0
    if overlap_minutes >= 60:
        severity = "High"
    elif overlap_minutes >= 30:
        severity = "Medium"
    else:
        severity = "Low"
    persons = tuple(sorted({entry_a.person_id, entry_b.person_id}))
    activities = (entry_a.activity_name, entry_b.activity_name)
    locations = (entry_a.location, entry_b.location)
    scenarios = sorted(set(filter(None, (entry_a.scenario, entry_b.scenario))))
    scenario = scenarios[0] if scenarios else ""
    signature = create_signature(entry_a, entry_b)
    return ConflictRecord(
        signature=signature,
        involved_persons=persons,
        activities=activities,
        locations=locations,
        scenario=scenario,
        overlap_start=overlap_start,
        overlap_end=overlap_end,
        conflict_type=conflict_type,
        overlap_minutes=overlap_minutes,
        severity=severity,
        algorithm="",
        entries=(entry_a, entry_b),
    )


def detect_conflicts_brute_force(entries: Iterable[ScheduleEntry]) -> List[ConflictRecord]:
    grouped: Dict[str, List[ScheduleEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.person_id].append(entry)
    conflicts: List[ConflictRecord] = []
    for person_entries in grouped.values():
        count = len(person_entries)
        for i in range(count):
            for j in range(i + 1, count):
                record = classify_conflict(person_entries[i], person_entries[j])
                if record:
                    record.algorithm = "Brute Force"
                    conflicts.append(record)
    return conflicts


def detect_conflicts_sweep_line(entries: Iterable[ScheduleEntry]) -> List[ConflictRecord]:
    grouped: Dict[str, List[ScheduleEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.person_id].append(entry)
    conflicts: List[ConflictRecord] = []
    for person_entries in grouped.values():
        sorted_entries = sorted(person_entries, key=lambda e: e.start_time)
        active: List[ScheduleEntry] = []
        for current in sorted_entries:
            active = [entry for entry in active if entry.end_time > current.start_time]
            for other in active:
                record = classify_conflict(other, current)
                if record:
                    record.algorithm = "Sweep Line"
                    conflicts.append(record)
            active.append(current)
    return conflicts


def detect_conflicts_interval_tree(entries: Iterable[ScheduleEntry]) -> List[ConflictRecord]:
    grouped: Dict[str, List[ScheduleEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.person_id].append(entry)
    conflicts: List[ConflictRecord] = []
    for person_entries in grouped.values():
        tree = IntervalTree(person_entries)
        seen: Set[Tuple[Tuple[str, str, str, str], ...]] = set()
        for entry in person_entries:
            overlaps = tree.search(entry)
            for other in overlaps:
                if other is entry:
                    continue
                signature = create_signature(entry, other)
                if signature in seen:
                    continue
                record = classify_conflict(entry, other)
                if record:
                    record.algorithm = "Interval Tree"
                    conflicts.append(record)
                    seen.add(signature)
    return conflicts


def run_algorithms(entries: List[ScheduleEntry]) -> Dict[str, Dict[str, object]]:
    algorithms = {
        "Brute Force": detect_conflicts_brute_force,
        "Sweep Line": detect_conflicts_sweep_line,
        "Interval Tree": detect_conflicts_interval_tree,
    }
    results: Dict[str, Dict[str, object]] = {}
    for name, func in algorithms.items():
        tracemalloc.start()
        start = time.perf_counter()
        conflicts = func(entries)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        results[name] = {
            "conflicts": conflicts,
            "time_ms": elapsed_ms,
            "memory_kb": peak / 1024.0,
        }
    return results


def aggregate_conflicts(algorithm_results: Dict[str, Dict[str, object]]) -> Dict[
    Tuple[Tuple[str, str, str, str], ...], Dict[str, object]
]:
    aggregated: Dict[Tuple[Tuple[str, str, str, str], ...], Dict[str, object]] = {}
    for algorithm, data in algorithm_results.items():
        for record in data["conflicts"]:
            signature = record.signature
            if signature not in aggregated:
                aggregated[signature] = {
                    "persons": record.involved_persons,
                    "activities": record.activities,
                    "locations": record.locations,
                    "scenario": record.scenario,
                    "start": record.overlap_start,
                    "end": record.overlap_end,
                    "conflict_type": record.conflict_type,
                    "overlap_minutes": record.overlap_minutes,
                    "severity": record.severity,
                    "entries": record.entries,
                    "algorithms": {algorithm},
                }
            else:
                aggregated[signature]["algorithms"].add(algorithm)
    return aggregated


def load_known_conflicts(path: str) -> Dict[Tuple[Tuple[str, str, str, str], ...], Dict[str, object]]:
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    known: Dict[Tuple[Tuple[str, str, str, str], ...], Dict[str, object]] = {}
    for item in payload:
        person = item["person_id"]
        orig_start_raw, orig_end_raw = [
            part.strip() for part in item["original_schedule"].split(" - ")
        ]
        conflict_start_raw, conflict_end_raw = [
            part.strip() for part in item["conflict_schedule"].split(" - ")
        ]
        orig_start = parse_datetime(orig_start_raw)
        orig_end = parse_datetime(orig_end_raw)
        conflict_start = parse_datetime(conflict_start_raw)
        conflict_end = parse_datetime(conflict_end_raw)
        signature = create_signature_from_details(
            person,
            orig_start,
            orig_end,
            item["activity_1"],
            conflict_start,
            conflict_end,
            item["activity_2"],
        )
        overlap_start = max(orig_start, conflict_start)
        overlap_end = min(orig_end, conflict_end)
        known[signature] = {
            "person_id": person,
            "activities": (item["activity_1"], item["activity_2"]),
            "start": overlap_start,
            "end": overlap_end,
        }
    return known


def compute_metrics(
    predicted: Set[Tuple[Tuple[str, str, str, str], ...]],
    expected: Set[Tuple[Tuple[str, str, str, str], ...]],
) -> Dict[str, float]:
    tp = len(predicted & expected)
    fp = len(predicted - expected)
    fn = len(expected - predicted)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    if precision + recall:
        f1_score = 2 * precision * recall / (precision + recall)
    else:
        f1_score = 0.0
    accuracy = tp / (tp + fp + fn) if tp + fp + fn else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "accuracy": accuracy,
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def format_datetime(dt: datetime) -> str:
    return dt.strftime(TIME_FORMAT)


def build_validation_rows(
    aggregated: Dict[Tuple[Tuple[str, str, str, str], ...], Dict[str, object]],
    algorithm_results: Dict[str, Dict[str, object]],
    known_conflicts: Dict[Tuple[Tuple[str, str, str, str], ...], Dict[str, object]],
) -> List[Dict[str, object]]:
    signature_to_algorithms: Dict[
        Tuple[Tuple[str, str, str, str], ...], Set[str]
    ] = {}
    for signature, details in aggregated.items():
        signature_to_algorithms[signature] = set(details["algorithms"])
    predicted_sets: Dict[str, Set[Tuple[Tuple[str, str, str, str], ...]]] = {
        name: {record.signature for record in data["conflicts"]}
        for name, data in algorithm_results.items()
    }
    all_signatures = set(signature_to_algorithms.keys()) | set(known_conflicts.keys())
    rows: List[Dict[str, object]] = []
    for signature in sorted(all_signatures):
        is_known = signature in known_conflicts
        detected_by = {
            name: signature in predicted_sets.get(name, set())
            for name in algorithm_results
        }
        overall_detected = any(detected_by.values())
        if is_known and overall_detected:
            status = "True Positive"
        elif is_known and not overall_detected:
            status = "False Negative"
        else:
            status = "False Positive"
        if signature in aggregated:
            details = aggregated[signature]
            start = details["start"]
            end = details["end"]
            persons = ", ".join(details["persons"])
            activities = ", ".join(details["activities"])
        else:
            reference = known_conflicts[signature]
            start = reference["start"]
            end = reference["end"]
            persons = reference["person_id"]
            activities = ", ".join(reference["activities"])
        row = {
            "conflict_signature": " | ".join(
                ["/".join(component) for component in signature]
            ),
            "person_ids": persons,
            "activities": activities,
            "start_time": format_datetime(start),
            "end_time": format_datetime(end),
            "expected_conflict": "Yes" if is_known else "No",
            "status": status,
        }
        for name in algorithm_results:
            row[f"detected_by_{name.lower().replace(' ', '_')}"] = (
                "Yes" if detected_by[name] else "No"
            )
        rows.append(row)
    return rows


def write_conflict_report(
    aggregated: Dict[Tuple[Tuple[str, str, str, str], ...], Dict[str, object]],
    output_dir: str,
) -> None:
    csv_path = os.path.join(output_dir, "conflict_report.csv")
    txt_path = os.path.join(output_dir, "conflict_report.txt")
    fieldnames = [
        "Conflict ID",
        "Involved Persons",
        "Activities",
        "Locations",
        "Time Interval",
        "Overlap Minutes",
        "Conflict Type",
        "Severity",
        "Scenario",
        "Detected By",
    ]
    sorted_items = sorted(aggregated.items(), key=lambda item: item[1]["start"])
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, (signature, details) in enumerate(sorted_items, start=1):
            conflict_id = f"CONFLICT-{index:04d}"
            interval = f"{format_datetime(details['start'])} -> {format_datetime(details['end'])}"
            writer.writerow(
                {
                    "Conflict ID": conflict_id,
                    "Involved Persons": ", ".join(details["persons"]),
                    "Activities": ", ".join(details["activities"]),
                    "Locations": ", ".join(details["locations"]),
                    "Time Interval": interval,
                    "Overlap Minutes": f"{details['overlap_minutes']:.2f}",
                    "Conflict Type": details["conflict_type"],
                    "Severity": details["severity"],
                    "Scenario": details["scenario"] or "N/A",
                    "Detected By": ", ".join(sorted(details["algorithms"])),
                }
            )
    with open(txt_path, "w", encoding="utf-8") as handle:
        for index, (signature, details) in enumerate(sorted_items, start=1):
            conflict_id = f"CONFLICT-{index:04d}"
            handle.write(f"{conflict_id}\n")
            handle.write(f"  Persons: {', '.join(details['persons'])}\n")
            handle.write(f"  Activities: {', '.join(details['activities'])}\n")
            handle.write(f"  Locations: {', '.join(details['locations'])}\n")
            handle.write(
                f"  Interval: {format_datetime(details['start'])} -> {format_datetime(details['end'])}\n"
            )
            handle.write(f"  Conflict Type: {details['conflict_type']}\n")
            handle.write(f"  Overlap Minutes: {details['overlap_minutes']:.2f}\n")
            handle.write(f"  Severity: {details['severity']}\n")
            handle.write(f"  Scenario: {details['scenario'] or 'N/A'}\n")
            handle.write(f"  Detected By: {', '.join(sorted(details['algorithms']))}\n\n")


def write_validation_report(rows: List[Dict[str, object]], output_dir: str) -> None:
    path = os.path.join(output_dir, "validation_report.csv")
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_performance_statistics(
    algorithm_stats: Dict[str, Dict[str, float]], output_dir: str
) -> None:
    path = os.path.join(output_dir, "performance_statistics.csv")
    fieldnames = [
        "Algorithm",
        "Execution Time (ms)",
        "Memory Usage (KB)",
        "Precision",
        "Recall",
        "F1 Score",
        "Accuracy",
        "True Positives",
        "False Positives",
        "False Negatives",
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for algorithm, stats in algorithm_stats.items():
            writer.writerow(
                {
                    "Algorithm": algorithm,
                    "Execution Time (ms)": f"{stats['time_ms']:.3f}",
                    "Memory Usage (KB)": f"{stats['memory_kb']:.3f}",
                    "Precision": f"{stats['precision']:.4f}",
                    "Recall": f"{stats['recall']:.4f}",
                    "F1 Score": f"{stats['f1_score']:.4f}",
                    "Accuracy": f"{stats['accuracy']:.4f}",
                    "True Positives": stats["tp"],
                    "False Positives": stats["fp"],
                    "False Negatives": stats["fn"],
                }
            )


def generate_gantt_chart(
    entries: List[ScheduleEntry],
    aggregated: Dict[Tuple[Tuple[str, str, str, str], ...], Dict[str, object]],
    output_dir: str,
) -> None:
    path = os.path.join(output_dir, "gantt_chart.png")
    persons = sorted({entry.person_id for entry in entries})
    person_to_index = {person: idx for idx, person in enumerate(persons)}
    conflict_signatures = set()
    for signature, details in aggregated.items():
        for entry in details["entries"]:
            conflict_signatures.add(entry.entry_id)
    fig, ax = plt.subplots(figsize=(12, max(4, len(persons) * 0.6)))
    for entry in entries:
        start = mdates.date2num(entry.start_time)
        end = mdates.date2num(entry.end_time)
        duration = end - start
        color = "#d62728" if entry.entry_id in conflict_signatures else "#1f77b4"
        ax.barh(
            person_to_index[entry.person_id],
            duration,
            left=start,
            height=0.4,
            align="center",
            color=color,
            alpha=0.8,
        )
    ax.set_yticks(range(len(persons)))
    ax.set_yticklabels(persons)
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.set_xlabel("Time")
    ax.set_ylabel("Person")
    ax.set_title("Schedule Gantt Chart with Conflicts Highlighted")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def generate_conflict_heatmap(
    aggregated: Dict[Tuple[Tuple[str, str, str, str], ...], Dict[str, object]],
    output_dir: str,
) -> None:
    path = os.path.join(output_dir, "conflict_heatmap.png")
    persons = sorted({person for details in aggregated.values() for person in details["persons"]})
    if not persons:
        return
    matrix = [[0 for _ in range(24)] for _ in range(len(persons))]
    for details in aggregated.values():
        start = details["start"]
        end = details["end"]
        start_hour = start.hour
        end_hour = end.hour
        for person in details["persons"]:
            row = persons.index(person)
            for hour in range(start_hour, end_hour + 1):
                matrix[row][hour] += 1
    fig, ax = plt.subplots(figsize=(12, max(4, len(persons) * 0.5)))
    heatmap = ax.imshow(matrix, aspect="auto", cmap="Reds")
    ax.set_yticks(range(len(persons)))
    ax.set_yticklabels(persons)
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{hour:02d}:00" for hour in range(24)], rotation=45, ha="right")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Person")
    ax.set_title("Conflict Frequency Heatmap")
    fig.colorbar(heatmap, ax=ax, label="Conflict Count")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def generate_performance_chart(
    algorithm_stats: Dict[str, Dict[str, float]], output_dir: str
) -> None:
    path = os.path.join(output_dir, "algorithm_performance.png")
    algorithms = list(algorithm_stats.keys())
    times = [algorithm_stats[alg]["time_ms"] for alg in algorithms]
    memory = [algorithm_stats[alg]["memory_kb"] for alg in algorithms]
    fig, ax1 = plt.subplots(figsize=(10, 6))
    bar_positions = range(len(algorithms))
    ax1.bar(bar_positions, times, color="#1f77b4", alpha=0.7)
    ax1.set_ylabel("Execution Time (ms)")
    ax1.set_xticks(bar_positions)
    ax1.set_xticklabels(algorithms, rotation=20, ha="right")
    ax1.set_title("Algorithm Performance Comparison")
    ax2 = ax1.twinx()
    ax2.plot(bar_positions, memory, color="#d62728", marker="o")
    ax2.set_ylabel("Memory Usage (KB)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def generate_reports(
    entries: List[ScheduleEntry],
    aggregated: Dict[Tuple[Tuple[str, str, str, str], ...], Dict[str, object]],
    algorithm_stats: Dict[str, Dict[str, float]],
    validation_rows: List[Dict[str, object]],
    output_dir: str,
) -> None:
    os.makedirs(output_dir, exist_ok=True)
    write_conflict_report(aggregated, output_dir)
    write_validation_report(validation_rows, output_dir)
    write_performance_statistics(algorithm_stats, output_dir)
    generate_gantt_chart(entries, aggregated, output_dir)
    generate_conflict_heatmap(aggregated, output_dir)
    generate_performance_chart(algorithm_stats, output_dir)


def run_pipeline(input_path: str, known_path: Optional[str], output_dir: str) -> Dict[str, object]:
    schedules = load_schedules(input_path)
    algorithm_results = run_algorithms(schedules)
    aggregated = aggregate_conflicts(algorithm_results)
    known_conflicts = load_known_conflicts(known_path) if known_path else {}
    known_signatures = set(known_conflicts.keys())
    algorithm_stats: Dict[str, Dict[str, float]] = {}
    for name, data in algorithm_results.items():
        predicted_signatures = {record.signature for record in data["conflicts"]}
        metrics = compute_metrics(predicted_signatures, known_signatures)
        algorithm_stats[name] = {
            **metrics,
            "time_ms": data["time_ms"],
            "memory_kb": data["memory_kb"],
        }
    validation_rows = build_validation_rows(aggregated, algorithm_results, known_conflicts)
    generate_reports(schedules, aggregated, algorithm_stats, validation_rows, output_dir)
    combined_metrics = compute_metrics(set(aggregated.keys()), known_signatures)
    return {
        "schedules": schedules,
        "algorithm_results": algorithm_results,
        "aggregated": aggregated,
        "known_conflicts": known_conflicts,
        "algorithm_stats": algorithm_stats,
        "validation_rows": validation_rows,
        "combined_metrics": combined_metrics,
    }


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Multi-Person Schedule Conflict Detection System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="Path to the schedule CSV file")
    parser.add_argument(
        "--known",
        required=False,
        help="Path to the ground truth conflicts JSON file",
    )
    parser.add_argument(
        "--output", required=True, help="Directory to store generated reports"
    )
    args = parser.parse_args(args=argv)
    run_pipeline(args.input, args.known, args.output)
    print(f"Reports generated in: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
