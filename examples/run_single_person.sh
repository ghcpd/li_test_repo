#!/bin/bash
# Example: Analyze conflicts for a specific person

PERSON_ID="P001"

echo "Analyzing conflicts for person: $PERSON_ID"
echo "=========================================="
echo ""

python ../schedule_conflict_detector.py \
  --input ../test_schedule.csv \
  --output ../report/ \
  --algorithm sweep \
  --filter-person $PERSON_ID \
  --verbose

echo ""
echo "Filtered results saved to report/ directory"
