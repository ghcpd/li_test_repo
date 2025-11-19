#!/bin/bash
# Example: Run fastest algorithm (Sweep Line) without visualizations

echo "Running Sweep Line Algorithm (Fast Mode)"
echo "========================================="
echo ""

python ../schedule_conflict_detector.py \
  --input ../test_schedule.csv \
  --known ../known_conflicts.json \
  --output ../report/ \
  --algorithm sweep \
  --no-viz \
  --verbose

echo ""
echo "Reports saved to report/ directory"
