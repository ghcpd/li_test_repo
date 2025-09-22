#!/usr/bin/env python3
"""
Simple test script for the log analyzer.
This verifies basic functionality of the log analysis script.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def create_test_log():
    """Create a small test log file for validation."""
    test_content = """2023-12-25 10:00:00 INFO Application started
2023-12-25 10:00:01 ERROR Connection refused to database
2023-12-25 10:00:02 WARNING Authentication failed for user test
2023-12-25 10:00:03 ERROR Out of memory exception
2023-12-26 10:00:00 INFO Processing completed
2023-12-26 10:00:01 WARNING File not found: test.txt
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(test_content)
        return f.name


def test_log_analyzer():
    """Test the log analyzer script."""
    print("Running log analyzer tests...")
    
    # Create test log file
    test_log_path = create_test_log()
    test_output_path = tempfile.mktemp(suffix='.json')
    
    try:
        # Run the log analyzer
        result = subprocess.run([
            sys.executable, 'log_analyzer.py', 
            test_log_path, '-o', test_output_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Test failed: {result.stderr}")
            return False
        
        # Check if output file was created
        if not os.path.exists(test_output_path):
            print("❌ Test failed: Output file not created")
            return False
        
        # Load and validate JSON output
        with open(test_output_path, 'r') as f:
            report = json.load(f)
        
        # Basic validation checks
        required_keys = ['metadata', 'summary', 'errors_by_date', 'warnings_by_date']
        for key in required_keys:
            if key not in report:
                print(f"❌ Test failed: Missing key '{key}' in report")
                return False
        
        # Check summary data
        summary = report['summary']
        if summary['total_errors'] != 2:
            print(f"❌ Test failed: Expected 2 errors, got {summary['total_errors']}")
            return False
        
        if summary['total_warnings'] != 2:
            print(f"❌ Test failed: Expected 2 warnings, got {summary['total_warnings']}")
            return False
        
        if summary['unique_dates'] != 2:
            print(f"❌ Test failed: Expected 2 unique dates, got {summary['unique_dates']}")
            return False
        
        print("✅ All tests passed!")
        print(f"  - Found {summary['total_errors']} errors and {summary['total_warnings']} warnings")
        print(f"  - Processed {summary['unique_dates']} unique dates")
        print(f"  - Error categories: {list(summary['error_categories'].keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
        
    finally:
        # Cleanup
        if os.path.exists(test_log_path):
            os.unlink(test_log_path)
        if os.path.exists(test_output_path):
            os.unlink(test_output_path)


if __name__ == '__main__':
    success = test_log_analyzer()
    sys.exit(0 if success else 1)