#!/usr/bin/env python3
"""Run all basic tests for ptracker."""

import sys
import subprocess


def run_test(test_file):
    """Run a single test file."""
    print(f"\n{'='*60}")
    print(f"Running: {test_file}")
    print('='*60)
    
    result = subprocess.run(
        [sys.executable, test_file],
        capture_output=False
    )
    
    return result.returncode == 0


def main():
    """Run all tests."""
    tests = [
        'tests/test_id_generator.py',
        'tests/test_models.py',
        'tests/test_config.py',
        'tests/test_repositories.py',
    ]
    
    print("🧪 Running ptracker basic tests...")
    
    passed = 0
    failed = 0
    
    for test in tests:
        if run_test(test):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed} passed, {failed} failed")
    print('='*60)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")


if __name__ == '__main__':
    main()
