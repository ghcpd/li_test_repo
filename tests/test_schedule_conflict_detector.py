import unittest

from schedule_conflict_detector import (
    ScheduleEntry,
    compute_validation,
    detect_conflicts_brute_force,
    detect_conflicts_interval_tree,
    detect_conflicts_sweep_line,
    parse_datetime,
)


class ScheduleConflictDetectorTests(unittest.TestCase):
    def build_sample_schedule(self):
        return [
            ScheduleEntry(
                identifier="a-1",
                person_id="A",
                start_time=parse_datetime("2025-09-10 09:00"),
                end_time=parse_datetime("2025-09-10 10:00"),
                activity_name="Planning",
                location="Room 1",
            ),
            ScheduleEntry(
                identifier="a-2",
                person_id="A",
                start_time=parse_datetime("2025-09-10 09:30"),
                end_time=parse_datetime("2025-09-10 10:30"),
                activity_name="Review",
                location="Room 1",
            ),
            ScheduleEntry(
                identifier="a-3",
                person_id="A",
                start_time=parse_datetime("2025-09-10 10:45"),
                end_time=parse_datetime("2025-09-10 11:15"),
                activity_name="Standup",
                location="Room 2",
            ),
            ScheduleEntry(
                identifier="b-1",
                person_id="B",
                start_time=parse_datetime("2025-09-10 15:00"),
                end_time=parse_datetime("2025-09-10 16:00"),
                activity_name="Workshop",
                location="Room 3",
            ),
            ScheduleEntry(
                identifier="b-2",
                person_id="B",
                start_time=parse_datetime("2025-09-10 15:15"),
                end_time=parse_datetime("2025-09-10 15:45"),
                activity_name="Briefing",
                location="Room 3",
            ),
            ScheduleEntry(
                identifier="b-3",
                person_id="B",
                start_time=parse_datetime("2025-09-10 16:15"),
                end_time=parse_datetime("2025-09-10 16:45"),
                activity_name="Debrief",
                location="Room 3",
            ),
        ]

    def build_known_conflicts(self):
        return [
            {
                "person_id": "A",
                "original_schedule": "2025-09-10 09:00 - 2025-09-10 10:00",
                "conflict_schedule": "2025-09-10 09:30 - 2025-09-10 10:30",
                "activity_1": "Planning",
                "activity_2": "Review",
            },
            {
                "person_id": "B",
                "original_schedule": "2025-09-10 15:00 - 2025-09-10 16:00",
                "conflict_schedule": "2025-09-10 15:15 - 2025-09-10 15:45",
                "activity_1": "Workshop",
                "activity_2": "Briefing",
            },
        ]

    def test_algorithms_detect_same_conflicts(self):
        entries = self.build_sample_schedule()
        brute_conflicts = detect_conflicts_brute_force(entries)
        sweep_conflicts = detect_conflicts_sweep_line(entries)
        tree_conflicts = detect_conflicts_interval_tree(entries)

        self.assertEqual(set(brute_conflicts.keys()), set(sweep_conflicts.keys()))
        self.assertEqual(set(brute_conflicts.keys()), set(tree_conflicts.keys()))
        self.assertEqual(len(brute_conflicts), 2)

        conflict_types = {record.conflict_type for record in brute_conflicts.values()}
        self.assertIn("partial overlap", conflict_types)
        self.assertIn("containment", conflict_types)

    def test_validation_metrics_are_correct(self):
        entries = self.build_sample_schedule()
        conflicts = detect_conflicts_brute_force(entries)
        known = self.build_known_conflicts()
        rows, metrics = compute_validation(conflicts, known)

        self.assertEqual(len(rows), 2)
        self.assertAlmostEqual(metrics["precision"], 1.0)
        self.assertAlmostEqual(metrics["recall"], 1.0)
        self.assertAlmostEqual(metrics["f1_score"], 1.0)
        self.assertEqual(metrics["true_positive"], 2)
        self.assertEqual(metrics["false_positive"], 0)
        self.assertEqual(metrics["false_negative"], 0)


if __name__ == "__main__":
    unittest.main()