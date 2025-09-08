# Multi-Person Schedule Conflict Detection System
# This tool reads schedule data and detects conflicts using multiple algorithms.
# Usage: python schedule_conflict_detector.py --input test_schedule.csv --known known_conflicts.json --output report/

import argparse
import csv
import json
import os
import tracemalloc
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Dict, Set, Optional

import matplotlib.pyplot as plt


@dataclass
class Schedule:
    idx: int
    person_id: str
    start: datetime
    end: datetime
    activity: str
    location: str


def parse_args():
    p = argparse.ArgumentParser(description="Multi-Person Schedule Conflict Detection System")
    p.add_argument("--input", required=True, help="Path to schedule CSV")
    p.add_argument("--known", required=True, help="Path to known_conflicts.json")
    p.add_argument("--output", required=True, help="Output directory for reports")
    return p.parse_args()


def read_schedules(path: str) -> List[Schedule]:
    items: List[Schedule] = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for i, row in enumerate(r):
            items.append(
                Schedule(
                    idx=i,
                    person_id=row.get("person_id", "").strip(),
                    start=datetime.strptime(row["start_time"], "%Y-%m-%d %H:%M"),
                    end=datetime.strptime(row["end_time"], "%Y-%m-%d %H:%M"),
                    activity=row.get("activity_name", "").strip(),
                    location=row.get("location", "").strip(),
                )
            )
    return items


def overlaps(a: Schedule, b: Schedule) -> bool:
    return a.person_id == b.person_id and a.start < b.end and b.start < a.end


def conflict_type(a: Schedule, b: Schedule) -> str:
    if a.start == b.start and a.end == b.end:
        return "full overlap"
    if a.start <= b.start and a.end >= b.end or b.start <= a.start and b.end >= a.end:
        return "containment"
    return "partial overlap"


def overlap_minutes(a: Schedule, b: Schedule) -> int:
    delta = min(a.end, b.end) - max(a.start, b.start)
    return max(0, int(delta.total_seconds() // 60))


def severity(minutes: int) -> str:
    if minutes >= 60:
        return "High"
    if minutes >= 15:
        return "Medium"
    return "Low"


# Visualization helpers: Gantt and heatmap

def draw_gantt(output_dir: str, schedules: List[Schedule]):
    try:
        by_person: Dict[str, List[Schedule]] = {}
        for s in schedules:
            by_person.setdefault(s.person_id, []).append(s)
        fig, ax = plt.subplots(figsize=(10, 6))
        yticks, ylabels = [], []
        y = 0
        for pid, items in sorted(by_person.items()):
            items.sort(key=lambda x: x.start)
            for it in items:
                ax.barh(y, (it.end - it.start).total_seconds() / 60, left=(it.start - items[0].start).total_seconds() / 60)
            yticks.append(y)
            ylabels.append(pid)
            y += 1
        ax.set_yticks(yticks)
        ax.set_yticklabels(ylabels)
        ax.set_xlabel("Minutes from first activity per person")
        ax.set_title("Gantt Chart of Schedules")
        fig.tight_layout()
        fig.savefig(os.path.join(output_dir, "gantt.png"))
        plt.close(fig)
    except Exception:
        pass


def draw_heatmap(output_dir: str, schedules: List[Schedule]):
    try:
        persons = sorted({s.person_id for s in schedules})
        base = min(s.start for s in schedules)
        max_minute = int(max(s.end for s in schedules).timestamp() - base.timestamp()) // 60 + 1
        grid = [[0] * max_minute for _ in persons]
        for s in schedules:
            i = persons.index(s.person_id)
            start = int((s.start.timestamp() - base.timestamp()) // 60)
            end = int((s.end.timestamp() - base.timestamp()) // 60)
            for m in range(start, end):
                grid[i][m] += 1
        import numpy as np
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.imshow(np.array(grid), aspect='auto', cmap='hot')
        ax.set_yticks(range(len(persons)))
        ax.set_yticklabels(persons)
        ax.set_title("Conflict Heatmap (counts of activities per minute)")
        fig.tight_layout()
        fig.savefig(os.path.join(output_dir, "heatmap.png"))
        plt.close(fig)
    except Exception:
        pass


def brute_force_conflicts(s: List[Schedule]):
    conflicts = []
    n = len(s)
    for i in range(n):
        for j in range(i + 1, n):
            if overlaps(s[i], s[j]):
                conflicts.append((s[i], s[j]))
    return conflicts


def sweep_line_conflicts(s: List[Schedule]):
    # Group by person and sweep for overlaps
    conflicts: List[Tuple[Schedule, Schedule]] = []
    by_person: Dict[str, List[Schedule]] = {}
    for item in s:
        by_person.setdefault(item.person_id, []).append(item)
    for pid, lst in by_person.items():
        lst.sort(key=lambda x: x.start)
        active: List[Schedule] = []
        ai = 0
        for cur in lst:
            active = [x for x in active if x.end > cur.start]
            for x in active:
                conflicts.append((x, cur))
            active.append(cur)
    return conflicts


@dataclass
class ITNode:
    start: datetime
    end: datetime
    max_end: datetime
    item: Schedule
    left: Optional['ITNode'] = None
    right: Optional['ITNode'] = None


def it_insert(root: Optional[ITNode], node: ITNode) -> ITNode:
    if root is None:
        return node
    if node.start <= root.start:
        root.left = it_insert(root.left, node)
    else:
        root.right = it_insert(root.right, node)
    if node.end > root.max_end:
        root.max_end = node.end
    return root


def it_search(root: Optional[ITNode], start: datetime, end: datetime, out: List[Schedule]):
    if root is None:
        return
    if root.start < end and start < root.end:
        out.append(root.item)
    if root.left and root.left.max_end > start:
        it_search(root.left, start, end, out)
    if root.right and root.start < end:
        it_search(root.right, start, end, out)


def interval_tree_conflicts(s: List[Schedule]):
    conflicts: List[Tuple[Schedule, Schedule]] = []
    by_person: Dict[str, List[Schedule]] = {}
    for item in s:
        by_person.setdefault(item.person_id, []).append(item)
    for pid, lst in by_person.items():
        root: Optional[ITNode] = None
        for item in lst:
            node = ITNode(item.start, item.end, item.end, item)
            root = it_insert(root, node)
        seen: Set[Tuple[int, int]] = set()
        for item in lst:
            hits: List[Schedule] = []
            it_search(root, item.start, item.end, hits)
            for other in hits:
                if other.idx == item.idx:
                    continue
                a, b = (item, other) if item.idx < other.idx else (other, item)
                if (a.idx, b.idx) not in seen:
                    seen.add((a.idx, b.idx))
                    if overlaps(a, b):
                        conflicts.append((a, b))
    return conflicts


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def write_conflict_report(path: str, conflicts: List[Tuple[Schedule, Schedule]]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "conflict_id",
            "person_id",
            "activity_1",
            "activity_2",
            "start_time",
            "end_time",
            "conflict_type",
            "overlap_minutes",
            "severity",
        ])
        for k, (a, b) in enumerate(conflicts, start=1):
            ct = conflict_type(a, b)
            om = overlap_minutes(a, b)
            w.writerow([
                k,
                a.person_id,
                a.activity,
                b.activity,
                max(a.start, b.start).strftime("%Y-%m-%d %H:%M"),
                min(a.end, b.end).strftime("%Y-%m-%d %H:%M"),
                ct,
                om,
                severity(om),
            ])


# Validation utilities

def to_key(a: Schedule, b: Schedule) -> Tuple[str, str, str, str, str, str, str]:
    # Normalize order by earlier start
    first, second = (a, b) if a.start <= b.start else (b, a)
    return (
        first.person_id,
        first.start.strftime("%Y-%m-%d %H:%M"),
        first.end.strftime("%Y-%m-%d %H:%M"),
        second.start.strftime("%Y-%m-%d %H:%M"),
        second.end.strftime("%Y-%m-%d %H:%M"),
        first.activity,
        second.activity,
    )


def read_known(path: str) -> Set[Tuple[str, str, str, str, str, str, str]]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    out: Set[Tuple[str, str, str, str, str, str, str]] = set()
    for item in raw:
        pid = item["person_id"]
        s1 = item["original_schedule"]
        s2 = item["conflict_schedule"]
        a1 = item["activity_1"]
        a2 = item["activity_2"]
        st1, en1 = [x.strip() for x in s1.split(" - ")]
        st2, en2 = [x.strip() for x in s2.split(" - ")]
        d1s = datetime.strptime(st1, "%Y-%m-%d %H:%M")
        d2s = datetime.strptime(st2, "%Y-%m-%d %H:%M")
        # Normalize order
        if d1s <= d2s:
            out.add((pid, st1, en1, st2, en2, a1, a2))
        else:
            out.add((pid, st2, en2, st1, en1, a2, a1))
    return out


def validate_and_write(path: str, detected: List[Tuple[Schedule, Schedule]], known: Set[Tuple[str, str, str, str, str, str, str]]) -> Dict[str, float]:
    detected_keys = [to_key(a, b) for a, b in detected]
    det_set = set(detected_keys)
    tp = det_set & known
    fp = det_set - known
    fn = known - det_set

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["status", "person_id", "activity_1", "activity_2", "original_schedule", "conflict_schedule"])
        for key in detected_keys:
            status = "TP" if key in known else "FP"
            w.writerow([status, key[0], key[5], key[6], f"{key[1]} - {key[2]}", f"{key[3]} - {key[4]}"])
        for key in fn:
            w.writerow(["FN", key[0], key[5], key[6], f"{key[1]} - {key[2]}", f"{key[3]} - {key[4]}"])

    precision = len(tp) / (len(tp) + len(fp)) if (len(tp) + len(fp)) else 0.0
    recall = len(tp) / (len(tp) + len(fn)) if (len(tp) + len(fn)) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def main():
    args = parse_args()
    ensure_dir(args.output)
    schedules = read_schedules(args.input)

    # Run algorithms and benchmark
    results: Dict[str, Dict[str, object]] = {}
    algos = {
        "brute": brute_force_conflicts,
        "sweep": sweep_line_conflicts,
        "interval": interval_tree_conflicts,
    }
    for name, fn in algos.items():
        tracemalloc.start()
        t0 = datetime.now()
        confs = fn(schedules)
        t1 = datetime.now()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        results[name] = {"conflicts": confs, "time_ms": (t1 - t0).total_seconds() * 1000, "peak_mb": peak / 1024 / 1024}

    # Keep existing report behavior using brute force output
    write_conflict_report(os.path.join(args.output, "conflicts.csv"), results["brute"]["conflicts"])  # type: ignore

    known = read_known(args.known)
    # Validation per algorithm
    with open(os.path.join(args.output, "performance.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["algorithm", "time_ms", "peak_mb", "precision", "recall", "f1"])    
        for name in ["brute", "sweep", "interval"]:
            metrics = validate_and_write(os.path.join(args.output, f"validation_{name}.csv"), results[name]["conflicts"], known)  # type: ignore
            w.writerow([name, f"{results[name]['time_ms']:.2f}", f"{results[name]['peak_mb']:.2f}", f"{metrics['precision']:.3f}", f"{metrics['recall']:.3f}", f"{metrics['f1']:.3f}"])  # type: ignore

    # Simple performance chart
    try:
        labels = list(results.keys())
        times = [results[k]["time_ms"] for k in labels]  # type: ignore
        mems = [results[k]["peak_mb"] for k in labels]  # type: ignore
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(labels, times, color=["#66c2a5", "#fc8d62", "#8da0cb"])
        ax.set_title("Algorithm Execution Time (ms)")
        ax.set_ylabel("ms")
        fig.tight_layout()
        fig.savefig(os.path.join(args.output, "performance_time.png"))
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(labels, mems, color=["#8da0cb", "#66c2a5", "#fc8d62"])
        ax.set_title("Algorithm Peak Memory (MB)")
        ax.set_ylabel("MB")
        fig.tight_layout()
        fig.savefig(os.path.join(args.output, "performance_memory.png"))
        plt.close(fig)

        # Draw visualizations
        draw_gantt(args.output, schedules)
        draw_heatmap(args.output, schedules)
    except Exception:
        pass

    print(f"Detected {len(results['brute']['conflicts'])} conflicts. Reports written to {args.output}.")  # type: ignore
    for name in ["brute", "sweep", "interval"]:
        print(f"{name} time: {results[name]['time_ms']:.2f} ms, peak memory: {results[name]['peak_mb']:.2f} MB")  # type: ignore


if __name__ == "__main__":
    main()
