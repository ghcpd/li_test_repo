#!/usr/bin/env python3
"""Multi-Person Schedule Conflict Detection System.

This command-line tool loads schedule data, executes three conflict detection
algorithms (brute force, sweep line, and interval tree), validates the detected
conflicts against a ground-truth file, and generates analytic reports including
performance metrics and visualisations.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
import tracemalloc
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt


@dataclass(frozen=True)
class ScheduleEntry:
    """Represents a single scheduled activity for a person."""

    entry_id: int
    person_id: str
    start: datetime
    end: datetime
    activity: str
    location: str

    @property
    def duration_minutes(self) -> float:
        return (self.end - self.start).total_seconds() / 60.0


@dataclass
class ConflictRecord:
    """Stores information about an identified schedule conflict."""

    key: Tuple[str, int, int]
    person_id: str
    activity_1: str
    activity_2: str
    location_1: str
    location_2: str
    start_1: datetime
    end_1: datetime
    start_2: datetime
    end_2: datetime
    overlap_start: datetime
    overlap_end: datetime
    overlap_minutes: float
    conflict_type: str
    severity: str

    def to_csv_row(self, conflict_id: str) -> List[str]:
        return [
            conflict_id,
            self.person_id,
            f"{self.activity_1} / {self.activity_2}",
            f"{self.start_1:%Y-%m-%d %H:%M} - {self.end_1:%Y-%m-%d %H:%M}",
            f"{self.start_2:%Y-%m-%d %H:%M} - {self.end_2:%Y-%m-%d %H:%M}",
            f"{self.overlap_start:%Y-%m-%d %H:%M}",
            f"{self.overlap_end:%Y-%m-%d %H:%M}",
            f"{int(self.overlap_minutes)}",
            self.conflict_type,
            self.severity,
        ]


def parse_schedule(input_path: str) -> List[ScheduleEntry]:
    entries: List[ScheduleEntry] = []
    with open(input_path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required_columns = {"person_id", "start_time", "end_time", "activity_name", "location"}
        if not required_columns.issubset(reader.fieldnames or {}):
            raise ValueError("Input CSV must contain person_id, start_time, end_time, activity_name, and location columns")
        for idx, row in enumerate(reader):
            try:
                start = datetime.strptime(row["start_time"], "%Y-%m-%d %H:%M")
                end = datetime.strptime(row["end_time"], "%Y-%m-%d %H:%M")
            except (KeyError, ValueError) as exc:  # pragma: no cover - defensive branch
                raise ValueError(f"Invalid datetime format in row {idx + 2}: {exc}") from exc
            if end <= start:
                continue
            entries.append(
                ScheduleEntry(
                    entry_id=idx,
                    person_id=row["person_id"],
                    start=start,
                    end=end,
                    activity=row["activity_name"],
                    location=row["location"],
                )
            )
    return entries


def group_entries_by_person(entries: Sequence[ScheduleEntry]) -> Dict[str, List[ScheduleEntry]]:
    grouped: Dict[str, List[ScheduleEntry]] = {}
    for entry in entries:
        grouped.setdefault(entry.person_id, []).append(entry)
    for event_list in grouped.values():
        event_list.sort(key=lambda x: (x.start, x.end, x.entry_id))
    return grouped


def _compute_overlap(entry_a: ScheduleEntry, entry_b: ScheduleEntry) -> Optional[Tuple[datetime, datetime]]:
    start = max(entry_a.start, entry_b.start)
    end = min(entry_a.end, entry_b.end)
    if start < end:
        return start, end
    return None


def _conflict_type(entry_a: ScheduleEntry, entry_b: ScheduleEntry) -> str:
    if entry_a.start == entry_b.start and entry_a.end == entry_b.end:
        return "full overlap"
    if (entry_a.start <= entry_b.start and entry_a.end >= entry_b.end) or (
        entry_b.start <= entry_a.start and entry_b.end >= entry_a.end
    ):
        return "containment"
    return "partial overlap"


def _severity(minutes: float) -> str:
    if minutes < 15:
        return "Low"
    if minutes < 60:
        return "Medium"
    return "High"


def build_conflict(entry_a: ScheduleEntry, entry_b: ScheduleEntry) -> Optional[ConflictRecord]:
    overlap = _compute_overlap(entry_a, entry_b)
    if not overlap:
        return None
    overlap_start, overlap_end = overlap
    overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60.0
    key = (entry_a.person_id, min(entry_a.entry_id, entry_b.entry_id), max(entry_a.entry_id, entry_b.entry_id))
    return ConflictRecord(
        key=key,
        person_id=entry_a.person_id,
        activity_1=entry_a.activity,
        activity_2=entry_b.activity,
        location_1=entry_a.location,
        location_2=entry_b.location,
        start_1=entry_a.start,
        end_1=entry_a.end,
        start_2=entry_b.start,
        end_2=entry_b.end,
        overlap_start=overlap_start,
        overlap_end=overlap_end,
        overlap_minutes=overlap_minutes,
        conflict_type=_conflict_type(entry_a, entry_b),
        severity=_severity(overlap_minutes),
    )


def detect_conflicts_bruteforce(grouped_entries: Dict[str, List[ScheduleEntry]]) -> Dict[Tuple[str, int, int], ConflictRecord]:
    conflicts: Dict[Tuple[str, int, int], ConflictRecord] = {}
    for person, entries in grouped_entries.items():
        length = len(entries)
        for idx in range(length):
            for other_idx in range(idx + 1, length):
                conflict = build_conflict(entries[idx], entries[other_idx])
                if conflict:
                    conflicts[conflict.key] = conflict
    return conflicts


def detect_conflicts_sweepline(grouped_entries: Dict[str, List[ScheduleEntry]]) -> Dict[Tuple[str, int, int], ConflictRecord]:
    conflicts: Dict[Tuple[str, int, int], ConflictRecord] = {}
    for person, entries in grouped_entries.items():
        active: List[ScheduleEntry] = []
        for entry in entries:
            active = [evt for evt in active if evt.end > entry.start]
            for active_entry in active:
                conflict = build_conflict(active_entry, entry)
                if conflict:
                    conflicts[conflict.key] = conflict
            active.append(entry)
    return conflicts


class IntervalNode:
    def __init__(self, entries: Sequence[ScheduleEntry]):
        points = sorted(((entry.start.timestamp() + entry.end.timestamp()) / 2.0) for entry in entries)
        self.center: float = points[len(points) // 2] if points else 0.0
        self.overlapping: List[ScheduleEntry] = []
        left_list: List[ScheduleEntry] = []
        right_list: List[ScheduleEntry] = []
        for entry in entries:
            start_ts = entry.start.timestamp()
            end_ts = entry.end.timestamp()
            if end_ts < self.center:
                left_list.append(entry)
            elif start_ts > self.center:
                right_list.append(entry)
            else:
                self.overlapping.append(entry)
        self.left: Optional[IntervalNode] = IntervalNode(left_list) if left_list else None
        self.right: Optional[IntervalNode] = IntervalNode(right_list) if right_list else None

    def search(self, entry: ScheduleEntry) -> List[ScheduleEntry]:
        matches: List[ScheduleEntry] = []
        entry_start = entry.start.timestamp()
        entry_end = entry.end.timestamp()
        for candidate in self.overlapping:
            if candidate.entry_id == entry.entry_id:
                continue
            if candidate.start < entry.end and candidate.end > entry.start:
                matches.append(candidate)
        if self.left and entry_start <= self.center:
            matches.extend(self.left.search(entry))
        if self.right and entry_end >= self.center:
            matches.extend(self.right.search(entry))
        return matches


def detect_conflicts_interval_tree(grouped_entries: Dict[str, List[ScheduleEntry]]) -> Dict[Tuple[str, int, int], ConflictRecord]:
    conflicts: Dict[Tuple[str, int, int], ConflictRecord] = {}
    for person, entries in grouped_entries.items():
        if not entries:
            continue
        tree = IntervalNode(entries)
        for entry in entries:
            for other in tree.search(entry):
                if other.entry_id < entry.entry_id:
                    continue
                conflict = build_conflict(entry, other)
                if conflict:
                    conflicts[conflict.key] = conflict
    return conflicts


def load_known_conflicts(path: str, entries: Sequence[ScheduleEntry]) -> Dict[Tuple[str, int, int], ConflictRecord]:
    with open(path, "r", encoding="utf-8") as handle:
        reference = json.load(handle)
    entry_lookup: Dict[Tuple[str, str, str], ScheduleEntry] = {}
    for entry in entries:
        key = (entry.person_id, f"{entry.start:%Y-%m-%d %H:%M}", f"{entry.end:%Y-%m-%d %H:%M}")
        entry_lookup[key] = entry
    known: Dict[Tuple[str, int, int], ConflictRecord] = {}
    for item in reference:
        person = item["person_id"]
        schedule_a = [part.strip() for part in item["original_schedule"].split(" - ")]
        schedule_b = [part.strip() for part in item["conflict_schedule"].split(" - ")]
        if len(schedule_a) != 2 or len(schedule_b) != 2:
            continue
        start_a, end_a = schedule_a
        start_b, end_b = schedule_b
        entry_a = entry_lookup.get((person, start_a, end_a))
        entry_b = entry_lookup.get((person, start_b, end_b))
        if not entry_a or not entry_b:
            continue
        conflict = build_conflict(entry_a, entry_b)
        if conflict:
            known[conflict.key] = conflict
    return known


def evaluate_conflicts(
    detected: Dict[Tuple[str, int, int], ConflictRecord],
    known: Dict[Tuple[str, int, int], ConflictRecord],
) -> Tuple[float, float, float, List[Dict[str, str]]]:
    detected_keys = set(detected.keys())
    known_keys = set(known.keys())
    true_positive = detected_keys & known_keys
    false_positive = detected_keys - known_keys
    false_negative = known_keys - detected_keys

    precision = len(true_positive) / len(detected_keys) if detected_keys else 0.0
    recall = len(true_positive) / len(known_keys) if known_keys else 0.0
    if precision + recall == 0:
        f1_score = 0.0
    else:
        f1_score = 2 * precision * recall / (precision + recall)

    details: List[Dict[str, str]] = []
    for key in sorted(true_positive):
        conflict = detected[key]
        details.append(
            {
                "person_id": conflict.person_id,
                "conflict_key": str(key),
                "activity_1": conflict.activity_1,
                "activity_2": conflict.activity_2,
                "status": "True Positive",
            }
        )
    for key in sorted(false_positive):
        conflict = detected[key]
        details.append(
            {
                "person_id": conflict.person_id,
                "conflict_key": str(key),
                "activity_1": conflict.activity_1,
                "activity_2": conflict.activity_2,
                "status": "False Positive",
            }
        )
    for key in sorted(false_negative):
        conflict = known[key]
        details.append(
            {
                "person_id": conflict.person_id,
                "conflict_key": str(key),
                "activity_1": conflict.activity_1,
                "activity_2": conflict.activity_2,
                "status": "False Negative",
            }
        )

    return precision, recall, f1_score, details


def _write_csv(path: str, headers: Sequence[str], rows: Iterable[Sequence[str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)


def save_conflict_reports(conflicts: Sequence[ConflictRecord], output_dir: str) -> None:
    csv_rows: List[List[str]] = []
    text_lines: List[str] = []
    for idx, conflict in enumerate(sorted(conflicts, key=lambda c: c.key)):
        conflict_id = f"CF-{idx + 1:04d}"
        csv_rows.append(conflict.to_csv_row(conflict_id))
        text_lines.append(
            f"{conflict_id}: Person {conflict.person_id} conflicts between {conflict.activity_1} "
            f"({conflict.start_1:%Y-%m-%d %H:%M}-{conflict.end_1:%Y-%m-%d %H:%M}) and {conflict.activity_2} "
            f"({conflict.start_2:%Y-%m-%d %H:%M}-{conflict.end_2:%Y-%m-%d %H:%M}) | "
            f"Overlap: {int(conflict.overlap_minutes)} minutes | Type: {conflict.conflict_type} | Severity: {conflict.severity}"
        )

    csv_path = os.path.join(output_dir, "conflict_report.csv")
    txt_path = os.path.join(output_dir, "conflict_report.txt")
    _write_csv(
        csv_path,
        [
            "Conflict ID",
            "Person",
            "Activities",
            "Schedule A",
            "Schedule B",
            "Overlap Start",
            "Overlap End",
            "Overlap (minutes)",
            "Conflict Type",
            "Severity",
        ],
        csv_rows,
    )
    with open(txt_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(text_lines))


def save_validation_report(details: Sequence[Dict[str, str]], output_dir: str) -> None:
    csv_path = os.path.join(output_dir, "validation_report.csv")
    _write_csv(
        csv_path,
        ["Person", "Conflict Key", "Activity 1", "Activity 2", "Status"],
        [[d["person_id"], d["conflict_key"], d["activity_1"], d["activity_2"], d["status"]] for d in details],
    )


def save_performance_report(
    performance_rows: Sequence[Tuple[str, int, float, float, float, float]], output_dir: str
) -> None:
    csv_path = os.path.join(output_dir, "performance_report.csv")
    _write_csv(
        csv_path,
        ["Algorithm", "Conflict Count", "Time (ms)", "Memory (KB)", "Precision", "Recall", "F1"],
        [
            [
                name,
                str(conflict_count),
                f"{time_ms:.3f}",
                f"{memory_kb:.2f}",
                f"{precision:.3f}",
                f"{recall:.3f}",
                f"{f1:.3f}",
            ]
            for name, conflict_count, time_ms, memory_kb, precision, recall, f1 in performance_rows
        ],
    )


def generate_gantt_chart(entries: Sequence[ScheduleEntry], conflicts: Sequence[ConflictRecord], output_dir: str) -> None:
    persons = sorted({entry.person_id for entry in entries})
    if not persons:
        return
    person_index = {person: idx for idx, person in enumerate(persons)}
    conflict_entry_ids = {id_ for conflict in conflicts for id_ in conflict.key[1:]}
    fig, ax = plt.subplots(figsize=(12, max(6, len(persons) * 0.3 + 2)))
    for entry in entries:
        idx = person_index[entry.person_id]
        start = mdates.date2num(entry.start)
        duration = (entry.end - entry.start).total_seconds() / (24 * 3600)
        color = "tab:red" if entry.entry_id in conflict_entry_ids else "tab:blue"
        ax.barh(idx, duration, left=start, height=0.6, color=color, alpha=0.7)
    ax.set_yticks(range(len(persons)))
    ax.set_yticklabels(persons)
    ax.set_xlabel("Time")
    ax.set_ylabel("Person")
    ax.set_title("Schedule Gantt Chart with Conflicts Highlighted")
    ax.xaxis_date()
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "gantt_chart.png"))
    plt.close(fig)


def generate_conflict_heatmap(conflicts: Sequence[ConflictRecord], output_dir: str) -> None:
    if not conflicts:
        return
    persons = sorted({conflict.person_id for conflict in conflicts})
    person_index = {person: idx for idx, person in enumerate(persons)}
    heatmap = [[0 for _ in range(24)] for _ in persons]
    for conflict in conflicts:
        hour = conflict.overlap_start.hour
        heatmap[person_index[conflict.person_id]][hour] += 1
    fig, ax = plt.subplots(figsize=(12, max(4, len(persons) * 0.3 + 2)))
    im = ax.imshow(heatmap, aspect="auto", cmap="Reds")
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(24)], rotation=45, ha="right")
    ax.set_yticks(range(len(persons)))
    ax.set_yticklabels(persons)
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Person")
    ax.set_title("Conflict Frequency Heatmap")
    fig.colorbar(im, ax=ax, label="Conflict Count")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "conflict_heatmap.png"))
    plt.close(fig)


def generate_performance_chart(performance_rows: Sequence[Tuple[str, int, float, float, float, float]], output_dir: str) -> None:
    algorithms = [row[0] for row in performance_rows]
    times_ms = [row[2] for row in performance_rows]
    memory_kb = [row[3] for row in performance_rows]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    positions = list(range(len(algorithms)))
    axes[0].bar(positions, times_ms, color="tab:blue")
    axes[0].set_ylabel("Time (ms)")
    axes[0].set_title("Execution Time")
    axes[0].set_xticks(positions)
    axes[1].bar(positions, memory_kb, color="tab:green")
    axes[1].set_ylabel("Peak Memory (KB)")
    axes[1].set_title("Memory Usage")
    axes[1].set_xticks(positions)
    for ax in axes:
        ax.set_xticklabels(algorithms, rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "algorithm_performance.png"))
    plt.close(fig)


def run_algorithm(
    name: str,
    func,
    grouped_entries: Dict[str, List[ScheduleEntry]],
    known_conflicts: Dict[Tuple[str, int, int], ConflictRecord],
) -> Tuple[str, Dict[Tuple[str, int, int], ConflictRecord], float, float, float, float, float]:
    tracemalloc.start()
    start = time.perf_counter()
    conflicts = func(grouped_entries)
    elapsed_ms = (time.perf_counter() - start) * 1000
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    precision, recall, f1, _ = evaluate_conflicts(conflicts, known_conflicts)
    return (
        name,
        conflicts,
        elapsed_ms,
        peak / 1024.0,
        precision,
        recall,
        f1,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Multi-Person Schedule Conflict Detection System")
    parser.add_argument("--input", required=True, help="Path to schedule CSV file")
    parser.add_argument("--known", required=True, help="Path to known conflicts JSON file")
    parser.add_argument("--output", required=True, help="Directory to store generated reports")
    args = parser.parse_args(argv)

    entries = parse_schedule(args.input)
    grouped = group_entries_by_person(entries)
    known_conflicts = load_known_conflicts(args.known, entries)

    os.makedirs(args.output, exist_ok=True)

    algorithms = [
        ("Brute Force", detect_conflicts_bruteforce),
        ("Sweep Line", detect_conflicts_sweepline),
        ("Interval Tree", detect_conflicts_interval_tree),
    ]

    performance_rows: List[Tuple[str, int, float, float, float, float]] = []
    collected_conflicts: Dict[str, Dict[Tuple[str, int, int], ConflictRecord]] = {}
    for name, func in algorithms:
        result = run_algorithm(name, func, grouped, known_conflicts)
        _, conflicts, elapsed_ms, memory_kb, precision, recall, f1 = result
        performance_rows.append((name, len(conflicts), elapsed_ms, memory_kb, precision, recall, f1))
        collected_conflicts[name] = conflicts

    base_conflicts = collected_conflicts["Brute Force"]
    precision, recall, f1, validation_details = evaluate_conflicts(base_conflicts, known_conflicts)

    save_conflict_reports(list(base_conflicts.values()), args.output)
    save_validation_report(validation_details, args.output)
    save_performance_report(performance_rows, args.output)
    generate_gantt_chart(entries, list(base_conflicts.values()), args.output)
    generate_conflict_heatmap(list(base_conflicts.values()), args.output)
    generate_performance_chart(performance_rows, args.output)

    metrics_summary_path = os.path.join(args.output, "metrics_summary.json")
    with open(metrics_summary_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "conflict_count": len(base_conflicts),
                "known_conflicts": len(known_conflicts),
                "algorithms": [
                    {
                        "name": name,
                        "conflict_count": conflicts,
                        "time_ms": time_ms,
                        "memory_kb": memory_kb,
                        "precision": prec,
                        "recall": rec,
                        "f1": f1_score,
                    }
                    for name, conflicts, time_ms, memory_kb, prec, rec, f1_score in performance_rows
                ],
            },
            handle,
            indent=2,
        )

    print("Conflict detection completed.")
    print(f"Precision: {precision:.3f} | Recall: {recall:.3f} | F1: {f1:.3f}")
    print(f"Reports saved to: {os.path.abspath(args.output)}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())
