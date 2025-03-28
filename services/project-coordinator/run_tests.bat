@echo off
REM Run tests for the Project Coordinator service
REM This script runs the tests for the Project Coordinator service

REM Set up environment variables
for %%i in ("%CD%\..\..\") do set PROJECT_ROOT=%%~fi
set PYTHONPATH=%PYTHONPATH%;%CD%;%PROJECT_ROOT%
set ENVIRONMENT=test

REM Run the tests
pytest tests/ -v
