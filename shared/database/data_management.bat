@echo off
REM Data management script for multi-environment PostgreSQL databases (Windows version)
REM This script provides functions for cloning data and resetting test database

setlocal enabledelayedexpansion

REM Database connection parameters
set DB_HOST=%DB_HOST%
if "%DB_HOST%"=="" set DB_HOST=localhost
set DB_PORT=%DB_PORT%
if "%DB_PORT%"=="" set DB_PORT=5432
set DB_USER=%DB_USER%
if "%DB_USER%"=="" set DB_USER=postgres
set DB_PASSWORD=%DB_PASSWORD%
if "%DB_PASSWORD%"=="" set DB_PASSWORD=postgres
set PROD_DB=%PROD_DB%
if "%PROD_DB%"=="" set PROD_DB=mas_framework_prod
set DEV_DB=%DEV_DB%
if "%DEV_DB%"=="" set DEV_DB=mas_framework_dev
set TEST_DB=%TEST_DB%
if "%TEST_DB%"=="" set TEST_DB=mas_framework_test

REM Check for PostgreSQL tools
where pg_dump >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo PostgreSQL tools not found in PATH. Please ensure PostgreSQL is installed and in your PATH.
    exit /b 1
)

REM Function to clone data from prod to dev
:clone_prod_to_dev
    echo Starting data clone from %PROD_DB% to %DEV_DB%...
    
    REM Get list of tables
    set "TABLES="
    for /f "tokens=*" %%a in ('psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %PROD_DB% -t -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'schema_version' AND tablename != 'test_data_tracking';"') do (
        set "TABLE=%%a"
        set "TABLE=!TABLE: =!"
        if not "!TABLE!"=="" (
            echo Copying data for table: !TABLE!
            
            REM Clear table in dev
            psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DEV_DB% -c "TRUNCATE TABLE !TABLE! CASCADE;"
            
            REM Copy data from prod to dev
            pg_dump -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %PROD_DB% --table=!TABLE! --data-only | psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DEV_DB%
        )
    )
    
    echo Data clone completed successfully.
    exit /b 0

REM Function to reset test database
:reset_test_db
    echo Resetting test database %TEST_DB%...
    
    REM Get list of tables
    for /f "tokens=*" %%a in ('psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %TEST_DB% -t -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'schema_version' AND tablename != 'test_data_tracking';"') do (
        set "TABLE=%%a"
        set "TABLE=!TABLE: =!"
        if not "!TABLE!"=="" (
            echo Resetting data for table: !TABLE!
            
            REM Get list of preserved record IDs
            set "PRESERVED_IDS="
            for /f "tokens=*" %%b in ('psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %TEST_DB% -t -c "SELECT record_id FROM test_data_tracking WHERE table_name = '!TABLE!' AND preserve_in_reset = true;"') do (
                set "ID=%%b"
                set "ID=!ID: =!"
                if not "!ID!"=="" (
                    if "!PRESERVED_IDS!"=="" (
                        set "PRESERVED_IDS=!ID!"
                    ) else (
                        set "PRESERVED_IDS=!PRESERVED_IDS!,!ID!"
                    )
                )
            )
            
            if "!PRESERVED_IDS!"=="" (
                REM No preserved records, truncate the table
                psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %TEST_DB% -c "TRUNCATE TABLE !TABLE! CASCADE;"
            ) else (
                REM Delete all records except preserved ones
                psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %TEST_DB% -c "DELETE FROM !TABLE! WHERE id NOT IN (!PRESERVED_IDS!);"
            )
        )
    )
    
    REM Insert default data
    psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %TEST_DB% -c "INSERT INTO users (username, email, password_hash, is_admin) VALUES ('test_admin', 'test_admin@example.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', TRUE) ON CONFLICT (username) DO NOTHING;"
    
    echo Test database reset completed successfully.
    exit /b 0

REM Function to mark test data for preservation
:mark_test_data
    set TABLE=%~1
    set RECORD_ID=%~2
    set PRESERVE=%~3
    
    if "%PRESERVE%"=="true" (
        set PRESERVE_VAL=true
    ) else (
        set PRESERVE_VAL=false
    )
    
    psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %TEST_DB% -c "SELECT mark_test_data_preserve('%TABLE%', '%RECORD_ID%', %PRESERVE_VAL%);"
    
    echo Marked record %RECORD_ID% in table %TABLE% with preserve=%PRESERVE_VAL%
    exit /b 0

REM Main execution based on command line arguments
if "%~1"=="" (
    echo Usage: %0 [clone^|reset^|mark] [args...]
    echo   clone - Clone data from prod to dev
    echo   reset - Reset test database
    echo   mark table_name record_id [true^|false] - Mark test data for preservation
    exit /b 1
)

set COMMAND=%~1

if "%COMMAND%"=="clone" (
    call :clone_prod_to_dev
) else if "%COMMAND%"=="reset" (
    call :reset_test_db
) else if "%COMMAND%"=="mark" (
    if "%~2"=="" (
        echo Usage: %0 mark table_name record_id [true^|false]
        exit /b 1
    )
    if "%~3"=="" (
        echo Usage: %0 mark table_name record_id [true^|false]
        exit /b 1
    )
    set TABLE=%~2
    set RECORD_ID=%~3
    set PRESERVE=%~4
    if "%PRESERVE%"=="" set PRESERVE=true
    call :mark_test_data %TABLE% %RECORD_ID% %PRESERVE%
) else (
    echo Unknown command: %COMMAND%
    echo Usage: %0 [clone^|reset^|mark] [args...]
    exit /b 1
)

exit /b 0
