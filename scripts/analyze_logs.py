#!/usr/bin/env python3
import argparse
import json
import re
from collections import defaultdict

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
LEVEL_RE = re.compile(r"\b(ERROR|WARNING)\b", re.IGNORECASE)

CAUSE_HINTS = [
    (re.compile(r"timeout", re.I), "Likely due to network latency, overloaded service, or slow dependency."),
    (re.compile(r"connection (refused|reset|aborted)", re.I), "Connection issues; the remote service may be down or blocking access."),
    (re.compile(r"not found|no such file|does not exist", re.I), "Missing file or resource path is incorrect."),
    (re.compile(r"permission denied|access denied", re.I), "Insufficient permissions for the file or operation."),
    (re.compile(r"out of memory|memory error", re.I), "Process ran out of memory; increase limits or optimize workload."),
    (re.compile(r"disk full|no space left", re.I), "Insufficient disk space on the host or container."),
    (re.compile(r"invalid (argument|input|format)", re.I), "Malformed input or unexpected format provided."),
]

def explain_cause(message: str) -> str:
    for pattern, hint in CAUSE_HINTS:
        if pattern.search(message):
            return hint
    return "General error or warning; check surrounding log context for details."


def parse_line(line: str):
    level_match = LEVEL_RE.search(line)
    if not level_match:
        return None
    level = level_match.group(1).upper()

    date_match = DATE_RE.search(line)
    date = date_match.group(1) if date_match else "unknown"

    # Extract message after the level token if possible
    idx = level_match.end()
    msg = line[idx:].strip(" -:|\t\n\r") or line.strip()
    return date, level, msg


def analyze(log_path: str):
    by_date = defaultdict(lambda: {"ERROR": defaultdict(int), "WARNING": defaultdict(int)})

    with open(log_path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            parsed = parse_line(line)
            if not parsed:
                continue
            date, level, msg = parsed
            by_date[date][level][msg] += 1

    summary = {}
    for date, levels in by_date.items():
        details = []
        err_total = 0
        warn_total = 0
        for lvl in ("ERROR", "WARNING"):
            for msg, count in levels[lvl].items():
                details.append({
                    "level": lvl,
                    "message": msg,
                    "count": count,
                    "explanation": explain_cause(msg),
                })
                if lvl == "ERROR":
                    err_total += count
                else:
                    warn_total += count
        summary[date] = {
            "errors": err_total,
            "warnings": warn_total,
            "details": sorted(details, key=lambda d: (-d["count"], d["level"], d["message"]))
        }
    return {"summary": summary}


def main():
    parser = argparse.ArgumentParser(description="Analyze a log file for errors and warnings.")
    parser.add_argument("logfile", help="Path to input log file")
    parser.add_argument("-o", "--output", help="Write JSON report to this file (defaults to stdout)")
    args = parser.parse_args()

    report = analyze(args.logfile)
    text = json.dumps(report, indent=2, sort_keys=True)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)


if __name__ == "__main__":
    main()
