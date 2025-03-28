#!/bin/bash
# Bash script to run tests for the Tool Integration service
# Usage: ./run_tests.sh [options]
# Options:
#   -v, --verbose     Enable verbose output
#   -c, --coverage    Run tests with coverage
#   -r, --report      Generate test reports
#   -p, --performance Run performance tests
#   -a, --all         Run all tests (including slow tests)
#   -h, --help        Show help message

# Set default values
VERBOSE=false
COVERAGE=false
REPORT=false
PERFORMANCE=false
ALL=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -r|--report)
            REPORT=true
            shift
            ;;
        -p|--performance)
            PERFORMANCE=true
            shift
            ;;
        -a|--all)
            ALL=true
            shift
            ;;
        -h|--help)
            echo "Usage: ./run_tests.sh [options]"
            echo "Options:"
            echo "  -v, --verbose     Enable verbose output"
            echo "  -c, --coverage    Run tests with coverage"
            echo "  -r, --report      Generate test reports"
            echo "  -p, --performance Run performance tests"
            echo "  -a, --all         Run all tests (including slow tests)"
            echo "  -h, --help        Show help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Set working directory to the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Build command
COMMAND="python -m pytest"

# Add options
if [ "$VERBOSE" = true ]; then
    COMMAND="$COMMAND -v"
fi

if [ "$COVERAGE" = true ]; then
    COMMAND="$COMMAND --cov=src --cov-report=term --cov-report=html:reports/coverage"
fi

if [ "$REPORT" = true ]; then
    COMMAND="$COMMAND --html=reports/pytest/report.html --self-contained-html"
fi

if [ "$PERFORMANCE" = true ]; then
    COMMAND="$COMMAND -m performance"
elif [ "$ALL" = false ]; then
    COMMAND="$COMMAND -m 'not slow'"
fi

# Add test directory
COMMAND="$COMMAND tests/"

# Create reports directory if it doesn't exist
if [ "$COVERAGE" = true ] || [ "$REPORT" = true ]; then
    mkdir -p reports
    if [ "$COVERAGE" = true ]; then
        mkdir -p reports/coverage
    fi
    if [ "$REPORT" = true ]; then
        mkdir -p reports/pytest
    fi
fi

# Display command
echo "Running tests with command: $COMMAND"

# Run command
eval "$COMMAND"

# Display coverage report location if coverage is enabled
if [ "$COVERAGE" = true ]; then
    echo "Coverage report generated at: $SCRIPT_DIR/reports/coverage/index.html"
fi

# Display test report location if report is enabled
if [ "$REPORT" = true ]; then
    echo "Test report generated at: $SCRIPT_DIR/reports/pytest/report.html"
fi
