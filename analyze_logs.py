#!/usr/bin/env python3
import argparse
import json
import re
from collections import defaultdict
from datetime import datetime

LEVELS = {
    'ERROR': 'errors',
    'WARN': 'warnings',
    'WARNING': 'warnings',
}

# Precompile regex patterns for performance
PATTERNS = [
    # ISO-like: 2025-09-08 12:34:56,789 ERROR Message
    re.compile(r'^(?P<date>\d{4}-\d{2}-\d{2})[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?\s+(?P<level>ERROR|WARN|WARNING)\s+(?P<message>.*)$', re.IGNORECASE),
    # Bracketed: [2025-09-08 12:34:56] [ERROR] Message
    re.compile(r'^\[(?P<date>\d{4}-\d{2}-\d{2})[ T]\d{2}:\d{2}:\d{2}[^\]]*\]\s*\[(?P<level>ERROR|WARN|WARNING)\]\s*(?P<message>.*)$', re.IGNORECASE),
]

DATE_EXTRACTOR = re.compile(r'(\d{4}-\d{2}-\d{2})')
LEVEL_FINDER = re.compile(r'\b(ERROR|WARN|WARNING)\b', re.IGNORECASE)

CAUSE_PATTERNS = [
    (re.compile(r'timeout|timed out', re.IGNORECASE), 'The operation timed out, possibly due to network latency or an unresponsive service.'),
    (re.compile(r'connection refused', re.IGNORECASE), 'The target service refused the connection; it may be down, unreachable, or blocked by a firewall.'),
    (re.compile(r'not found|\b404\b|file not found', re.IGNORECASE), 'The requested resource or file could not be found.'),
    (re.compile(r'permission denied|\b403\b', re.IGNORECASE), 'Operation failed due to insufficient permissions or access rights.'),
    (re.compile(r'out of memory', re.IGNORECASE), 'The process ran out of memory resources.'),
    (re.compile(r'disk full|no space left', re.IGNORECASE), 'The storage device is full; no space left on device.'),
    (re.compile(r'invalid (argument|format|input|configuration|config)', re.IGNORECASE), 'An invalid input or configuration was provided.'),
    (re.compile(r'authentication failed|invalid credentials|unauthorized|\b401\b', re.IGNORECASE), 'Authentication failed due to invalid or missing credentials.'),
    (re.compile(r'rate limit|too many requests|\b429\b', re.IGNORECASE), 'The service rate limit was exceeded due to too many requests in a short period.'),
    (re.compile(r'(database|sql).*(error|exception)|deadlock|constraint violation', re.IGNORECASE), 'A database-related error occurred; check connectivity, queries, and constraints.'),
    (re.compile(r'null pointer|NoneType|attributeerror|typeerror|valueerror|exception', re.IGNORECASE), 'An application exception occurred; check stack trace and input values.'),
]

def explain_cause(message: str) -> str:
    for pattern, explanation in CAUSE_PATTERNS:
        if pattern.search(message):
            return explanation
    return 'An error or warning was logged. Investigate the message and context for root cause.'


def parse_line(line: str):
    for pat in PATTERNS:
        m = pat.match(line)
        if m:
            date = m.group('date')
            level = m.group('level').upper()
            message = m.group('message').strip()
            return date, level, message
    # Fallback: find any ERROR/WARN and attempt to extract date anywhere
    if LEVEL_FINDER.search(line):
        level_match = LEVEL_FINDER.search(line)
        level = level_match.group(1).upper()
        date_match = DATE_EXTRACTOR.search(line)
        date = date_match.group(1) if date_match else 'unknown_date'
        # Message as the remainder after the level word if possible
        idx = level_match.end()
        message = line[idx:].strip() or line.strip()
        return date, level, message
    return None


def analyze_log(file_path: str):
    summary = {
        'total_errors': 0,
        'total_warnings': 0,
        'dates': defaultdict(lambda: {
            'errors': {'total': 0, 'messages': defaultdict(int)},
            'warnings': {'total': 0, 'messages': defaultdict(int)},
        })
    }

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parsed = parse_line(line)
            if not parsed:
                continue
            date, level, message = parsed
            bucket = LEVELS.get(level, None)
            if not bucket:
                continue
            if bucket == 'errors':
                summary['total_errors'] += 1
            else:
                summary['total_warnings'] += 1
            day_data = summary['dates'][date][bucket]
            day_data['total'] += 1
            day_data['messages'][message] += 1

    # Convert defaultdicts to plain dicts and attach explanations
    dates_out = {}
    for date, data in summary['dates'].items():
        date_entry = {}
        for bucket in ['errors', 'warnings']:
            messages_dict = data[bucket]['messages']
            messages_list = []
            for msg, count in sorted(messages_dict.items(), key=lambda x: (-x[1], x[0])):
                messages_list.append({
                    'message': msg,
                    'count': count,
                    'explanation': explain_cause(msg)
                })
            date_entry[bucket] = {
                'total': data[bucket]['total'],
                'messages': messages_list
            }
        dates_out[date] = date_entry

    summary['dates'] = dates_out
    return summary


def main():
    parser = argparse.ArgumentParser(description='Analyze log files, extract errors/warnings, group by date, and output JSON summary with explanations.')
    parser.add_argument('logfile', help='Path to the log file to analyze')
    parser.add_argument('-o', '--output', help='Path to write JSON summary (defaults to stdout)')
    args = parser.parse_args()

    result = analyze_log(args.logfile)
    output = json.dumps(result, indent=2)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as out:
            out.write(output)
    else:
        print(output)


if __name__ == '__main__':
    main()
