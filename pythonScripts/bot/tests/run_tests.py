#!/usr/bin/env python3
"""
Test runner for the TagPro bot.
Run this script to execute all tests.
"""

import sys
import os
import subprocess

# Add the parent directory to the path so we can import bot modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_test(test_file):
    """Run a specific test file."""
    print(f"Running {test_file}...")
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            print(f"✓ {test_file} passed")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"✗ {test_file} failed")
            if result.stderr:
                print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"✗ Error running {test_file}: {e}")
        return False


def main():
    """Run all tests."""
    print("Running TagPro Bot Tests...")
    print("=" * 40)
    
    # Get all test files
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_files = [f for f in os.listdir(test_dir) if f.endswith('.py') and f != 'run_tests.py']
    
    if not test_files:
        print("No test files found!")
        return
    
    # Run each test
    passed = 0
    total = len(test_files)
    
    for test_file in test_files:
        if run_test(test_file):
            passed += 1
        print()
    
    # Summary
    print("=" * 40)
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("All tests passed! 🎉")
        return 0
    else:
        print("Some tests failed! 😞")
        return 1


if __name__ == '__main__':
    sys.exit(main())
