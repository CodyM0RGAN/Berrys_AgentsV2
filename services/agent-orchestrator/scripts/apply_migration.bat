@echo off
REM Script to apply the Agent Orchestrator service migrations

REM Change to the script directory
cd %~dp0

REM Run the migration script
python apply_migration.py %*

REM Check the exit code
if %ERRORLEVEL% neq 0 (
    echo Migration failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo Migration completed successfully
exit /b 0
