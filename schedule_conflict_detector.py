# Multi-Person Schedule Conflict Detection System
# This tool reads schedule data and detects conflicts using multiple algorithms.
# Usage: python schedule_conflict_detector.py --input test_schedule.csv --known known_conflicts.json --output report/

import argparse
import csv
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple


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


def main():
    args = parse_args()
    ensure_dir(args.output)
    schedules = read_schedules(args.input)
    conflicts = brute_force_conflicts(schedules)
    write_conflict_report(os.path.join(args.output, "conflicts.csv"), conflicts)
    print(f"Detected {len(conflicts)} conflicts. Report written to {args.output}.")


if __name__ == "__main__":
    main()
