#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Test Runner
Run all tests
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_all_tests():
    """Run all tests"""
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    print("🧪 Running Blue Rose Bot Tests")
    print("==============================")
    
    exit_code = run_all_tests()
    sys.exit(exit_code)