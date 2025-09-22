#!/usr/bin/env python3
"""
Log Analyzer Script

This script analyzes large log files to extract error and warning messages,
groups them by date, and generates a comprehensive JSON summary report.
"""

import re
import json
import argparse
import sys
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional


class LogAnalyzer:
    """Main class for analyzing log files and generating reports."""
    
    # Common log level patterns
    LOG_PATTERNS = {
        'error': re.compile(r'\b(ERROR|error|Error|FATAL|fatal|Fatal|CRITICAL|critical|Critical)\b'),
        'warning': re.compile(r'\b(WARNING|warning|Warning|WARN|warn|Warn)\b')
    }
    
    # Common date patterns for different log formats
    DATE_PATTERNS = [
        # ISO format: 2023-12-25 14:30:45
        re.compile(r'(\d{4}-\d{2}-\d{2})\s+\d{2}:\d{2}:\d{2}'),
        # Apache format: 25/Dec/2023:14:30:45
        re.compile(r'(\d{2}/\w{3}/\d{4}):\d{2}:\d{2}:\d{2}'),
        # Syslog format: Dec 25 14:30:45
        re.compile(r'(\w{3}\s+\d{1,2})\s+\d{2}:\d{2}:\d{2}'),
        # Simple date: 2023-12-25
        re.compile(r'(\d{4}-\d{2}-\d{2})'),
        # US format: 12/25/2023
        re.compile(r'(\d{1,2}/\d{1,2}/\d{4})'),
    ]
    
    # Common error patterns and their explanations
    ERROR_EXPLANATIONS = {
        'connection': {
            'patterns': [
                re.compile(r'\b(connection.*(?:refused|timeout|reset|failed|lost))', re.IGNORECASE),
                re.compile(r'\b(socket.*(?:timeout|error|closed))', re.IGNORECASE),
                re.compile(r'\b(network.*(?:unreachable|error))', re.IGNORECASE),
            ],
            'explanation': 'Network connectivity issues, possibly due to service unavailability, network configuration problems, or firewall blocking'
        },
        'authentication': {
            'patterns': [
                re.compile(r'\b(auth.*(?:failed|error|denied))', re.IGNORECASE),
                re.compile(r'\b(login.*(?:failed|invalid))', re.IGNORECASE),
                re.compile(r'\b(permission.*denied)', re.IGNORECASE),
                re.compile(r'\b(access.*denied)', re.IGNORECASE),
            ],
            'explanation': 'Authentication or authorization failures, typically due to incorrect credentials, expired tokens, or insufficient permissions'
        },
        'database': {
            'patterns': [
                re.compile(r'\b(database.*(?:error|connection|timeout))', re.IGNORECASE),
                re.compile(r'\b(sql.*(?:error|exception))', re.IGNORECASE),
                re.compile(r'\b(query.*(?:failed|timeout))', re.IGNORECASE),
                re.compile(r'\b(deadlock|lock.*timeout)', re.IGNORECASE),
            ],
            'explanation': 'Database-related issues including connection problems, query errors, deadlocks, or performance issues'
        },
        'file_system': {
            'patterns': [
                re.compile(r'\b(file.*(?:not found|permission|access))', re.IGNORECASE),
                re.compile(r'\b(disk.*(?:full|space|error))', re.IGNORECASE),
                re.compile(r'\b(io.*error)', re.IGNORECASE),
                re.compile(r'\b(no space left)', re.IGNORECASE),
            ],
            'explanation': 'File system issues such as missing files, permission problems, disk space shortage, or I/O errors'
        },
        'memory': {
            'patterns': [
                re.compile(r'\b(out of memory|oom|memory.*error)', re.IGNORECASE),
                re.compile(r'\b(heap.*(?:space|overflow))', re.IGNORECASE),
                re.compile(r'\b(stack.*overflow)', re.IGNORECASE),
            ],
            'explanation': 'Memory-related issues including out-of-memory conditions, heap space exhaustion, or stack overflow'
        },
        'timeout': {
            'patterns': [
                re.compile(r'\b(timeout|timed out)', re.IGNORECASE),
                re.compile(r'\b(request.*timeout)', re.IGNORECASE),
                re.compile(r'\b(operation.*timeout)', re.IGNORECASE),
            ],
            'explanation': 'Timeout issues indicating operations taking longer than expected, possibly due to performance problems or resource constraints'
        },
        'configuration': {
            'patterns': [
                re.compile(r'\b(config.*(?:error|missing|invalid))', re.IGNORECASE),
                re.compile(r'\b(property.*(?:not found|invalid))', re.IGNORECASE),
                re.compile(r'\b(setting.*(?:error|invalid))', re.IGNORECASE),
            ],
            'explanation': 'Configuration errors due to missing, invalid, or malformed configuration settings'
        }
    }
    
    def __init__(self):
        self.log_entries = []
        self.error_summary = defaultdict(list)
        self.warning_summary = defaultdict(list)
        self.date_stats = defaultdict(lambda: {'errors': 0, 'warnings': 0})
        
    def extract_date(self, line: str) -> Optional[str]:
        """Extract date from log line using various patterns."""
        current_year = datetime.now().year
        
        for pattern in self.DATE_PATTERNS:
            match = pattern.search(line)
            if match:
                date_str = match.group(1)
                
                # Normalize different date formats
                try:
                    if '/' in date_str and len(date_str.split('/')) == 3:
                        # Handle different slash formats
                        parts = date_str.split('/')
                        if len(parts[2]) == 4:  # Year is last (US format)
                            if len(parts[0]) <= 2:  # MM/DD/YYYY or M/D/YYYY
                                date_obj = datetime.strptime(date_str, '%m/%d/%Y' if len(parts[0]) == 2 else '%m/%d/%Y')
                            else:  # DD/MM/YYYY
                                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                        else:  # Year is first
                            date_obj = datetime.strptime(date_str, '%Y/%m/%d')
                        return date_obj.strftime('%Y-%m-%d')
                    elif '/' in date_str:  # Apache format: 25/Dec/2023
                        date_obj = datetime.strptime(date_str, '%d/%b/%Y')
                        return date_obj.strftime('%Y-%m-%d')
                    elif ' ' in date_str:  # Syslog format: Dec 25
                        date_str_with_year = f"{date_str} {current_year}"
                        date_obj = datetime.strptime(date_str_with_year, '%b %d %Y')
                        return date_obj.strftime('%Y-%m-%d')
                    else:  # ISO format: 2023-12-25
                        datetime.strptime(date_str, '%Y-%m-%d')  # Validate format
                        return date_str
                except ValueError:
                    continue
        
        return None
    
    def classify_error_cause(self, message: str) -> Tuple[str, str]:
        """Classify error message and provide explanation."""
        for category, error_info in self.ERROR_EXPLANATIONS.items():
            for pattern in error_info['patterns']:
                if pattern.search(message):
                    return category, error_info['explanation']
        
        return 'general', 'General error that does not match specific known patterns'
    
    def analyze_log_file(self, file_path: str) -> None:
        """Analyze the log file line by line for memory efficiency."""
        print(f"Analyzing log file: {file_path}")
        
        line_count = 0
        error_count = 0
        warning_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    line_count += 1
                    date = self.extract_date(line)
                    
                    # Check for errors
                    if self.LOG_PATTERNS['error'].search(line):
                        error_count += 1
                        category, explanation = self.classify_error_cause(line)
                        
                        entry = {
                            'line_number': line_num,
                            'message': line,
                            'category': category,
                            'explanation': explanation
                        }
                        
                        if date:
                            self.error_summary[date].append(entry)
                            self.date_stats[date]['errors'] += 1
                        else:
                            self.error_summary['unknown_date'].append(entry)
                            self.date_stats['unknown_date']['errors'] += 1
                    
                    # Check for warnings
                    elif self.LOG_PATTERNS['warning'].search(line):
                        warning_count += 1
                        category, explanation = self.classify_error_cause(line)
                        
                        entry = {
                            'line_number': line_num,
                            'message': line,
                            'category': category,
                            'explanation': explanation
                        }
                        
                        if date:
                            self.warning_summary[date].append(entry)
                            self.date_stats[date]['warnings'] += 1
                        else:
                            self.warning_summary['unknown_date'].append(entry)
                            self.date_stats['unknown_date']['warnings'] += 1
                    
                    # Progress indicator for large files
                    if line_count % 10000 == 0:
                        print(f"Processed {line_count} lines...")
        
        except FileNotFoundError:
            print(f"Error: Log file '{file_path}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading log file: {e}")
            sys.exit(1)
        
        print(f"Analysis complete: {line_count} lines processed")
        print(f"Found {error_count} errors and {warning_count} warnings")
    
    def generate_summary_statistics(self) -> Dict:
        """Generate summary statistics for the report."""
        total_errors = sum(len(entries) for entries in self.error_summary.values())
        total_warnings = sum(len(entries) for entries in self.warning_summary.values())
        
        # Error categories count
        error_categories = Counter()
        warning_categories = Counter()
        
        for entries in self.error_summary.values():
            for entry in entries:
                error_categories[entry['category']] += 1
        
        for entries in self.warning_summary.values():
            for entry in entries:
                warning_categories[entry['category']] += 1
        
        # Date range
        all_dates = list(self.date_stats.keys())
        valid_dates = [d for d in all_dates if d != 'unknown_date']
        
        date_range = None
        if valid_dates:
            valid_dates.sort()
            date_range = {
                'start': valid_dates[0],
                'end': valid_dates[-1]
            }
        
        return {
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'unique_dates': len(valid_dates),
            'date_range': date_range,
            'error_categories': dict(error_categories.most_common()),
            'warning_categories': dict(warning_categories.most_common()),
            'daily_stats': dict(self.date_stats)
        }
    
    def generate_report(self, output_file: str) -> None:
        """Generate comprehensive JSON report."""
        print(f"Generating report: {output_file}")
        
        # Prepare report data
        report_data = {
            'metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'analyzer_version': '1.0.0'
            },
            'summary': self.generate_summary_statistics(),
            'errors_by_date': dict(self.error_summary),
            'warnings_by_date': dict(self.warning_summary),
            'error_explanations': {
                category: info['explanation'] 
                for category, info in self.ERROR_EXPLANATIONS.items()
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(report_data, file, indent=2, ensure_ascii=False)
            
            print(f"Report successfully generated: {output_file}")
            
            # Print summary to console
            summary = report_data['summary']
            print("\n=== ANALYSIS SUMMARY ===")
            print(f"Total Errors: {summary['total_errors']}")
            print(f"Total Warnings: {summary['total_warnings']}")
            print(f"Date Range: {summary['date_range']}")
            print(f"Top Error Categories: {list(summary['error_categories'].keys())[:3]}")
            
        except Exception as e:
            print(f"Error writing report file: {e}")
            sys.exit(1)


def main():
    """Main function to handle command line arguments and run analysis."""
    parser = argparse.ArgumentParser(
        description='Analyze log files and generate JSON summary reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s /var/log/application.log
  %(prog)s /var/log/system.log -o report.json
  %(prog)s large_log_file.log -o detailed_report.json
        '''
    )
    
    parser.add_argument(
        'log_file',
        help='Path to the log file to analyze'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='log_analysis_report.json',
        help='Output JSON report file (default: log_analysis_report.json)'
    )
    
    args = parser.parse_args()
    
    # Create analyzer and run analysis
    analyzer = LogAnalyzer()
    analyzer.analyze_log_file(args.log_file)
    analyzer.generate_report(args.output)


if __name__ == '__main__':
    main()