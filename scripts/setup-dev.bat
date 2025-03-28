@echo off
echo Setting up development environment...

:: Set up PYTHONPATH to include project root
call %~dp0\..\setup-env.bat

:: Create Python virtual environment if it doesn't exist
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install development dependencies
echo Installing development dependencies...
pip install -r requirements-dev.txt

echo Development setup completed successfully!
echo.
echo Note: This setup uses pg8000 (a pure Python PostgreSQL adapter) instead of psycopg2-binary
echo for local development. The Docker containers will still use psycopg2-binary.
echo.
echo You can now run the services with Docker Compose: docker-compose up -d
