#!/usr/bin/env python3
"""
Comprehensive test runner for PDF service
Runs all test suites: unit, integration, and performance tests
Requirements: 1.3, 1.4, 6.1, 6.2
"""

import sys
import subprocess
import os


def run_command(cmd, description):
    """Run a command and report results"""
    print("\n" + "=" * 70)
    print(f"Running: {description}")
    print("=" * 70)
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
        return True
    else:
        print(f"❌ {description} - FAILED")
        return False


def main():
    """Run all test suites"""
    print("\n" + "=" * 70)
    print("PDF Service Comprehensive Test Suite")
    print("Task 8: Write comprehensive tests for PDF service")
    print("=" * 70)
    
    # Change to pdf directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    results = []
    
    # 1. Run unit tests
    results.append(run_command(
        "pytest test_unit.py -v --tb=short",
        "Unit Tests (Health Check, Validation, Error Handling)"
    ))
    
    # 2. Run integration tests
    results.append(run_command(
        "pytest test_integration.py -v --tb=short",
        "Integration Tests (Invalid Input, Error Responses, CORS)"
    ))
    
    # 3. Run performance tests
    results.append(run_command(
        "pytest test_performance.py -v --tb=short",
        "Performance Tests (Conversion Times, Resource Usage)"
    ))
    
    # 4. Run all tests with coverage
    print("\n" + "=" * 70)
    print("Running: All Tests with Coverage Report")
    print("=" * 70)
    
    coverage_result = subprocess.run(
        "pytest test_unit.py test_integration.py test_performance.py -v --cov=app --cov-report=term-missing",
        shell=True
    )
    
    if coverage_result.returncode == 0:
        print("✅ Coverage Report Generated")
        results.append(True)
    else:
        print("⚠️  Coverage Report Failed (tests may have passed)")
        # Don't fail overall if just coverage reporting failed
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTest Suites: {passed}/{total} passed")
    
    if all(results):
        print("\n✅ All comprehensive tests PASSED!")
        print("\nTask 8 Requirements Verified:")
        print("  ✓ Unit tests for health check endpoint")
        print("  ✓ Unit tests for PDF conversion functionality")
        print("  ✓ Integration tests for invalid input handling")
        print("  ✓ Integration tests for error response validation")
        print("  ✓ Performance tests for conversion times (30s requirement)")
        print("  ✓ Performance tests for resource usage")
        return 0
    else:
        print("\n❌ Some tests FAILED")
        print("\nPlease review the test output above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
