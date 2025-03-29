# Testing Guide

This guide provides detailed information about the testing framework for the Berrys_AgentsV2 system. It explains how to write tests, run tests, and integrate tests with the CI/CD pipeline.

## Table of Contents

- [Overview](#overview)
- [Testing Framework](#testing-framework)
- [Test Types](#test-types)
- [Writing Tests](#writing-tests)
- [Running Tests](#running-tests)
- [Test Fixtures](#test-fixtures)
- [Mocking](#mocking)
- [Test Coverage](#test-coverage)
- [Integration with CI/CD](#integration-with-cicd)
- [Best Practices](#best-practices)

## Overview

The Berrys_AgentsV2 system uses a comprehensive testing framework to ensure code quality and reliability. The testing framework is designed to:

- Make it easy to write and run tests
- Support different types of tests (unit, integration, API)
- Provide useful fixtures and utilities
- Generate detailed test reports
- Integrate with the CI/CD pipeline

## Testing Framework

The testing framework is built on top of [pytest](https://docs.pytest.org/), a powerful and flexible testing framework for Python. It includes:

- Base test classes for different types of tests
- Fixtures for common test scenarios
- Utilities for mocking and patching
- Configuration for test discovery and execution
- Reporting utilities for test results and coverage

The framework is located in the `shared/utils/tests/framework` directory and includes the following components:

- `base.py`: Base test classes
- `fixtures.py`: Common test fixtures
- `mock_data.py`: Mock data for testing
- `database.py`: Database utilities for testing
- `api.py`: API testing utilities
- `config.py`: Test configuration
- `performance.py`: Performance testing utilities
- `reporting.py`: Test reporting utilities
- `utils.py`: Miscellaneous test utilities
- `constants.py`: Constants used in tests

## Test Types

The testing framework supports the following types of tests:

### Unit Tests

Unit tests test individual functions, methods, or classes in isolation. They should be fast, isolated, and focused on testing business logic. Unit tests should mock external dependencies to ensure isolation.

Example unit test:

```python
from shared.utils.tests.framework.base import BaseUnitTest
from services.tool_integration.src.tool_curator import ToolCurator

class TestToolCurator(BaseUnitTest):
    def test_get_tool_by_id(self):
        # Arrange
        curator = ToolCurator()
        tool_id = "test-tool"
        expected_tool = {"id": tool_id, "name": "Test Tool"}
        curator._tools = {tool_id: expected_tool}
        
        # Act
        actual_tool = curator.get_tool_by_id(tool_id)
        
        # Assert
        self.assertEqual(expected_tool, actual_tool)
```

### Integration Tests

Integration tests test the interaction between components, such as services, databases, and external APIs. They should verify that components work together correctly.

Example integration test:

```python
from shared.utils.tests.framework.base import BaseIntegrationTest
from services.tool_integration.src.tool_curator import ToolCurator
from services.tool_integration.src.tool_repository import ToolRepository

class TestToolCuratorIntegration(BaseIntegrationTest):
    def test_get_tool_by_id_from_repository(self):
        # Arrange
        repository = ToolRepository()
        curator = ToolCurator(repository=repository)
        tool_id = "test-tool"
        expected_tool = {"id": tool_id, "name": "Test Tool"}
        repository.add_tool(expected_tool)
        
        # Act
        actual_tool = curator.get_tool_by_id(tool_id)
        
        # Assert
        self.assertEqual(expected_tool, actual_tool)
```

### API Tests

API tests test the API endpoints of a service. They should verify that the API behaves correctly, including request validation, response validation, and error handling.

Example API test:

```python
from shared.utils.tests.framework.base import BaseAPITest
from services.tool_integration.src.main import app

class TestToolCuratorAPI(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.app = app
        self.client = self.app.test_client()
    
    def test_get_tool_by_id(self):
        # Arrange
        tool_id = "test-tool"
        expected_tool = {"id": tool_id, "name": "Test Tool"}
        self.mock_database.add_tool(expected_tool)
        
        # Act
        response = self.client.get(f"/tools/{tool_id}")
        
        # Assert
        self.assertEqual(200, response.status_code)
        self.assertEqual(expected_tool, response.json)
```

## Writing Tests

### Test Organization

Tests should be organized by module and test type. For example, tests for the `tool_curator` module should be in the `tests/test_tool_curator.py` file for unit tests and `tests/test_tool_curator_integration.py` file for integration tests.

### Test Structure

Tests should follow the Arrange-Act-Assert (AAA) pattern:

1. **Arrange**: Set up the test data and environment
2. **Act**: Perform the action being tested
3. **Assert**: Verify the expected outcome

Example:

```python
def test_get_tool_by_id(self):
    # Arrange
    curator = ToolCurator()
    tool_id = "test-tool"
    expected_tool = {"id": tool_id, "name": "Test Tool"}
    curator._tools = {tool_id: expected_tool}
    
    # Act
    actual_tool = curator.get_tool_by_id(tool_id)
    
    # Assert
    self.assertEqual(expected_tool, actual_tool)
```

### Test Naming

Test functions should be named `test_<function_name>_<scenario>`. For example, `test_get_tool_by_id_not_found` for a test that verifies the behavior when a tool is not found.

### Test Classes

Test classes should inherit from the appropriate base test class:

- `BaseUnitTest` for unit tests
- `BaseIntegrationTest` for integration tests
- `BaseAPITest` for API tests

Example:

```python
from shared.utils.tests.framework.base import BaseUnitTest

class TestToolCurator(BaseUnitTest):
    def test_get_tool_by_id(self):
        # Test implementation
```

## Running Tests

### Running Tests Locally

To run tests locally, use the `run_tests.py` script in the service directory:

```bash
cd services/tool-integration
python run_tests.py
```

Or use the provided shell scripts:

```bash
cd services/tool-integration
./run_tests.sh  # Linux/macOS
run_tests.bat   # Windows
```

### Running Specific Tests

To run specific tests, use the `-k` option:

```bash
cd services/tool-integration
python run_tests.py -k test_get_tool_by_id
```

### Running Tests with Coverage

To run tests with coverage, use the `--cov` option:

```bash
cd services/tool-integration
python run_tests.py --cov=src
```

## Test Fixtures

Test fixtures are functions that set up the test environment and provide test data. The testing framework provides several fixtures for common test scenarios.

### Database Fixtures

The `database` fixture provides a database connection for testing:

```python
def test_get_tool_by_id_from_database(self, database):
    # Test implementation using database
```

### API Fixtures

The `client` fixture provides an API client for testing:

```python
def test_get_tool_by_id_api(self, client):
    # Test implementation using client
```

### Mock Fixtures

The `mock_database` fixture provides a mock database for testing:

```python
def test_get_tool_by_id_with_mock(self, mock_database):
    # Test implementation using mock_database
```

### Custom Fixtures

You can define custom fixtures in the `conftest.py` file in the test directory:

```python
import pytest

@pytest.fixture
def tool_curator():
    from services.tool_integration.src.tool_curator import ToolCurator
    return ToolCurator()
```

## Mocking

Mocking is used to replace real objects with mock objects for testing. The testing framework provides utilities for mocking.

### Mocking Functions

To mock a function, use the `patch` decorator:

```python
from unittest.mock import patch

@patch('services.tool_integration.src.tool_repository.ToolRepository.get_tool')
def test_get_tool_by_id_mocked(self, mock_get_tool):
    # Arrange
    mock_get_tool.return_value = {"id": "test-tool", "name": "Test Tool"}
    curator = ToolCurator()
    
    # Act
    tool = curator.get_tool_by_id("test-tool")
    
    # Assert
    self.assertEqual("Test Tool", tool["name"])
    mock_get_tool.assert_called_once_with("test-tool")
```

### Mocking Classes

To mock a class, use the `patch` decorator with `autospec=True`:

```python
from unittest.mock import patch

@patch('services.tool_integration.src.tool_repository.ToolRepository', autospec=True)
def test_get_tool_by_id_mocked_class(self, MockToolRepository):
    # Arrange
    mock_repository = MockToolRepository.return_value
    mock_repository.get_tool.return_value = {"id": "test-tool", "name": "Test Tool"}
    curator = ToolCurator(repository=mock_repository)
    
    # Act
    tool = curator.get_tool_by_id("test-tool")
    
    # Assert
    self.assertEqual("Test Tool", tool["name"])
    mock_repository.get_tool.assert_called_once_with("test-tool")
```

### Mocking HTTP Requests

To mock HTTP requests, use the `responses` library:

```python
import responses

@responses.activate
def test_get_tool_from_external_api(self):
    # Arrange
    responses.add(
        responses.GET,
        "https://api.example.com/tools/test-tool",
        json={"id": "test-tool", "name": "Test Tool"},
        status=200,
    )
    curator = ToolCurator()
    
    # Act
    tool = curator.get_tool_from_external_api("test-tool")
    
    # Assert
    self.assertEqual("Test Tool", tool["name"])
```

## Test Coverage

Test coverage measures how much of the code is covered by tests. The testing framework uses [coverage.py](https://coverage.readthedocs.io/) to measure test coverage.

### Measuring Coverage

To measure coverage, run tests with the `--cov` option:

```bash
cd services/tool-integration
python run_tests.py --cov=src
```

### Coverage Reports

To generate a coverage report, run tests with the `--cov-report` option:

```bash
cd services/tool-integration
python run_tests.py --cov=src --cov-report=html
```

This will generate an HTML coverage report in the `htmlcov` directory.

### Coverage Requirements

The CI/CD pipeline requires a minimum coverage of 80% for all services. Critical code paths should have 100% coverage.

## Integration with CI/CD

The testing framework is integrated with the CI/CD pipeline to ensure that all code meets the required quality standards.

### CI/CD Pipeline

The CI/CD pipeline runs tests for all services and generates reports. The pipeline includes the following steps:

1. **Build**: Build the service
2. **Test**: Run tests and measure coverage
3. **Quality**: Check code quality and security
4. **Deploy**: Deploy the service if all checks pass

### Test Reports

The CI/CD pipeline generates test reports for each service. These reports include:

- Test results (pass/fail)
- Test coverage
- Test execution time
- Test logs

### Quality Gates

The CI/CD pipeline includes quality gates that must be passed before code can be merged:

- All tests must pass
- Code coverage must meet the required threshold
- No critical or high-severity issues

## Best Practices

### Test Independence

Tests should be independent and idempotent. Each test should be able to run in isolation and should not depend on the state left by other tests.

### Test Readability

Tests should be readable and maintainable. Use descriptive names, clear assertions, and avoid unnecessary complexity.

### Test Coverage

Aim for high test coverage, especially for critical code paths. Use coverage reports to identify areas that need more tests.

### Test Performance

Tests should be fast. Slow tests slow down development and discourage testing. Use mocking to avoid slow external dependencies.

### Test Maintenance

Keep tests up to date as the code changes. Refactor tests when necessary to maintain readability and maintainability.

### Test First

Consider writing tests before writing code (Test-Driven Development). This helps ensure that code is testable and meets requirements.

### Test Edge Cases

Test edge cases and error conditions. Don't just test the happy path.

### Test Refactoring

Refactor tests when necessary to maintain readability and maintainability. Don't be afraid to change tests as the code evolves.

### Test Documentation

Document tests with clear comments and docstrings. Explain what the test is testing and why.

### Test Review

Review tests as part of code review. Ensure that tests are comprehensive, readable, and maintainable.
