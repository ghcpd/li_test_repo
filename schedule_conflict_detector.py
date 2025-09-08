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
from typing import List, Tuple, Dict, Set

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


def brute_force_conflicts(s: List[Schedule]):
    conflicts = []
    n = len(s)
    for i in range(n):
        for j in range(i + 1, n):
            if overlaps(s[i], s[j]):
                conflicts.append((s[i], s[j]))
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

    # Performance tracking for brute force
    tracemalloc.start()
    t0 = datetime.now()
    conflicts = brute_force_conflicts(schedules)
    t1 = datetime.now()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    write_conflict_report(os.path.join(args.output, "conflicts.csv"), conflicts)

    known = read_known(args.known)
    metrics = validate_and_write(os.path.join(args.output, "validation.csv"), conflicts, known)

    print(f"Detected {len(conflicts)} conflicts. Report written to {args.output}.")
    print(f"Brute force time: {(t1 - t0).total_seconds()*1000:.2f} ms, peak memory: {peak/1024/1024:.2f} MB")
    print(f"Precision: {metrics['precision']:.3f}, Recall: {metrics['recall']:.3f}, F1: {metrics['f1']:.3f}")


if __name__ == "__main__":
    main()
