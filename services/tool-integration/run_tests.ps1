# PowerShell script to run tests for the Tool Integration service
# Usage: .\run_tests.ps1 [options]
# Options:
#   -v, --verbose     Enable verbose output
#   -c, --coverage    Run tests with coverage
#   -r, --report      Generate test reports
#   -p, --performance Run performance tests
#   -a, --all         Run all tests (including slow tests)
#   -h, --help        Show help message

param (
    [switch]$v = $false,
    [switch]$verbose = $false,
    [switch]$c = $false,
    [switch]$coverage = $false,
    [switch]$r = $false,
    [switch]$report = $false,
    [switch]$p = $false,
    [switch]$performance = $false,
    [switch]$a = $false,
    [switch]$all = $false,
    [switch]$h = $false,
    [switch]$help = $false
)

# Set working directory to the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Show help message
if ($h -or $help) {
    Write-Host "Usage: .\run_tests.ps1 [options]"
    Write-Host "Options:"
    Write-Host "  -v, --verbose     Enable verbose output"
    Write-Host "  -c, --coverage    Run tests with coverage"
    Write-Host "  -r, --report      Generate test reports"
    Write-Host "  -p, --performance Run performance tests"
    Write-Host "  -a, --all         Run all tests (including slow tests)"
    Write-Host "  -h, --help        Show help message"
    exit 0
}

# Combine short and long options
$verboseEnabled = $v -or $verbose
$coverageEnabled = $c -or $coverage
$reportEnabled = $r -or $report
$performanceEnabled = $p -or $performance
$allEnabled = $a -or $all

# Build command
$command = "python -m pytest"

# Add options
if ($verboseEnabled) {
    $command += " -v"
}

if ($coverageEnabled) {
    $command += " --cov=src --cov-report=term --cov-report=html:reports/coverage"
}

if ($reportEnabled) {
    $command += " --html=reports/pytest/report.html --self-contained-html"
}

if ($performanceEnabled) {
    $command += " -m performance"
} elseif (-not $allEnabled) {
    $command += " -m 'not slow'"
}

# Add test directory
$command += " tests/"

# Create reports directory if it doesn't exist
if ($coverageEnabled -or $reportEnabled) {
    if (-not (Test-Path "reports")) {
        New-Item -ItemType Directory -Path "reports" | Out-Null
    }
    if ($coverageEnabled -and -not (Test-Path "reports/coverage")) {
        New-Item -ItemType Directory -Path "reports/coverage" | Out-Null
    }
    if ($reportEnabled -and -not (Test-Path "reports/pytest")) {
        New-Item -ItemType Directory -Path "reports/pytest" | Out-Null
    }
}

# Display command
Write-Host "Running tests with command: $command"

# Run command
Invoke-Expression $command

# Display coverage report location if coverage is enabled
if ($coverageEnabled) {
    Write-Host "Coverage report generated at: $scriptDir\reports\coverage\index.html"
}

# Display test report location if report is enabled
if ($reportEnabled) {
    Write-Host "Test report generated at: $scriptDir\reports\pytest\report.html"
}
