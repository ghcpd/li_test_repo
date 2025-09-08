# li_test_repo

## Log Analysis Script

A minimal Python script `analyze_logs.py` is provided to analyze large log files, extract error and warning messages, group them by date, and generate a summary report in JSON format with brief explanations of likely causes.

Usage:

- Print JSON summary to stdout:

```
python3 analyze_logs.py path/to/your.log
```

- Write JSON summary to a file:

```
python3 analyze_logs.py path/to/your.log -o report.json
```

A sample log file `sample_log.txt` is included for quick testing:

```
python3 analyze_logs.py sample_log.txt
```
