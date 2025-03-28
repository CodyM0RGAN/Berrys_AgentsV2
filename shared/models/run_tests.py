import unittest
import sys
import os

def run_tests():
    """Run the adapter tests and print the results."""
    print("Running adapter tests...")
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Open a file to write the test results
    with open('logs/test_results.txt', 'w') as f:
        f.write("Running adapter tests...\n")
        # Discover and run the tests
        loader = unittest.TestLoader()
        test_dir = os.path.abspath('shared/models/tests/adapters')
        tests = loader.discover(test_dir)
        
        # Run the tests with a text test runner
        runner = unittest.TextTestRunner(verbosity=2, stream=f)
        result = runner.run(tests)
        
        # Write the results
        f.write("\nTest Results:\n")
        f.write(f"Ran {result.testsRun} tests\n")
        f.write(f"Failures: {len(result.failures)}\n")
        f.write(f"Errors: {len(result.errors)}\n")
        
        # Write failures and errors
        if result.failures:
            f.write("\nFailures:\n")
            for i, (test, traceback) in enumerate(result.failures):
                f.write(f"\n{i+1}. {test}\n")
                f.write(traceback)
        
        if result.errors:
            f.write("\nErrors:\n")
            for i, (test, traceback) in enumerate(result.errors):
                f.write(f"\n{i+1}. {test}\n")
                f.write(traceback)
    
    # Print a message to the console
    print(f"Test results written to logs/test_results.txt")
    
    # Return the success status
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
