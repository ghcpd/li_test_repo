#!/bin/bash
# Example: Run all algorithms with full validation and visualization

echo "Running Multi-Person Schedule Conflict Detection System"
echo "========================================================"
echo ""

python ../schedule_conflict_detector.py \
  --input ../test_schedule.csv \
  --known ../known_conflicts.json \
  --output ../report/ \
  --algorithm all \
  --verbose

echo ""
echo "Results saved to report/ directory"
echo "Open the PNG files to view visualizations"
