@echo off
:: Batch script to run tests for the Tool Integration service
:: Usage: run_tests.bat [options]
:: Options:
::   /v, /verbose     Enable verbose output
::   /c, /coverage    Run tests with coverage
::   /r, /report      Generate test reports
::   /p, /performance Run performance tests
::   /a, /all         Run all tests (including slow tests)
::   /h, /help        Show help message

setlocal enabledelayedexpansion

:: Set default values
set VERBOSE=false
set COVERAGE=false
set REPORT=false
set PERFORMANCE=false
set ALL=false

:: Parse command line arguments
:parse_args
if "%~1"=="" goto :end_parse_args
if /i "%~1"=="/v" set VERBOSE=true
if /i "%~1"=="/verbose" set VERBOSE=true
if /i "%~1"=="/c" set COVERAGE=true
if /i "%~1"=="/coverage" set COVERAGE=true
if /i "%~1"=="/r" set REPORT=true
if /i "%~1"=="/report" set REPORT=true
if /i "%~1"=="/p" set PERFORMANCE=true
if /i "%~1"=="/performance" set PERFORMANCE=true
if /i "%~1"=="/a" set ALL=true
if /i "%~1"=="/all" set ALL=true
if /i "%~1"=="/h" goto :show_help
if /i "%~1"=="/help" goto :show_help
shift
goto :parse_args
:end_parse_args

:: Set working directory to the script directory
cd /d "%~dp0"

:: Build command
set COMMAND=python -m pytest

:: Add options
if "%VERBOSE%"=="true" (
    set COMMAND=!COMMAND! -v
)

if "%COVERAGE%"=="true" (
    set COMMAND=!COMMAND! --cov=src --cov-report=term --cov-report=html:reports/coverage
)

if "%REPORT%"=="true" (
    set COMMAND=!COMMAND! --html=reports/pytest/report.html --self-contained-html
)

if "%PERFORMANCE%"=="true" (
    set COMMAND=!COMMAND! -m performance
) else (
    if "%ALL%"=="false" (
        set COMMAND=!COMMAND! -m "not slow"
    )
)

:: Add test directory
set COMMAND=!COMMAND! tests/

:: Create reports directory if it doesn't exist
if "%COVERAGE%"=="true" (
    if not exist "reports" mkdir reports
    if not exist "reports\coverage" mkdir reports\coverage
)

if "%REPORT%"=="true" (
    if not exist "reports" mkdir reports
    if not exist "reports\pytest" mkdir reports\pytest
)

:: Display command
echo Running tests with command: !COMMAND!

:: Run command
!COMMAND!

:: Display coverage report location if coverage is enabled
if "%COVERAGE%"=="true" (
    echo Coverage report generated at: %~dp0reports\coverage\index.html
)

:: Display test report location if report is enabled
if "%REPORT%"=="true" (
    echo Test report generated at: %~dp0reports\pytest\report.html
)

goto :eof

:show_help
echo Usage: run_tests.bat [options]
echo Options:
echo   /v, /verbose     Enable verbose output
echo   /c, /coverage    Run tests with coverage
echo   /r, /report      Generate test reports
echo   /p, /performance Run performance tests
echo   /a, /all         Run all tests (including slow tests)
echo   /h, /help        Show help message
exit /b 0
