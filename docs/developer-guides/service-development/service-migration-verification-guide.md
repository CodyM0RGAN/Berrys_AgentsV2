# Service Migration Verification Guide

This guide provides detailed information about verifying service migrations in the Berrys_AgentsV2 system. It explains how to verify that a service has been successfully migrated to a new version, how to run migration verification tests, and how to integrate migration verification with the CI/CD pipeline.

## Table of Contents

- [Overview](#overview)
- [Migration Verification Framework](#migration-verification-framework)
- [Verification Types](#verification-types)
- [Writing Verification Tests](#writing-verification-tests)
- [Running Verification Tests](#running-verification-tests)
- [Integration with CI/CD](#integration-with-cicd)
- [Best Practices](#best-practices)

## Overview

Service migration verification is a critical part of the deployment process for the Berrys_AgentsV2 system. It ensures that services are correctly migrated to new versions without data loss or functionality regression. The migration verification framework is designed to:

- Verify that database migrations are applied correctly
- Verify that service functionality works as expected after migration
- Verify that data is preserved and accessible after migration
- Verify that API contracts are maintained after migration
- Integrate with the CI/CD pipeline to automate verification

## Migration Verification Framework

The migration verification framework is built on top of the testing framework and provides additional utilities for verifying service migrations. It includes:

- Base verification test classes
- Fixtures for migration verification
- Utilities for comparing service state before and after migration
- Configuration for verification test discovery and execution
- Reporting utilities for verification results

The framework is located in the `shared/utils/tests/framework` directory and includes the following components:

- `base.py`: Base test classes, including migration verification classes
- `fixtures.py`: Common test fixtures, including migration verification fixtures
- `database.py`: Database utilities, including migration verification utilities
- `api.py`: API testing utilities, including migration verification utilities
- `reporting.py`: Test reporting utilities, including migration verification reporting

## Verification Types

The migration verification framework supports the following types of verification:

### Database Migration Verification

Database migration verification tests verify that database migrations are applied correctly and that data is preserved and accessible after migration.

Example database migration verification test:

```python
from shared.utils.tests.framework.base import BaseDatabaseMigrationVerificationTest
from services.tool_integration.src.models import Tool

class TestToolDatabaseMigration(BaseDatabaseMigrationVerificationTest):
    def test_tool_table_migration(self):
        # Arrange
        # Create a tool in the old database
        old_tool = Tool(id="test-tool", name="Test Tool")
        self.old_session.add(old_tool)
        self.old_session.commit()
        
        # Act
        # Run the migration
        self.run_migration()
        
        # Assert
        # Verify that the tool exists in the new database
        new_tool = self.new_session.query(Tool).filter_by(id="test-tool").first()
        self.assertIsNotNone(new_tool)
        self.assertEqual("Test Tool", new_tool.name)
```

### API Migration Verification

API migration verification tests verify that API contracts are maintained after migration and that service functionality works as expected.

Example API migration verification test:

```python
from shared.utils.tests.framework.base import BaseAPIMigrationVerificationTest
from services.tool_integration.src.main import app

class TestToolAPIMigration(BaseAPIMigrationVerificationTest):
    def setUp(self):
        super().setUp()
        self.app = app
        self.client = self.app.test_client()
    
    def test_get_tool_by_id_api(self):
        # Arrange
        # Create a tool in the database
        tool_id = "test-tool"
        expected_tool = {"id": tool_id, "name": "Test Tool"}
        self.mock_database.add_tool(expected_tool)
        
        # Act
        # Call the API
        response = self.client.get(f"/tools/{tool_id}")
        
        # Assert
        # Verify that the API returns the expected tool
        self.assertEqual(200, response.status_code)
        self.assertEqual(expected_tool, response.json)
```

### Functional Migration Verification

Functional migration verification tests verify that service functionality works as expected after migration.

Example functional migration verification test:

```python
from shared.utils.tests.framework.base import BaseFunctionalMigrationVerificationTest
from services.tool_integration.src.tool_curator import ToolCurator

class TestToolFunctionalMigration(BaseFunctionalMigrationVerificationTest):
    def test_get_tool_by_id_functionality(self):
        # Arrange
        # Create a tool curator with the old version
        old_curator = ToolCurator(version="1.0.0")
        # Create a tool curator with the new version
        new_curator = ToolCurator(version="2.0.0")
        
        # Add a tool to both curators
        tool_id = "test-tool"
        expected_tool = {"id": tool_id, "name": "Test Tool"}
        old_curator.add_tool(expected_tool)
        new_curator.add_tool(expected_tool)
        
        # Act
        # Get the tool from both curators
        old_tool = old_curator.get_tool_by_id(tool_id)
        new_tool = new_curator.get_tool_by_id(tool_id)
        
        # Assert
        # Verify that both curators return the same tool
        self.assertEqual(old_tool, new_tool)
```

## Writing Verification Tests

### Test Organization

Verification tests should be organized by module and verification type. For example, tests for the `tool_curator` module should be in the `tests/test_tool_curator_migration.py` file.

### Test Structure

Verification tests should follow the Arrange-Act-Assert (AAA) pattern:

1. **Arrange**: Set up the test data and environment for both old and new versions
2. **Act**: Perform the migration or action being verified
3. **Assert**: Verify the expected outcome

Example:

```python
def test_tool_table_migration(self):
    # Arrange
    # Create a tool in the old database
    old_tool = Tool(id="test-tool", name="Test Tool")
    self.old_session.add(old_tool)
    self.old_session.commit()
    
    # Act
    # Run the migration
    self.run_migration()
    
    # Assert
    # Verify that the tool exists in the new database
    new_tool = self.new_session.query(Tool).filter_by(id="test-tool").first()
    self.assertIsNotNone(new_tool)
    self.assertEqual("Test Tool", new_tool.name)
```

### Test Naming

Verification test functions should be named `test_<module>_<verification_type>_<scenario>`. For example, `test_tool_table_migration_with_existing_data` for a test that verifies the migration of the tool table with existing data.

### Test Classes

Verification test classes should inherit from the appropriate base verification test class:

- `BaseDatabaseMigrationVerificationTest` for database migration verification
- `BaseAPIMigrationVerificationTest` for API migration verification
- `BaseFunctionalMigrationVerificationTest` for functional migration verification

Example:

```python
from shared.utils.tests.framework.base import BaseDatabaseMigrationVerificationTest

class TestToolDatabaseMigration(BaseDatabaseMigrationVerificationTest):
    def test_tool_table_migration(self):
        # Test implementation
```

## Running Verification Tests

### Running Verification Tests Locally

To run verification tests locally, use the `run_migration_verification.py` script in the service directory:

```bash
cd services/tool-integration
python run_migration_verification.py
```

Or use the provided shell scripts:

```bash
cd services/tool-integration
./run_migration_verification.sh  # Linux/macOS
run_migration_verification.bat   # Windows
```

### Running Specific Verification Tests

To run specific verification tests, use the `-k` option:

```bash
cd services/tool-integration
python run_migration_verification.py -k test_tool_table_migration
```

### Running Verification Tests with Different Versions

To run verification tests with different versions, use the `--old-version` and `--new-version` options:

```bash
cd services/tool-integration
python run_migration_verification.py --old-version=1.0.0 --new-version=2.0.0
```

## Integration with CI/CD

The migration verification framework is integrated with the CI/CD pipeline to ensure that service migrations are verified before deployment.

### CI/CD Pipeline

The CI/CD pipeline runs migration verification tests as part of the deployment process. The pipeline includes the following steps:

1. **Build**: Build the service
2. **Test**: Run tests and measure coverage
3. **Quality**: Check code quality and security
4. **Verify Migration**: Run migration verification tests
5. **Deploy**: Deploy the service if all checks pass

### Verification Reports

The CI/CD pipeline generates verification reports for each service. These reports include:

- Verification results (pass/fail)
- Verification logs
- Verification execution time

### Quality Gates

The CI/CD pipeline includes quality gates that must be passed before a service can be deployed:

- All verification tests must pass
- No critical or high-severity issues

## Best Practices

### Comprehensive Verification

Verify all aspects of the service migration, including database schema, data, API contracts, and functionality.

### Data Preservation

Ensure that data is preserved and accessible after migration. Verify that data is correctly migrated and that no data is lost.

### API Compatibility

Maintain API compatibility between versions. Verify that API contracts are maintained and that clients can continue to use the API without changes.

### Rollback Plan

Have a rollback plan in case the migration fails. Verify that the rollback process works correctly.

### Incremental Migration

Prefer incremental migrations over big-bang migrations. Verify each incremental migration separately.

### Test Coverage

Ensure that verification tests cover all critical aspects of the service. Use coverage reports to identify areas that need more verification.

### Automation

Automate the verification process as much as possible. Use the CI/CD pipeline to run verification tests automatically.

### Documentation

Document the migration process and verification results. Include information about what was migrated, what was verified, and any issues encountered.

### Monitoring

Monitor the service after migration to ensure that it continues to function correctly. Set up alerts for any issues that may arise.

### Continuous Improvement

Continuously improve the migration verification process based on lessons learned from previous migrations.
