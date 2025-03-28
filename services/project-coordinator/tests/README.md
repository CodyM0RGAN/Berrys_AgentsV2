# Project Coordinator Tests

This directory contains tests for the Project Coordinator service.

## Test Structure

- `test_project_creation.py`: Tests for project creation functionality, including handling of the status field

## Database Setup

Tests run against the `mas_framework_test` database, which is a separate PostgreSQL database from the development and production databases. This ensures that tests don't affect development or production data.

The test database is automatically selected when the `ENVIRONMENT` environment variable is set to `test`, which is done by the test scripts.

## Running Tests

You can run the tests using one of the following scripts:

### Linux/macOS

```bash
./run_tests.sh
```

### Windows (Command Prompt)

```cmd
run_tests.bat
```

### Windows (PowerShell)

```powershell
.\run_tests.ps1
```

## Adding New Tests

When adding new tests, follow these guidelines:

1. Create a new test file with a descriptive name (e.g., `test_feature_name.py`)
2. Use pytest fixtures for common setup and teardown
3. Write clear test function names that describe what is being tested
4. Add docstrings to test functions to explain the purpose of the test
5. Use assertions to verify expected behavior

## Test Database Transactions

Tests use database transactions that are rolled back after each test, ensuring that tests don't affect each other. This means you can create, modify, and delete data in your tests without worrying about cleaning up afterward.

## Mocking Dependencies

For tests that require mocking dependencies (e.g., external services), use pytest's monkeypatch fixture or unittest.mock.

Example:

```python
def test_function_with_mocked_dependency(monkeypatch):
    # Mock a dependency
    monkeypatch.setattr("module.function", lambda x: "mocked result")
    
    # Test the function that uses the dependency
    result = function_under_test()
    
    # Verify the result
    assert result == "expected result"
```

## Preserving Test Data

If you need to preserve certain test data between test runs, you can mark it for preservation using the `mark_test_data_preserve` function:

```bash
# Mark a record for preservation
./shared/database/data_management.sh mark table_name record_id true
```

This will prevent the record from being deleted when the test database is reset.

## Further Reading

For more information about the multi-database setup, see the [Multi-Database Setup Guide](../../../docs/best-practices/multi-database-setup.md).
