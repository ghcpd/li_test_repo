import argparse
import csv
import gc
import json
import os
import time
import tracemalloc
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from statistics import median
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

DATE_FORMAT = "%Y-%m-%d %H:%M"
GANTT_MAX_PERSONS = 10
HEATMAP_MAX_DATES = 12


@dataclass(frozen=True)
class ScheduleEntry:
    identifier: int
    person_id: str
    start_time: datetime
    end_time: datetime
    activity_name: str
    location: str


@dataclass
class ConflictResult:
    conflict_id: str
    algorithm: str
    event_a: ScheduleEntry
    event_b: ScheduleEntry
    overlap_start: datetime
    overlap_end: datetime
    conflict_type: str
    overlap_minutes: float
    severity: str

    @property
    def person_ids(self) -> Tuple[str, str]:
        return self.event_a.person_id, self.event_b.person_id

    @property
    def activity_names(self) -> Tuple[str, str]:
        return self.event_a.activity_name, self.event_b.activity_name

    def canonical_key(self) -> Tuple[Tuple[str, str, str, str], Tuple[str, str, str, str]]:
        event_a_key = (
            self.event_a.person_id,
            self.event_a.start_time.strftime(DATE_FORMAT),
            self.event_a.end_time.strftime(DATE_FORMAT),
            self.event_a.activity_name,
        )
        event_b_key = (
            self.event_b.person_id,
            self.event_b.start_time.strftime(DATE_FORMAT),
            self.event_b.end_time.strftime(DATE_FORMAT),
            self.event_b.activity_name,
        )
        return tuple(sorted([event_a_key, event_b_key]))  # type: ignore[return-value]


@dataclass
class KnownConflict:
    person_id: str
    activity_1: str
    activity_2: str
    event_a_start: datetime
    event_a_end: datetime
    event_b_start: datetime
    event_b_end: datetime

    def canonical_key(self) -> Tuple[Tuple[str, str, str, str], Tuple[str, str, str, str]]:
        event_a_key = (
            self.person_id,
            self.event_a_start.strftime(DATE_FORMAT),
            self.event_a_end.strftime(DATE_FORMAT),
            self.activity_1,
        )
        event_b_key = (
            self.person_id,
            self.event_b_start.strftime(DATE_FORMAT),
            self.event_b_end.strftime(DATE_FORMAT),
            self.activity_2,
        )
        return tuple(sorted([event_a_key, event_b_key]))  # type: ignore[return-value]

    def overlap_window(self) -> Tuple[datetime, datetime]:
        overlap_start = max(self.event_a_start, self.event_b_start)
        overlap_end = min(self.event_a_end, self.event_b_end)
        return overlap_start, overlap_end


class IntervalTreeNode:
    __slots__ = ("center", "intervals", "left", "right")

    def __init__(
        self,
        center: float,
        intervals: List[ScheduleEntry],
        left: Optional["IntervalTreeNode"],
        right: Optional["IntervalTreeNode"],
    ) -> None:
        self.center = center
        self.intervals = intervals
        self.left = left
        self.right = right


def parse_datetime(value: str) -> datetime:
    return datetime.strptime(value.strip(), DATE_FORMAT)


def load_schedule(input_path: str) -> List[ScheduleEntry]:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Schedule file not found: {input_path}")

    entries: List[ScheduleEntry] = []
    with open(input_path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        required_fields = {"person_id", "start_time", "end_time", "activity_name", "location"}
        missing_fields = required_fields - set(reader.fieldnames or [])
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"Missing required fields in schedule CSV: {missing}")

        for idx, row in enumerate(reader):
            if not row.get("person_id"):
                continue
            entry = ScheduleEntry(
                identifier=idx,
                person_id=row["person_id"].strip(),
                start_time=parse_datetime(row["start_time"]),
                end_time=parse_datetime(row["end_time"]),
                activity_name=row["activity_name"].strip(),
                location=row["location"].strip(),
            )
            entries.append(entry)
    return entries


def load_known_conflicts(path: str) -> List[KnownConflict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Known conflicts file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    known_conflicts: List[KnownConflict] = []
    for record in raw:
        person_id = record["person_id"].strip()
        activity_1 = record["activity_1"].strip()
        activity_2 = record["activity_2"].strip()
        event_a_start, event_a_end = [parse_datetime(ts) for ts in record["original_schedule"].split(" - ")]
        event_b_start, event_b_end = [parse_datetime(ts) for ts in record["conflict_schedule"].split(" - ")]
        known_conflicts.append(
            KnownConflict(
                person_id=person_id,
                activity_1=activity_1,
                activity_2=activity_2,
                event_a_start=event_a_start,
                event_a_end=event_a_end,
                event_b_start=event_b_start,
                event_b_end=event_b_end,
            )
        )
    return known_conflicts


def build_events_by_person(entries: Iterable[ScheduleEntry]) -> Dict[str, List[ScheduleEntry]]:
    events: Dict[str, List[ScheduleEntry]] = defaultdict(list)
    for entry in entries:
        events[entry.person_id].append(entry)
    for person in events:
        events[person].sort(key=lambda e: (e.start_time, e.end_time, e.identifier))
    return events


def determine_conflict_type(event_a: ScheduleEntry, event_b: ScheduleEntry) -> str:
    if (
        event_a.start_time == event_b.start_time
        and event_a.end_time == event_b.end_time
    ):
        return "full overlap"
    if (
        event_a.start_time <= event_b.start_time
        and event_a.end_time >= event_b.end_time
    ) or (
        event_b.start_time <= event_a.start_time
        and event_b.end_time >= event_a.end_time
    ):
        return "containment"
    return "partial overlap"


def severity_from_minutes(minutes: float) -> str:
    if minutes <= 15:
        return "Low"
    if minutes <= 45:
        return "Medium"
    return "High"


def build_conflict(
    event_a: ScheduleEntry,
    event_b: ScheduleEntry,
    algorithm: str,
    counter: int,
) -> ConflictResult:
    overlap_start = max(event_a.start_time, event_b.start_time)
    overlap_end = min(event_a.end_time, event_b.end_time)
    overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60
    conflict_type = determine_conflict_type(event_a, event_b)
    severity = severity_from_minutes(overlap_minutes)
    conflict_id = f"{algorithm[:2].upper()}-{counter:05d}"
    return ConflictResult(
        conflict_id=conflict_id,
        algorithm=algorithm,
        event_a=event_a,
        event_b=event_b,
        overlap_start=overlap_start,
        overlap_end=overlap_end,
        conflict_type=conflict_type,
        overlap_minutes=overlap_minutes,
        severity=severity,
    )


def detect_conflicts_brute_force(events_by_person: Dict[str, List[ScheduleEntry]]) -> List[ConflictResult]:
    conflicts: List[ConflictResult] = []
    counter = 1
    for person_events in events_by_person.values():
        n_events = len(person_events)
        for i in range(n_events):
            for j in range(i + 1, n_events):
                event_a = person_events[i]
                event_b = person_events[j]
                if event_a.end_time <= event_b.start_time or event_b.end_time <= event_a.start_time:
                    continue
                conflicts.append(build_conflict(event_a, event_b, "brute_force", counter))
                counter += 1
    return conflicts


def detect_conflicts_sweep_line(events_by_person: Dict[str, List[ScheduleEntry]]) -> List[ConflictResult]:
    conflicts: List[ConflictResult] = []
    counter = 1
    for person_events in events_by_person.values():
        active: List[ScheduleEntry] = []
        for event in person_events:
            active = [existing for existing in active if existing.end_time > event.start_time]
            for existing in active:
                if existing.end_time <= event.start_time:
                    continue
                conflicts.append(build_conflict(existing, event, "sweep_line", counter))
                counter += 1
            active.append(event)
        active.clear()
    return conflicts


def build_interval_tree(intervals: Sequence[ScheduleEntry]) -> Optional[IntervalTreeNode]:
    if not intervals:
        return None

    points = [event.start_time.timestamp() for event in intervals] + [event.end_time.timestamp() for event in intervals]
    center = median(points)

    left: List[ScheduleEntry] = []
    right: List[ScheduleEntry] = []
    overlapping: List[ScheduleEntry] = []

    for interval in intervals:
        start = interval.start_time.timestamp()
        end = interval.end_time.timestamp()
        if end < center:
            left.append(interval)
        elif start > center:
            right.append(interval)
        else:
            overlapping.append(interval)

    left_node = build_interval_tree(left)
    right_node = build_interval_tree(right)
    return IntervalTreeNode(center=center, intervals=overlapping, left=left_node, right=right_node)


def interval_tree_query(node: Optional[IntervalTreeNode], target: ScheduleEntry) -> Iterable[ScheduleEntry]:
    if node is None:
        return []

    results: List[ScheduleEntry] = []
    start = target.start_time.timestamp()
    end = target.end_time.timestamp()

    if start <= node.center <= end:
        for interval in node.intervals:
            if interval.identifier == target.identifier:
                continue
            if interval.end_time > target.start_time and interval.start_time < target.end_time:
                results.append(interval)

    if start < node.center and node.left is not None:
        results.extend(interval_tree_query(node.left, target))
    if end > node.center and node.right is not None:
        results.extend(interval_tree_query(node.right, target))
    return results


def detect_conflicts_interval_tree(events_by_person: Dict[str, List[ScheduleEntry]]) -> List[ConflictResult]:
    conflicts: List[ConflictResult] = []
    counter = 1
    for person_events in events_by_person.values():
        tree = build_interval_tree(person_events)
        seen_pairs = set()
        for event in person_events:
            for other in interval_tree_query(tree, event):
                pair = tuple(sorted((event.identifier, other.identifier)))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                if event.end_time <= other.start_time or other.end_time <= event.start_time:
                    continue
                conflicts.append(build_conflict(event, other, "interval_tree", counter))
                counter += 1
    return conflicts


def compute_validation_metrics(
    detected: Iterable[ConflictResult],
    known_conflicts: Iterable[KnownConflict],
) -> Tuple[int, int, int, float, float, float, Dict[Tuple[Tuple[str, str, str, str], Tuple[str, str, str, str]], ConflictResult]]:
    detected_map: Dict[Tuple[Tuple[str, str, str, str], Tuple[str, str, str, str]], ConflictResult] = {}
    for conflict in detected:
        key = conflict.canonical_key()
        if key not in detected_map:
            detected_map[key] = conflict

    known_map: Dict[Tuple[Tuple[str, str, str, str], Tuple[str, str, str, str]], KnownConflict] = {}
    for known in known_conflicts:
        key = known.canonical_key()
        if key not in known_map:
            known_map[key] = known

    detected_keys = set(detected_map.keys())
    known_keys = set(known_map.keys())

    true_positive = len(detected_keys & known_keys)
    false_positive = len(detected_keys - known_keys)
    false_negative = len(known_keys - detected_keys)

    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0.0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0.0
    if precision + recall == 0:
        f1_score = 0.0
    else:
        f1_score = 2 * (precision * recall) / (precision + recall)

    return (
        true_positive,
        false_positive,
        false_negative,
        precision,
        recall,
        f1_score,
        detected_map,
    )


def write_conflict_reports(
    output_dir: str,
    algorithm_conflicts: Dict[str, List[ConflictResult]],
) -> None:
    os.makedirs(output_dir, exist_ok=True)
    for algorithm, conflicts in algorithm_conflicts.items():
        filename = os.path.join(output_dir, f"conflicts_{algorithm}.csv")
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "conflict_id",
                    "algorithm",
                    "person_ids",
                    "activity_names",
                    "locations",
                    "overlap_start",
                    "overlap_end",
                    "conflict_type",
                    "overlap_minutes",
                    "severity",
                    "event_a_start",
                    "event_a_end",
                    "event_b_start",
                    "event_b_end",
                ]
            )
            for conflict in conflicts:
                writer.writerow(
                    [
                        conflict.conflict_id,
                        conflict.algorithm,
                        " & ".join(conflict.person_ids),
                        " vs ".join(conflict.activity_names),
                        f"{conflict.event_a.location} | {conflict.event_b.location}",
                        conflict.overlap_start.strftime(DATE_FORMAT),
                        conflict.overlap_end.strftime(DATE_FORMAT),
                        conflict.conflict_type,
                        round(conflict.overlap_minutes, 2),
                        conflict.severity,
                        conflict.event_a.start_time.strftime(DATE_FORMAT),
                        conflict.event_a.end_time.strftime(DATE_FORMAT),
                        conflict.event_b.start_time.strftime(DATE_FORMAT),
                        conflict.event_b.end_time.strftime(DATE_FORMAT),
                    ]
                )


def write_performance_summary(
    output_dir: str,
    performance: Dict[str, Dict[str, float]],
    metrics: Dict[str, Tuple[int, int, int, float, float, float]],
) -> None:
    filename = os.path.join(output_dir, "performance_summary.csv")
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "algorithm",
                "execution_ms",
                "memory_kb",
                "true_positive",
                "false_positive",
                "false_negative",
                "precision",
                "recall",
                "f1_score",
            ]
        )
        for algorithm in sorted(performance.keys()):
            exec_time = performance[algorithm]["execution_ms"]
            memory_kb = performance[algorithm]["memory_kb"]
            tp, fp, fn, precision, recall, f1_score = metrics[algorithm]
            writer.writerow(
                [
                    algorithm,
                    round(exec_time, 3),
                    round(memory_kb, 3),
                    tp,
                    fp,
                    fn,
                    round(precision, 3),
                    round(recall, 3),
                    round(f1_score, 3),
                ]
            )


def write_validation_report(
    output_dir: str,
    algorithm_conflicts: Dict[str, List[ConflictResult]],
    known_conflicts: List[KnownConflict],
) -> None:
    known_map = {known.canonical_key(): known for known in known_conflicts}
    filename = os.path.join(output_dir, "validation_report.csv")

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "algorithm",
                "status",
                "person_ids",
                "activity_names",
                "overlap_start",
                "overlap_end",
                "overlap_minutes",
                "conflict_type",
                "severity",
            ]
        )

        for algorithm, conflicts in algorithm_conflicts.items():
            detected_map = {conflict.canonical_key(): conflict for conflict in conflicts}
            detected_keys = set(detected_map.keys())
            known_keys = set(known_map.keys())

            for key in known_keys:
                known = known_map[key]
                overlap_start, overlap_end = known.overlap_window()
                overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60
                severity = severity_from_minutes(overlap_minutes)
                conflict_type = determine_conflict_type(
                    ScheduleEntry(-1, known.person_id, known.event_a_start, known.event_a_end, known.activity_1, ""),
                    ScheduleEntry(-2, known.person_id, known.event_b_start, known.event_b_end, known.activity_2, ""),
                )
                status = "true_positive" if key in detected_keys else "false_negative"
                writer.writerow(
                    [
                        algorithm,
                        status,
                        f"{known.person_id}",
                        f"{known.activity_1} vs {known.activity_2}",
                        overlap_start.strftime(DATE_FORMAT),
                        overlap_end.strftime(DATE_FORMAT),
                        round(overlap_minutes, 2),
                        conflict_type,
                        severity,
                    ]
                )

            for key in detected_keys - known_keys:
                conflict = detected_map[key]
                writer.writerow(
                    [
                        algorithm,
                        "false_positive",
                        " & ".join(conflict.person_ids),
                        " vs ".join(conflict.activity_names),
                        conflict.overlap_start.strftime(DATE_FORMAT),
                        conflict.overlap_end.strftime(DATE_FORMAT),
                        round(conflict.overlap_minutes, 2),
                        conflict.conflict_type,
                        conflict.severity,
                    ]
                )


def generate_gantt_chart(
    output_dir: str,
    events_by_person: Dict[str, List[ScheduleEntry]],
    conflicts: List[ConflictResult],
) -> None:
    if not conflicts:
        return

    conflict_counter = Counter()
    conflict_event_ids = set()
    for conflict in conflicts:
        conflict_counter.update(conflict.person_ids)
        conflict_event_ids.add(conflict.event_a.identifier)
        conflict_event_ids.add(conflict.event_b.identifier)

    top_persons = [person for person, _ in conflict_counter.most_common(GANTT_MAX_PERSONS)]
    if not top_persons:
        top_persons = list(events_by_person.keys())[:GANTT_MAX_PERSONS]

    fig, ax = plt.subplots(figsize=(14, 0.8 * max(len(top_persons), 2)))

    y_positions = {person: idx for idx, person in enumerate(top_persons)}

    for person, y in y_positions.items():
        for event in events_by_person.get(person, []):
            start = mdates.date2num(event.start_time)
            duration = (event.end_time - event.start_time).total_seconds() / 3600
            color = "#e57373" if event.identifier in conflict_event_ids else "#64b5f6"
            ax.broken_barh([(start, duration)], (y - 0.4, 0.8), facecolors=color, edgecolor="black")
            ax.text(
                start + duration / 2,
                y,
                event.activity_name,
                ha="center",
                va="center",
                fontsize=8,
                rotation=0,
            )

    ax.set_yticks(list(y_positions.values()))
    ax.set_yticklabels(list(y_positions.keys()))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d\n%H:%M"))
    ax.set_xlabel("Time")
    ax.set_title("Gantt Chart of Scheduled Activities and Conflicts")
    plt.tight_layout()
    filename = os.path.join(output_dir, "gantt_chart.png")
    plt.savefig(filename, dpi=200)
    plt.close(fig)


def generate_conflict_heatmap(
    output_dir: str,
    conflicts: List[ConflictResult],
) -> None:
    if not conflicts:
        return

    conflict_counter: Dict[Tuple[str, date], int] = defaultdict(int)
    for conflict in conflicts:
        overlap_date = conflict.overlap_start.date()
        for person in conflict.person_ids:
            conflict_counter[(person, overlap_date)] += 1

    persons = sorted({person for person, _ in conflict_counter.keys()})
    dates = sorted({conflict_date for _, conflict_date in conflict_counter.keys()})[:HEATMAP_MAX_DATES]
    if not persons or not dates:
        return

    selected_persons = persons[:GANTT_MAX_PERSONS]
    data = []
    for person in selected_persons:
        row = []
        for conflict_date in dates:
            row.append(conflict_counter.get((person, conflict_date), 0))
        data.append(row)

    fig, ax = plt.subplots(figsize=(1 + len(dates), 0.6 * max(len(selected_persons), 2)))
    cax = ax.imshow(data, cmap="Reds", aspect="auto")
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels([conflict_date.strftime("%Y-%m-%d") for conflict_date in dates], rotation=45, ha="right")
    ax.set_yticks(range(len(selected_persons)))
    ax.set_yticklabels(selected_persons)
    ax.set_xlabel("Date")
    ax.set_ylabel("Person")
    ax.set_title("Conflict Frequency Heatmap")
    fig.colorbar(cax, ax=ax, label="Conflicts")
    plt.tight_layout()
    filename = os.path.join(output_dir, "conflict_heatmap.png")
    plt.savefig(filename, dpi=200)
    plt.close(fig)


def generate_performance_chart(
    output_dir: str,
    performance: Dict[str, Dict[str, float]],
) -> None:
    if not performance:
        return

    algorithms = list(sorted(performance.keys()))
    times = [performance[algo]["execution_ms"] for algo in algorithms]
    memories = [performance[algo]["memory_kb"] for algo in algorithms]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(algorithms, times, color="#64b5f6", label="Execution Time (ms)")
    ax.set_ylabel("Execution Time (ms)", color="#1e88e5")
    ax.tick_params(axis="y", labelcolor="#1e88e5")
    ax2 = ax.twinx()
    ax2.plot(algorithms, memories, color="#e57373", marker="o", label="Memory (KB)")
    ax2.set_ylabel("Memory Usage (KB)", color="#e53935")
    ax2.tick_params(axis="y", labelcolor="#e53935")
    ax.set_title("Algorithm Performance Comparison")

    handles, labels = [], []
    for axis in [ax, ax2]:
        h, l = axis.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)
    ax.legend(handles, labels, loc="upper left")

    plt.tight_layout()
    filename = os.path.join(output_dir, "algorithm_performance.png")
    plt.savefig(filename, dpi=200)
    plt.close(fig)


def run_algorithms(
    events_by_person: Dict[str, List[ScheduleEntry]],
    known_conflicts: List[KnownConflict],
) -> Tuple[Dict[str, List[ConflictResult]], Dict[str, Dict[str, float]], Dict[str, Tuple[int, int, int, float, float, float]]]:
    algorithm_functions = {
        "brute_force": detect_conflicts_brute_force,
        "sweep_line": detect_conflicts_sweep_line,
        "interval_tree": detect_conflicts_interval_tree,
    }

    algorithm_conflicts: Dict[str, List[ConflictResult]] = {}
    performance: Dict[str, Dict[str, float]] = {}
    metrics: Dict[str, Tuple[int, int, int, float, float, float]] = {}

    for name, func in algorithm_functions.items():
        gc.collect()
        tracemalloc.start()
        start_time = time.perf_counter()
        conflicts = func(events_by_person)
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        performance[name] = {
            "execution_ms": elapsed_ms,
            "memory_kb": peak_mem / 1024,
        }
        algorithm_conflicts[name] = conflicts
        metrics_result = compute_validation_metrics(conflicts, known_conflicts)
        tp, fp, fn, precision, recall, f1_score, _ = metrics_result
        metrics[name] = (tp, fp, fn, precision, recall, f1_score)

    return algorithm_conflicts, performance, metrics


def run_detection_pipeline(input_path: str, known_path: str, output_dir: str) -> Dict[str, object]:
    entries = load_schedule(input_path)
    events_by_person = build_events_by_person(entries)
    known_conflicts = load_known_conflicts(known_path)

    algorithm_conflicts, performance, metrics = run_algorithms(events_by_person, known_conflicts)

    os.makedirs(output_dir, exist_ok=True)
    write_conflict_reports(output_dir, algorithm_conflicts)
    write_performance_summary(output_dir, performance, metrics)
    write_validation_report(output_dir, algorithm_conflicts, known_conflicts)

    all_conflicts = []
    for conflicts in algorithm_conflicts.values():
        all_conflicts.extend(conflicts)

    generate_gantt_chart(output_dir, events_by_person, all_conflicts)
    generate_conflict_heatmap(output_dir, all_conflicts)
    generate_performance_chart(output_dir, performance)

    return {
        "conflicts": algorithm_conflicts,
        "performance": performance,
        "metrics": metrics,
    }


def parse_arguments(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multi-Person Schedule Conflict Detection System",
    )
    parser.add_argument("--input", required=True, help="Path to the schedule CSV file")
    parser.add_argument("--known", required=True, help="Path to known conflicts JSON file")
    parser.add_argument(
        "--output",
        default=os.path.join(os.getcwd(), "report"),
        help="Directory to store generated reports",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_arguments(argv)
    summary = run_detection_pipeline(args.input, args.known, args.output)

    print("Schedule conflict detection complete.")
    print(f"Reports generated in: {args.output}")
    print("Performance summary:")
    for algorithm, stats in summary["performance"].items():
        metrics = summary["metrics"][algorithm]
        print(
            f"  - {algorithm}: time={stats['execution_ms']:.2f} ms, "
            f"memory={stats['memory_kb']:.2f} KB, precision={metrics[3]:.3f}, "
            f"recall={metrics[4]:.3f}, f1={metrics[5]:.3f}"
        )


if __name__ == "__main__":
    main()
