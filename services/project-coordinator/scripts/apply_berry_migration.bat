@echo off
REM Script to apply the Berry agent configuration migration on Windows

echo Applying Berry agent configuration migration...
python "%~dp0apply_berry_migration.py" %*

if %ERRORLEVEL% EQU 0 (
    echo Migration completed successfully.
) else (
    echo Migration failed with error code %ERRORLEVEL%.
)

pause
