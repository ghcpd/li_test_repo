# Log Analyzer Tool

A Python script to analyze large log files, extract error and warning messages, group them by date, and generate comprehensive summary reports in JSON format.

## Features

- **Efficient Processing**: Handles large log files by processing them line by line
- **Multiple Log Formats**: Supports various date formats (ISO, Apache, Syslog, US format)
- **Error Classification**: Automatically categorizes errors and provides explanations
- **Date Grouping**: Groups messages by date for temporal analysis
- **JSON Output**: Generates structured JSON reports with detailed statistics
- **Command Line Interface**: Easy-to-use CLI with helpful options

## Usage

### Basic Usage

```bash
python3 log_analyzer.py /path/to/your/logfile.log
```

### Specify Output File

```bash
python3 log_analyzer.py /path/to/your/logfile.log -o custom_report.json
```

### Help

```bash
python3 log_analyzer.py --help
```

## Supported Log Formats

The script can parse logs with various date formats:

- ISO format: `2023-12-25 14:30:45`
- Apache format: `25/Dec/2023:14:30:45`
- Syslog format: `Dec 25 14:30:45`
- Simple date: `2023-12-25`
- US format: `12/25/2023`

## Error Categories

The tool automatically categorizes errors into these types:

- **Connection**: Network connectivity issues
- **Authentication**: Login and permission failures
- **Database**: Database-related problems
- **File System**: File and disk space issues
- **Memory**: Memory-related errors
- **Timeout**: Operation timeout issues
- **Configuration**: Configuration errors
- **General**: Other uncategorized errors

## Output Format

The generated JSON report includes:

- **Metadata**: Analysis timestamp and version
- **Summary**: Overall statistics and top categories
- **Errors by Date**: Detailed error messages grouped by date
- **Warnings by Date**: Detailed warning messages grouped by date
- **Error Explanations**: Descriptions of each error category

## Example

```bash
# Analyze a sample log file
python3 log_analyzer.py sample_log.txt -o analysis_report.json

# The script will output:
# Analyzing log file: sample_log.txt
# Analysis complete: 53 lines processed
# Found 18 errors and 11 warnings
# Report successfully generated: analysis_report.json
```

## Testing

Run the included test script to verify functionality:

```bash
python3 test_log_analyzer.py
```

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only standard library)

## Files

- `log_analyzer.py`: Main log analysis script
- `test_log_analyzer.py`: Test script for verification
- `sample_log.txt`: Sample log file for testing
- `README.md`: This documentation