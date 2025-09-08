# li_test_repo

This repo now includes a simple Python utility to analyze large log files.

Usage:
- Analyze and print to stdout: `python scripts/analyze_logs.py /path/to/your.log`
- Save report to a file: `python scripts/analyze_logs.py /path/to/your.log -o report.json`

The tool extracts ERROR and WARNING lines, groups results by date, and writes a JSON report that includes a short explanation for likely causes of each message.
