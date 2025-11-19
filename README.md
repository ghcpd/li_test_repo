# li_test_repo

## Multi-Person Schedule Conflict Detection System

A comprehensive Python command-line tool for detecting and analyzing scheduling conflicts in multi-person, multi-activity scenarios.

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run conflict detection
python schedule_conflict_detector.py --input test_schedule.csv --known known_conflicts.json --output report/
```

### Features

- ✅ Three conflict detection algorithms (Brute Force, Sweep Line, Interval Tree)
- ✅ Performance benchmarking and comparison
- ✅ Validation against known conflicts with Precision/Recall/F1 metrics
- ✅ Detailed CSV reports with conflict classification
- ✅ Visual analytics (Gantt charts, heatmaps, performance graphs)
- ✅ Command-line interface with filtering options

### Documentation

- **[Complete Tool Documentation](README_TOOL.md)** - Full usage guide, API reference, and examples
- **[Example Scripts](examples/)** - Ready-to-use shell scripts for common scenarios

### Sample Results

Tested with 12,074 schedule entries across 100 people:
- **Sweep Line Algorithm**: 63ms, 3,766 conflicts detected (fastest)
- **Metrics**: Precision=37.17%, Recall=88.95%, F1=52.43%

See the [tool documentation](README_TOOL.md) for complete details.