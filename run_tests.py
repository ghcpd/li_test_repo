#!/usr/bin/env python3
"""
Test runner for the nutrition system.
"""

import unittest
import sys
from pathlib import Path

# Add the nutrition_system to Python path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    # Discover and run tests
    loader = unittest.TestLoader()
    test_dir = Path(__file__).parent / "nutrition_system" / "tests"
    suite = loader.discover(str(test_dir), pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)