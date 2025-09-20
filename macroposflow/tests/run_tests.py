"""
Comprehensive test runner for MacroPosFlow Phase 1.

This script runs all tests for the Phase 1 implementation and provides
a detailed report of the results.
"""

import sys
import os
import time
import traceback
from typing import List, Dict, Any

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test_module(module_name: str) -> Dict[str, Any]:
    """
    Run tests for a specific module.
    
    Args:
        module_name: Name of the test module to run
        
    Returns:
        Dictionary containing test results
    """
    try:
        # Import the test module
        module = __import__(module_name, fromlist=[''])
        
        # Get all test classes
        test_classes = []
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                attr_name.startswith('Test') and 
                hasattr(attr, 'setUp')):
                test_classes.append(attr)
        
        results = {
            'module': module_name,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': [],
            'test_classes': []
        }
        
        # Run each test class
        for test_class in test_classes:
            class_results = run_test_class(test_class)
            results['total_tests'] += class_results['total_tests']
            results['passed_tests'] += class_results['passed_tests']
            results['failed_tests'] += class_results['failed_tests']
            results['errors'].extend(class_results['errors'])
            results['test_classes'].append(class_results)
        
        return results
        
    except Exception as e:
        return {
            'module': module_name,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': [f"Failed to import module {module_name}: {str(e)}"],
            'test_classes': []
        }

def run_test_class(test_class) -> Dict[str, Any]:
    """
    Run tests for a specific test class.
    
    Args:
        test_class: Test class to run
        
    Returns:
        Dictionary containing test results
    """
    results = {
        'class_name': test_class.__name__,
        'total_tests': 0,
        'passed_tests': 0,
        'failed_tests': 0,
        'errors': [],
        'test_methods': []
    }
    
    try:
        # Get all test methods
        test_methods = []
        for method_name in dir(test_class):
            if method_name.startswith('test_'):
                test_methods.append(method_name)
        
        # Run each test method
        for method_name in test_methods:
            method_results = run_test_method(test_class, method_name)
            results['total_tests'] += 1
            if method_results['passed']:
                results['passed_tests'] += 1
            else:
                results['failed_tests'] += 1
                results['errors'].append(method_results['error'])
            results['test_methods'].append(method_results)
    
    except Exception as e:
        results['errors'].append(f"Failed to run test class {test_class.__name__}: {str(e)}")
    
    return results

def run_test_method(test_class, method_name: str) -> Dict[str, Any]:
    """
    Run a specific test method.
    
    Args:
        test_class: Test class containing the method
        method_name: Name of the test method to run
        
    Returns:
        Dictionary containing test results
    """
    result = {
        'method_name': method_name,
        'passed': False,
        'error': None,
        'execution_time': 0.0
    }
    
    try:
        # Create test instance
        instance = test_class()
        
        # Set up
        if hasattr(instance, 'setUp'):
            instance.setUp()
        
        # Run test
        start_time = time.time()
        method = getattr(instance, method_name)
        method()
        end_time = time.time()
        
        result['passed'] = True
        result['execution_time'] = end_time - start_time
        
        # Tear down
        if hasattr(instance, 'tearDown'):
            instance.tearDown()
            
    except Exception as e:
        result['error'] = f"{method_name}: {str(e)}\n{traceback.format_exc()}"
        result['execution_time'] = time.time() - start_time
        
        # Try to tear down even if test failed
        try:
            if hasattr(instance, 'tearDown'):
                instance.tearDown()
        except:
            pass
    
    return result

def print_results(results: List[Dict[str, Any]]) -> None:
    """
    Print test results in a readable format.
    
    Args:
        results: List of test results
    """
    total_tests = sum(r['total_tests'] for r in results)
    passed_tests = sum(r['passed_tests'] for r in results)
    failed_tests = sum(r['failed_tests'] for r in results)
    
    print("\n" + "=" * 80)
    print("MACROPOSFLOW PHASE 1 TEST RESULTS")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
    print("=" * 80)
    
    # Print module results
    for module_result in results:
        print(f"\nModule: {module_result['module']}")
        print("-" * 40)
        print(f"Tests: {module_result['passed_tests']}/{module_result['total_tests']} passed")
        
        # Print class results
        for class_result in module_result['test_classes']:
            print(f"  Class: {class_result['class_name']}")
            print(f"  Tests: {class_result['passed_tests']}/{class_result['total_tests']} passed")
            
            # Print failed test details
            if class_result['failed_tests'] > 0:
                print("  Failed Tests:")
                for method_result in class_result['test_methods']:
                    if not method_result['passed']:
                        print(f"    - {method_result['method_name']}: {method_result['error'].split(':')[0]}")
    
    # Print errors if any
    all_errors = []
    for module_result in results:
        all_errors.extend(module_result['errors'])
    
    if all_errors:
        print("\n" + "=" * 80)
        print("DETAILED ERROR REPORT")
        print("=" * 80)
        for i, error in enumerate(all_errors, 1):
            print(f"\nError {i}:")
            print(error)
    
    print("\n" + "=" * 80)

def main():
    """Main test runner function."""
    print("🧪 Running MacroPosFlow Phase 1 Tests")
    print("This may take a few moments...\n")
    
    # Test modules to run
    test_modules = [
        'test_basic',
        'test_recorder',
        'test_executor',
        'test_config'
    ]
    
    # Run all tests
    start_time = time.time()
    all_results = []
    
    for module_name in test_modules:
        print(f"Running {module_name}...")
        result = run_test_module(f"macroposflow.tests.{module_name}")
        all_results.append(result)
    
    end_time = time.time()
    
    # Print results
    print_results(all_results)
    
    # Print summary
    total_tests = sum(r['total_tests'] for r in all_results)
    passed_tests = sum(r['passed_tests'] for r in all_results)
    failed_tests = sum(r['failed_tests'] for r in all_results)
    execution_time = end_time - start_time
    
    print(f"\nTest Execution Time: {execution_time:.2f} seconds")
    
    if failed_tests == 0:
        print("🎉 All tests passed! Phase 1 implementation is working correctly.")
        return 0
    else:
        print(f"❌ {failed_tests} test(s) failed. Please review the error report above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)