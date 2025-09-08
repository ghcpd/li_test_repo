#!/usr/bin/env python3
import argparse
import csv
import json
import os
import sys
import time
import tracemalloc
from collections import defaultdict, namedtuple
from datetime import datetime
from typing import List, Dict, Tuple, Any, Set

# Data structures
Schedule = namedtuple("Schedule", ["id", "person_id", "start", "end", "activity", "location", "scenario", "start_str", "end_str"])

class Conflict:
    __slots__ = (
        "person_id",
        "activity_1",
        "activity_2",
        "schedule_1",
        "schedule_2",
        "overlap_start",
        "overlap_end",
        "conflict_type",
        "overlap_minutes",
        "severity",
        "id"
    )

    def __init__(self, person_id: str, a1: str, a2: str, s1: str, s2: str,
                 o_start: datetime, o_end: datetime, ctype: str, minutes: int, severity: str, cid: int) -> None:
        self.person_id = person_id
        self.activity_1 = a1
        self.activity_2 = a2
        self.schedule_1 = s1
        self.schedule_2 = s2
        self.overlap_start = o_start
        self.overlap_end = o_end
        self.conflict_type = ctype
        self.overlap_minutes = minutes
        self.severity = severity
        self.id = cid

    def key_unordered(self) -> Tuple[str, str, str, str, str]:
        a1, a2 = sorted([self.activity_1, self.activity_2])
        s1, s2 = sorted([self.schedule_1, self.schedule_2])
        return (self.person_id, a1, a2, s1, s2)

# Utilities
TIME_FMT = "%Y-%m-%d %H:%M"

def parse_time(s: str) -> datetime:
    return datetime.strptime(s.strip(), TIME_FMT)


def overlap(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> Tuple[bool, datetime, datetime]:
    latest_start = max(a_start, b_start)
    earliest_end = min(a_end, b_end)
    if latest_start < earliest_end:
        return True, latest_start, earliest_end
    return False, latest_start, earliest_end


def conflict_type(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> str:
    if a_start == b_start and a_end == b_end:
        return "full overlap"
    # containment
    if a_start <= b_start and a_end >= b_end:
        return "containment"
    if b_start <= a_start and b_end >= a_end:
        return "containment"
    return "partial overlap"


def severity_rating(minutes: int) -> str:
    if minutes < 15:
        return "Low"
    if minutes < 45:
        return "Medium"
    return "High"


# Algorithms

def detect_conflicts_bruteforce(schedules_by_person: Dict[str, List[Schedule]]) -> List[Conflict]:
    conflicts: List[Conflict] = []
    cid = 1
    for person, items in schedules_by_person.items():
        n = len(items)
        for i in range(n):
            for j in range(i + 1, n):
                s1 = items[i]
                s2 = items[j]
                has, o_start, o_end = overlap(s1.start, s1.end, s2.start, s2.end)
                if has:
                    minutes = int((o_end - o_start).total_seconds() // 60)
                    ctype = conflict_type(s1.start, s1.end, s2.start, s2.end)
                    conflicts.append(
                        Conflict(
                            s1.person_id,
                            s1.activity,
                            s2.activity,
                            f"{s1.start_str} - {s1.end_str}",
                            f"{s2.start_str} - {s2.end_str}",
                            o_start,
                            o_end,
                            ctype,
                            minutes,
                            severity_rating(minutes),
                            cid,
                        )
                    )
                    cid += 1
    return conflicts


def detect_conflicts_sweepline(schedules_by_person: Dict[str, List[Schedule]]) -> List[Conflict]:
    conflicts: List[Conflict] = []
    cid = 1
    for person, items in schedules_by_person.items():
        items_sorted = sorted(items, key=lambda s: (s.start, s.end))
        active: List[Schedule] = []
        for s in items_sorted:
            # remove non-overlapping
            active = [a for a in active if a.end > s.start]
            for a in active:
                has, o_start, o_end = overlap(a.start, a.end, s.start, s.end)
                if has:
                    minutes = int((o_end - o_start).total_seconds() // 60)
                    ctype = conflict_type(a.start, a.end, s.start, s.end)
                    conflicts.append(
                        Conflict(
                            s.person_id,
                            a.activity,
                            s.activity,
                            f"{a.start_str} - {a.end_str}",
                            f"{s.start_str} - {s.end_str}",
                            o_start,
                            o_end,
                            ctype,
                            minutes,
                            severity_rating(minutes),
                            cid,
                        )
                    )
                    cid += 1
            active.append(s)
    return conflicts


# Simple Interval Tree
class IntervalNode:
    __slots__ = ("start", "end", "max_end", "left", "right", "payload")

    def __init__(self, start: datetime, end: datetime, payload: Schedule):
        self.start = start
        self.end = end
        self.max_end = end
        self.left = None
        self.right = None
        self.payload = payload

    def insert(self, start: datetime, end: datetime, payload: Schedule):
        if start < self.start:
            if self.left:
                self.left.insert(start, end, payload)
            else:
                self.left = IntervalNode(start, end, payload)
        else:
            if self.right:
                self.right.insert(start, end, payload)
            else:
                self.right = IntervalNode(start, end, payload)
        if end > self.max_end:
            self.max_end = end

    def search_overlaps(self, start: datetime, end: datetime, result: List[Schedule]):
        if self.left and self.left.max_end > start:
            self.left.search_overlaps(start, end, result)
        if self.start < end and start < self.end:
            result.append(self.payload)
        if self.right and self.start < end:
            self.right.search_overlaps(start, end, result)


def detect_conflicts_intervaltree(schedules_by_person: Dict[str, List[Schedule]]) -> List[Conflict]:
    conflicts: List[Conflict] = []
    cid = 1
    for person, items in schedules_by_person.items():
        root: IntervalNode = None
        for s in items:
            if root is None:
                root = IntervalNode(s.start, s.end, s)
            else:
                root.insert(s.start, s.end, s)
        if root is None:
            continue
        seen_pairs: Set[Tuple[int, int]] = set()
        for s in items:
            overlaps_list: List[Schedule] = []
            root.search_overlaps(s.start, s.end, overlaps_list)
            for a in overlaps_list:
                if a.id == s.id:
                    continue
                i, j = sorted((a.id, s.id))
                if (i, j) in seen_pairs:
                    continue
                seen_pairs.add((i, j))
                has, o_start, o_end = overlap(a.start, a.end, s.start, s.end)
                if has:
                    minutes = int((o_end - o_start).total_seconds() // 60)
                    ctype = conflict_type(a.start, a.end, s.start, s.end)
                    conflicts.append(
                        Conflict(
                            s.person_id,
                            a.activity,
                            s.activity,
                            f"{a.start_str} - {a.end_str}",
                            f"{s.start_str} - {s.end_str}",
                            o_start,
                            o_end,
                            ctype,
                            minutes,
                            severity_rating(minutes),
                            cid,
                        )
                    )
                    cid += 1
    return conflicts


# Reporting and validation

def load_schedules(csv_path: str) -> Dict[str, List[Schedule]]:
    schedules_by_person: Dict[str, List[Schedule]] = defaultdict(list)
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        idx = 1
        for row in reader:
            person_id = row.get("person_id").strip()
            start_str = row.get("start_time").strip()
            end_str = row.get("end_time").strip()
            activity = row.get("activity_name").strip()
            location = row.get("location", "").strip()
            scenario = row.get("scenario", "").strip()
            s = Schedule(
                idx,
                person_id,
                parse_time(start_str),
                parse_time(end_str),
                activity,
                location,
                scenario,
                start_str,
                end_str,
            )
            schedules_by_person[person_id].append(s)
            idx += 1
    return schedules_by_person


def conflicts_to_csv(conflicts: List[Conflict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "conflict_id",
            "person_id",
            "activity_1",
            "activity_2",
            "time_interval",
            "conflict_type",
            "overlap_minutes",
            "severity",
        ])
        for c in conflicts:
            time_interval = f"{c.overlap_start.strftime(TIME_FMT)} - {c.overlap_end.strftime(TIME_FMT)}"
            writer.writerow([
                c.id,
                c.person_id,
                c.activity_1,
                c.activity_2,
                time_interval,
                c.conflict_type,
                c.overlap_minutes,
                c.severity,
            ])


def load_known_conflicts(path: str) -> Set[Tuple[str, str, str, str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    keys: Set[Tuple[str, str, str, str, str]] = set()
    for item in data:
        person_id = item["person_id"].strip()
        a1 = item["activity_1"].strip()
        a2 = item["activity_2"].strip()
        s1 = item["original_schedule"].strip()
        s2 = item["conflict_schedule"].strip()
        a1, a2 = sorted([a1, a2])
        s1, s2 = sorted([s1, s2])
        keys.add((person_id, a1, a2, s1, s2))
    return keys


def validate_conflicts(conflicts: List[Conflict], known_keys: Set[Tuple[str, str, str, str, str]], path: str) -> Tuple[int, int, int, float, float, float]:
    detected_keys: Set[Tuple[str, str, str, str, str]] = set()
    for c in conflicts:
        detected_keys.add(c.key_unordered())

    tp_keys = detected_keys & known_keys
    fp_keys = detected_keys - known_keys
    fn_keys = known_keys - detected_keys

    precision = len(tp_keys) / (len(tp_keys) + len(fp_keys)) if (len(tp_keys) + len(fp_keys)) > 0 else 0.0
    recall = len(tp_keys) / (len(tp_keys) + len(fn_keys)) if (len(tp_keys) + len(fn_keys)) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    # Write validation report
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["person_id", "activity_1", "activity_2", "schedule_1", "schedule_2", "status"])
        for k in tp_keys:
            writer.writerow([k[0], k[1], k[2], k[3], k[4], "TP"])
        for k in fp_keys:
            writer.writerow([k[0], k[1], k[2], k[3], k[4], "FP"])
        for k in fn_keys:
            writer.writerow([k[0], k[1], k[2], k[3], k[4], "FN"])

    return len(tp_keys), len(fp_keys), len(fn_keys), precision, recall, f1


def measure_performance(func, *args, **kwargs) -> Tuple[Any, float, int]:
    tracemalloc.start()
    t0 = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed_ms, peak


def write_performance_csv(path: str, rows: List[List[Any]]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["algorithm", "exec_time_ms", "peak_memory_bytes", "precision", "recall", "f1"]) 
        writer.writerows(rows)


def visualize(output_dir: str, schedules_by_person: Dict[str, List[Schedule]], perf_rows: List[List[Any]]):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors
    except Exception as e:
        print(f"Visualization skipped: {e}")
        return

    # Gantt chart
    persons = sorted(schedules_by_person.keys())
    fig_height = max(6, len(persons) * 0.3)
    fig, ax = plt.subplots(figsize=(12, fig_height))
    y_ticks = []
    y_labels = []
    color_map = list(mcolors.TABLEAU_COLORS.values())
    color_idx = {}

    y = 0
    for person in persons:
        items = sorted(schedules_by_person[person], key=lambda s: (s.start, s.end))
        for s in items:
            if s.activity not in color_idx:
                color_idx[s.activity] = color_map[len(color_idx) % len(color_map)]
            ax.barh(y, (s.end - s.start).total_seconds() / 60, left=s.start.timestamp() / 60, height=0.4, color=color_idx[s.activity])
        y_ticks.append(y)
        y_labels.append(person)
        y += 1
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("Minutes since epoch")
    ax.set_title("Gantt Chart of Activities per Person")
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    fig.savefig(os.path.join(output_dir, "gantt_chart.png"))
    plt.close(fig)

    # Conflict heatmap: count conflicts per person per hour of day
    # Build conflicts from brute force (as representative)
    conflicts = detect_conflicts_bruteforce(schedules_by_person)
    hours = list(range(24))
    heat = [[0 for _ in hours] for _ in persons]
    for c in conflicts:
        h = c.overlap_start.hour
        i = persons.index(c.person_id)
        heat[i][h] += 1

    fig, ax = plt.subplots(figsize=(12, max(6, len(persons) * 0.3)))
    im = ax.imshow(heat, aspect='auto', cmap='Reds')
    ax.set_yticks(range(len(persons)))
    ax.set_yticklabels(persons)
    ax.set_xticks(hours)
    ax.set_xticklabels([str(h) for h in hours])
    ax.set_xlabel("Hour of Day")
    ax.set_title("Conflict Heatmap (counts by person and hour)")
    fig.colorbar(im, ax=ax)
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, "conflict_heatmap.png"))
    plt.close(fig)

    # Performance chart
    labels = [r[0] for r in perf_rows]
    times = [r[1] for r in perf_rows]
    mems = [r[2] / (1024 * 1024) for r in perf_rows]  # in MB

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].bar(labels, times, color='skyblue')
    axes[0].set_ylabel("Time (ms)")
    axes[0].set_title("Execution Time by Algorithm")

    axes[1].bar(labels, mems, color='salmon')
    axes[1].set_ylabel("Peak Memory (MB)")
    axes[1].set_title("Peak Memory by Algorithm")

    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, "performance.png"))
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Multi-Person Schedule Conflict Detection System")
    parser.add_argument("--input", required=True, help="Path to input CSV file (e.g., test_schedule.csv)")
    parser.add_argument("--known", required=True, help="Path to known conflicts JSON file")
    parser.add_argument("--output", required=True, help="Directory to write reports to")
    args = parser.parse_args()

    csv_path = os.path.abspath(args.input)
    known_path = os.path.abspath(args.known)
    output_dir = os.path.abspath(args.output)

    if not os.path.exists(csv_path):
        print(f"Input file not found: {csv_path}")
        sys.exit(1)
    if not os.path.exists(known_path):
        print(f"Known conflicts file not found: {known_path}")
        sys.exit(1)

    schedules_by_person = load_schedules(csv_path)

    # Run algorithms and measure performance
    perf_rows: List[List[Any]] = []

    conflicts_bf, t_bf, m_bf = measure_performance(detect_conflicts_bruteforce, schedules_by_person)
    conflicts_to_csv(conflicts_bf, os.path.join(output_dir, "conflict_report_bruteforce.csv"))
    known_keys = load_known_conflicts(known_path)
    tp, fp, fn, p, r, f1 = validate_conflicts(conflicts_bf, known_keys, os.path.join(output_dir, "validation_report_bruteforce.csv"))
    perf_rows.append(["bruteforce", round(t_bf, 3), m_bf, round(p, 4), round(r, 4), round(f1, 4)])

    conflicts_sl, t_sl, m_sl = measure_performance(detect_conflicts_sweepline, schedules_by_person)
    conflicts_to_csv(conflicts_sl, os.path.join(output_dir, "conflict_report_sweepline.csv"))
    tp, fp, fn, p, r, f1 = validate_conflicts(conflicts_sl, known_keys, os.path.join(output_dir, "validation_report_sweepline.csv"))
    perf_rows.append(["sweepline", round(t_sl, 3), m_sl, round(p, 4), round(r, 4), round(f1, 4)])

    conflicts_it, t_it, m_it = measure_performance(detect_conflicts_intervaltree, schedules_by_person)
    conflicts_to_csv(conflicts_it, os.path.join(output_dir, "conflict_report_intervaltree.csv"))
    tp, fp, fn, p, r, f1 = validate_conflicts(conflicts_it, known_keys, os.path.join(output_dir, "validation_report_intervaltree.csv"))
    perf_rows.append(["intervaltree", round(t_it, 3), m_it, round(p, 4), round(r, 4), round(f1, 4)])

    write_performance_csv(os.path.join(output_dir, "performance.csv"), perf_rows)

    # Visualization
    visualize(output_dir, schedules_by_person, perf_rows)

    print(f"Reports generated in: {output_dir}")


if __name__ == "__main__":
    main()
