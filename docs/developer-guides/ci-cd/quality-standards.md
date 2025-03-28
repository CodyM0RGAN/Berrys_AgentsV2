# Quality Standards

This document defines the quality standards for the Berrys_AgentsV2 codebase. It outlines the requirements for code quality, test coverage, and security that all services must meet.

## Table of Contents

- [Overview](#overview)
- [Code Quality](#code-quality)
- [Test Coverage](#test-coverage)
- [Security](#security)
- [Quality Gates](#quality-gates)
- [Enforcement](#enforcement)
- [Exceptions](#exceptions)

## Overview

Quality standards are enforced through the CI/CD pipeline to ensure that all code meets the required level of quality. These standards are designed to:

- Improve code readability and maintainability
- Reduce bugs and technical debt
- Ensure consistent code style across the codebase
- Identify and fix security vulnerabilities
- Ensure adequate test coverage

## Code Quality

### Style Guidelines

All Python code must follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide, with the following modifications:

- Maximum line length: 100 characters
- Use double quotes for strings
- Use trailing commas in multi-line lists, dictionaries, and function calls
- Use spaces around operators and after commas
- Use 4 spaces for indentation (no tabs)
- Use blank lines to separate logical sections of code
- Use docstrings for all modules, classes, and functions

### Linting Tools

The following linting tools are used to enforce code quality:

#### Flake8

[Flake8](https://flake8.pycqa.org/) is used to check for PEP 8 compliance and common programming errors. The configuration is defined in `.flake8`:

```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,build,dist
ignore = E203, W503
```

#### Pylint

[Pylint](https://pylint.org/) is used for more comprehensive code analysis. The configuration is defined in `.pylintrc`:

```ini
[MASTER]
ignore=CVS
ignore-patterns=
persistent=yes
load-plugins=

[MESSAGES CONTROL]
disable=C0111,C0103,C0303,W0613,R0903,R0913,R0914,R0902,R0801,W0212,C0111,C0103,C0303,W0613

[REPORTS]
output-format=text
reports=yes
evaluation=10.0 - ((float(5 * error + warning + refactor + convention) / statement) * 10)

[BASIC]
good-names=i,j,k,ex,Run,_

[FORMAT]
max-line-length=100

[DESIGN]
max-args=10
max-attributes=15
```

#### Black

[Black](https://black.readthedocs.io/) is used for code formatting. The configuration is defined in `pyproject.toml`:

```toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'
exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
```

#### isort

[isort](https://pycqa.github.io/isort/) is used to sort imports. The configuration is defined in `pyproject.toml`:

```toml
[tool.isort]
profile = "black"
line_length = 100
```

#### mypy

[mypy](http://mypy-lang.org/) is used for static type checking. The configuration is defined in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
disallow_incomplete_defs = false
```

### Code Organization

- Each service should be organized into logical modules
- Each module should have a clear responsibility
- Each class and function should have a single responsibility
- Code should be DRY (Don't Repeat Yourself)
- Use appropriate design patterns
- Avoid deep nesting of code
- Keep functions and methods short and focused

### Naming Conventions

- Use descriptive names for variables, functions, classes, and modules
- Use `snake_case` for variables, functions, and modules
- Use `PascalCase` for classes
- Use `UPPER_CASE` for constants
- Use `_private_name` for private variables, functions, and methods
- Use `__dunder__` for special methods

### Documentation

- All modules, classes, and functions should have docstrings
- Docstrings should follow the [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Complex code should be commented
- Use type hints for function parameters and return values
- Keep documentation up to date

## Test Coverage

### Coverage Requirements

- All services must have at least 80% code coverage
- All critical code paths must have 100% coverage
- All edge cases must be tested
- All error conditions must be tested

### Test Types

The following types of tests are required:

#### Unit Tests

- Test individual functions and methods
- Mock external dependencies
- Focus on testing business logic
- Should be fast and isolated

#### Integration Tests

- Test interactions between components
- Test database interactions
- Test API interactions
- May use real dependencies or mocks

#### API Tests

- Test API endpoints
- Test request validation
- Test response validation
- Test error handling

### Test Organization

- Tests should be organized by module and test type
- Test files should be named `test_*.py`
- Test classes should be named `Test*`
- Test functions should be named `test_*`
- Tests should be in a `tests` directory at the same level as the code being tested

### Test Quality

- Tests should be readable and maintainable
- Tests should be independent and idempotent
- Tests should have clear assertions
- Tests should have meaningful names
- Tests should not have hardcoded values
- Tests should not have unnecessary complexity

## Security

### Security Scanning

The following security scanning tools are used:

#### Bandit

[Bandit](https://bandit.readthedocs.io/) is used to find common security issues in Python code. The configuration is defined in `.bandit`:

```ini
[bandit]
exclude = tests
```

#### Safety

[Safety](https://pyup.io/safety/) is used to check for known vulnerabilities in dependencies. The configuration is defined in `.safety`:

```ini
[safety]
ignore = 1234,5678
```

### Security Requirements

- All code must pass security scanning
- All dependencies must be free of known vulnerabilities
- All user input must be validated
- All sensitive data must be encrypted
- All authentication and authorization must be properly implemented
- All API endpoints must be properly secured
- All error messages must not reveal sensitive information

## Quality Gates

The following quality gates must be passed before code can be merged:

### Build Gate

- Code must compile without errors
- All dependencies must be installed successfully
- All imports must be valid

### Test Gate

- All tests must pass
- Code coverage must meet the required threshold
- No test failures or errors

### Quality Gate

- Code must pass all linting checks
- Code must pass all security checks
- No critical or high-severity issues

### Deploy Gate

- Service must deploy successfully
- Service must pass health checks
- Service must pass verification tests

## Enforcement

Quality standards are enforced through the CI/CD pipeline. The pipeline includes the following checks:

### Pull Request Checks

- Build check
- Test check
- Quality check
- Security check

### Merge Checks

- All pull request checks must pass
- Code must be reviewed and approved
- No merge conflicts

### Deployment Checks

- All merge checks must pass
- Deployment must be successful
- Verification tests must pass

## Exceptions

Exceptions to quality standards may be granted in the following cases:

### Temporary Exceptions

- Critical bug fixes
- Emergency deployments
- Time-sensitive features

### Permanent Exceptions

- Legacy code
- Third-party code
- Generated code

### Exception Process

To request an exception:

1. Create an issue in the issue tracker
2. Provide a detailed explanation of why the exception is needed
3. Specify which quality standards are being excepted
4. Provide a plan for addressing the exception in the future
5. Get approval from the technical lead

Exceptions should be documented and reviewed regularly to ensure they are still necessary.
