# Testing Framework

This document describes the comprehensive testing framework implemented for the Berrys_AgentsV2 platform. The framework provides a robust set of utilities and patterns for unit testing, integration testing, contract testing, schema validation, and performance testing.

## Overview

The testing framework is designed to be:

- **Comprehensive**: Cover all aspects of the system from unit to integration testing
- **Standardized**: Provide consistent patterns across all services
- **Extensible**: Easy to add new test types and patterns
- **Maintainable**: Well-documented and organized 
- **Performance-aware**: Include tools for performance benchmarking and regression detection

## Test Types

### Unit Tests

Unit tests verify the behavior of individual components in isolation. They should be:
- Fast and lightweight
- Independent of external services and databases
- Focused on testing business logic

Example:
```python
def test_agent_creation():
    """Test creating an agent with valid parameters."""
    agent = Agent(
        name="Test Agent",
        agent_type="ASSISTANT",
        status="ACTIVE",
        config={"capabilities": ["chat"]}
    )
    assert agent.name == "Test Agent"
    assert agent.agent_type == "ASSISTANT"
    assert agent.status == "ACTIVE"
```

### Database Tests

Database tests verify the interaction between application code and databases. The framework provides utilities for:
- Creating in-memory databases for testing
- Setting up test fixtures and data
- Verifying database operations

Example:
```python
def test_store_agent(test_db):
    """Test storing and retrieving an agent."""
    agent = Agent(name="Test Agent", agent_type="ASSISTANT")
    test_db.add(agent)
    test_db.commit()
    
    retrieved = test_db.query(Agent).filter_by(name="Test Agent").first()
    assert retrieved is not None
    assert retrieved.name == "Test Agent"
```

### Schema Validation Tests

Schema validation tests verify that the database schema matches the expected structure and that any changes to the schema are intentional and backwards compatible.

Example:
```python
def test_schema_completeness(schema_validator):
    """Test that the database schema matches the SQLAlchemy models."""
    differences = schema_validator.compare_schema_with_models(Base)
    assert not differences['missing_tables']
    assert not differences['column_differences']
```

### Contract Tests

Contract tests verify that service interfaces adhere to their defined contracts, ensuring compatibility between services.

Example:
```python
def test_model_orchestration_contract_request(contract_verifier):
    """Test that requests to model-orchestration conform to the contract."""
    request_data = {
        "model": "gpt-4",
        "prompt": "Generate a story about a robot learning to paint.",
        "max_tokens": 500
    }
    
    # Verify request
    validated_data = contract_verifier.verify_request(
        consumer_name="agent-orchestrator",
        provider_name="model-orchestration",
        endpoint="/v1/models/generate",
        method="POST",
        request_data=request_data
    )
    
    # Should not raise any validation errors
    assert validated_data is not None
```

### Integration Tests

Integration tests verify the interaction between multiple components or services, ensuring they work together correctly.

Example:
```python
@integration_test(
    services=["agent-orchestrator"],
    mock_services=["model-orchestration", "project-coordinator"]
)
async def test_agent_lifecycle_with_service_harness(harness, mock_services):
    """Test agent lifecycle using the integration test harness."""
    # Set up mock services
    model_orch = mock_services["model-orchestration"]
    model_orch.add_endpoint(
        path="/v1/models/generate",
        method="POST",
        response_data={"choices": [{"text": "Mock response"}]}
    )
    
    # Test service interactions
    agent_orch = harness.get_service("agent-orchestrator")
    response = agent_orch.post("/v1/agents", json={"name": "Test Agent"})
    assert response.status_code == 200
```

### Performance Tests

Performance tests measure and benchmark the performance of critical parts of the system, helping to identify regressions and bottlenecks.

Example:
```python
@benchmark(iterations=100, warmup=5)
def test_agent_serialization_performance():
    """Test performance of agent serialization."""
    agent = Agent(name="Test Agent", agent_type="ASSISTANT")
    return {
        "id": agent.id,
        "name": agent.name,
        "agent_type": agent.agent_type
    }
```

## Test Coverage

The framework includes tools for collecting and reporting test coverage, with quality gates in the CI/CD pipeline to ensure adequate coverage.

Coverage reports are generated in multiple formats:
- HTML: For human-readable reports
- XML: For integration with CI/CD systems
- JSON: For programmatic consumption
- Badge: For displaying in READMEs and documentation

## Directory Structure

Tests should be organized as follows:

```
services/[service-name]/
  tests/
    __init__.py
    conftest.py                    # Shared fixtures
    test_[component].py            # Unit tests
    integration/                   # Integration tests
      test_[integration_type].py
    performance/                   # Performance tests
      test_[performance_type].py
    contract/                      # Contract tests
      test_[contract_type].py
```

## Running Tests

### Running All Tests

To run all tests for a service:

```bash
cd services/[service-name]
python -m pytest
```

### Running Specific Test Types

To run only unit tests:

```bash
python -m pytest tests/ --ignore=tests/integration --ignore=tests/performance
```

To run only integration tests:

```bash
python -m pytest tests/integration/
```

To run performance tests:

```bash
python -m pytest tests/performance/
```

### Running with Coverage

To run tests with coverage reporting:

```bash
python -m pytest --cov=src --cov-report=html --cov-report=xml
```

## Test Fixtures

The framework provides a set of reusable fixtures for common testing needs:

- `test_db_engine`: An in-memory SQLAlchemy engine
- `test_db`: A SQLAlchemy session for testing
- `mock_service_client`: A mock for service clients
- `test_config`: A standardized test configuration
- `integration_harness`: A harness for integration testing
- `mock_integration_service`: A mock service for integration testing

## Best Practices

### General Guidelines

1. **Test Independence**: Tests should be independent and not rely on the state from other tests
2. **Test Isolation**: Tests should be isolated from external dependencies
3. **Test Readability**: Tests should be clear and readable
4. **Test Maintainability**: Tests should be easy to maintain
5. **Test Performance**: Tests should be fast whenever possible

### Unit Test Best Practices

1. Follow the Arrange-Act-Assert pattern
2. Test one behavior per test
3. Use descriptive test names
4. Use fixtures for common setup
5. Mock external dependencies

### Integration Test Best Practices

1. Focus on service boundaries
2. Use mock services for external dependencies
3. Clean up after tests
4. Use retries for flaky operations
5. Test error cases and happy paths

### Contract Test Best Practices

1. Define contracts explicitly
2. Test both consumer and provider sides
3. Verify request and response formats
4. Include validation for required fields
5. Test error cases

### Performance Test Best Practices

1. Include warmup iterations
2. Run multiple iterations for stability
3. Set clear performance thresholds
4. Include benchmarks in CI/CD pipelines
5. Track performance trends over time

## CI/CD Integration

The testing framework is integrated with the CI/CD pipeline through workflow templates in `.github/workflows/templates/`:

- `testing.yml`: Template for running tests and reporting coverage
- `performance.yml`: Template for running performance tests and detecting regressions

These templates are used by service-specific workflows like `agent-orchestrator-tests.yml`.

## Extending the Framework

To extend the testing framework:

1. Add new utilities to the appropriate module in `shared/utils/src/testing/`
2. Add documentation for new utilities
3. Add example tests for new test types
4. Update this guide with new test types and best practices
