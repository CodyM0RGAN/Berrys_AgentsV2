# CI/CD Pipeline Troubleshooting Guide

This guide provides solutions for common issues encountered with the CI/CD pipeline for the Berrys_AgentsV2 system. It covers build failures, test failures, quality check failures, and deployment issues.

## Table of Contents

- [General Troubleshooting](#general-troubleshooting)
- [Build Issues](#build-issues)
- [Test Issues](#test-issues)
- [Quality Check Issues](#quality-check-issues)
- [Deployment Issues](#deployment-issues)
- [GitHub Actions Issues](#github-actions-issues)
- [Getting Help](#getting-help)

## General Troubleshooting

### Pipeline Not Triggered

**Issue**: The pipeline is not triggered when changes are pushed to the repository.

**Solutions**:

1. **Check Workflow Triggers**: Ensure that the workflow file has the correct triggers configured:

   ```yaml
   on:
     push:
       branches: [ main ]
       paths:
         - 'services/my-service/**'
         - 'shared/**'
         - '.github/workflows/my-service.yml'
     pull_request:
       branches: [ main ]
       paths:
         - 'services/my-service/**'
         - 'shared/**'
         - '.github/workflows/my-service.yml'
   ```

2. **Check File Paths**: Ensure that the changes are in the paths specified in the workflow triggers.

3. **Check Branch**: Ensure that the changes are pushed to the branch specified in the workflow triggers.

4. **Check Workflow File**: Ensure that the workflow file is valid YAML and does not contain syntax errors.

### Pipeline Fails with No Clear Error

**Issue**: The pipeline fails without a clear error message.

**Solutions**:

1. **Check Workflow Logs**: Check the workflow logs in GitHub Actions for error messages.

2. **Check Step Outputs**: Check the outputs of each step in the workflow for error messages.

3. **Enable Debug Logging**: Enable debug logging in GitHub Actions by setting the `ACTIONS_RUNNER_DEBUG` secret to `true`.

4. **Check Dependencies**: Ensure that all dependencies are available and correctly configured.

## Build Issues

### Dependency Installation Fails

**Issue**: The dependency installation step fails with errors.

**Solutions**:

1. **Check Requirements File**: Ensure that the requirements.txt file exists and contains valid dependencies.

2. **Check Python Version**: Ensure that the Python version specified in the workflow is compatible with the dependencies.

3. **Check Package Availability**: Ensure that all packages are available in the Python Package Index (PyPI).

4. **Check Package Compatibility**: Ensure that all packages are compatible with each other.

Example error:

```
ERROR: Could not find a version that satisfies the requirement package-name==1.0.0
```

Solution: Update the package version to one that is available in PyPI.

### Import Errors

**Issue**: The build fails with import errors.

**Solutions**:

1. **Check Package Installation**: Ensure that all required packages are installed.

2. **Check Import Paths**: Ensure that the import paths are correct.

3. **Check Python Path**: Ensure that the Python path includes the necessary directories.

Example error:

```
ImportError: No module named 'module_name'
```

Solution: Install the missing module or correct the import path.

### Build Artifacts Not Cached

**Issue**: Build artifacts are not cached between workflow runs.

**Solutions**:

1. **Check Cache Configuration**: Ensure that the cache configuration is correct:

   ```yaml
   - name: Cache build artifacts
     if: ${{ inputs.cache_dependencies }}
     uses: actions/cache@v3
     with:
       path: |
         ${{ inputs.working_directory }}/__pycache__
         ${{ inputs.working_directory }}/**/__pycache__
       key: ${{ runner.os }}-build-${{ inputs.service_name }}-${{ github.sha }}
       restore-keys: |
         ${{ runner.os }}-build-${{ inputs.service_name }}-
   ```

2. **Check Cache Key**: Ensure that the cache key is unique for each workflow run but has a common prefix for restore keys.

3. **Check Cache Paths**: Ensure that the cache paths include all necessary directories.

## Test Issues

### Tests Fail

**Issue**: Tests fail with errors.

**Solutions**:

1. **Check Test Code**: Ensure that the test code is correct and up to date.

2. **Check Test Dependencies**: Ensure that all test dependencies are installed.

3. **Check Test Environment**: Ensure that the test environment is correctly set up.

4. **Check Test Data**: Ensure that the test data is available and correct.

Example error:

```
AssertionError: assert 1 == 2
```

Solution: Fix the test or the code being tested.

### Tests Timeout

**Issue**: Tests timeout before completing.

**Solutions**:

1. **Check Test Duration**: Ensure that the tests do not take too long to run.

2. **Check Test Parallelism**: Ensure that the test parallelism is configured correctly.

3. **Check Test Dependencies**: Ensure that the tests do not have deadlocks or infinite loops.

Example error:

```
Timeout: Test took longer than 60 seconds to complete
```

Solution: Optimize the tests or increase the timeout.

### Coverage Below Threshold

**Issue**: Test coverage is below the required threshold.

**Solutions**:

1. **Check Coverage Report**: Check the coverage report to identify areas with low coverage.

2. **Add Tests**: Add tests for areas with low coverage.

3. **Exclude Non-Testable Code**: Exclude non-testable code from coverage calculations.

Example error:

```
Coverage of 75.0% does not meet the required threshold of 80.0%
```

Solution: Add tests to increase coverage or adjust the threshold if necessary.

## Quality Check Issues

### Linting Errors

**Issue**: Linting checks fail with errors.

**Solutions**:

1. **Check Code Style**: Ensure that the code follows the required style guidelines.

2. **Fix Linting Issues**: Fix the issues reported by the linting tools.

3. **Configure Linting Tools**: Configure the linting tools to match the project's style guidelines.

Example error:

```
E501 line too long (100 > 79 characters)
```

Solution: Shorten the line or configure the linting tool to allow longer lines.

### Formatting Errors

**Issue**: Formatting checks fail with errors.

**Solutions**:

1. **Check Code Formatting**: Ensure that the code is formatted according to the required style.

2. **Run Formatters Locally**: Run the formatters locally before pushing code.

3. **Configure Formatters**: Configure the formatters to match the project's style guidelines.

Example error:

```
would reformat file.py
```

Solution: Run the formatter on the file before pushing code.

### Import Order Errors

**Issue**: Import order checks fail with errors.

**Solutions**:

1. **Check Import Order**: Ensure that imports are ordered according to the required style.

2. **Run Import Sorter Locally**: Run the import sorter locally before pushing code.

3. **Configure Import Sorter**: Configure the import sorter to match the project's style guidelines.

Example error:

```
file.py Imports are incorrectly sorted.
```

Solution: Run the import sorter on the file before pushing code.

### Type Errors

**Issue**: Type checking fails with errors.

**Solutions**:

1. **Check Type Annotations**: Ensure that type annotations are correct.

2. **Add Missing Type Annotations**: Add type annotations where they are missing.

3. **Fix Type Errors**: Fix the type errors reported by the type checker.

Example error:

```
file.py:10: error: Incompatible types in assignment (expression has type "str", variable has type "int")
```

Solution: Fix the type error by changing the type annotation or the code.

### Security Issues

**Issue**: Security checks fail with vulnerabilities.

**Solutions**:

1. **Check Vulnerabilities**: Check the reported vulnerabilities and assess their severity.

2. **Update Dependencies**: Update dependencies to versions without known vulnerabilities.

3. **Mitigate Vulnerabilities**: Implement mitigations for vulnerabilities that cannot be fixed by updating dependencies.

Example error:

```
Found security vulnerability in package-name: CVE-2023-12345
```

Solution: Update the package to a version without the vulnerability.

## Deployment Issues

### Docker Build Fails

**Issue**: Docker build fails with errors.

**Solutions**:

1. **Check Dockerfile**: Ensure that the Dockerfile is correct and up to date.

2. **Check Build Context**: Ensure that the build context contains all necessary files.

3. **Check Base Image**: Ensure that the base image is available and compatible.

Example error:

```
Step 3/10 : RUN pip install -r requirements.txt
 ---> Running in 1234567890ab
ERROR: Could not find a version that satisfies the requirement package-name==1.0.0
```

Solution: Update the package version to one that is available in PyPI.

### Kubernetes Deployment Fails

**Issue**: Kubernetes deployment fails with errors.

**Solutions**:

1. **Check Deployment Configuration**: Ensure that the deployment configuration is correct.

2. **Check Kubernetes Cluster**: Ensure that the Kubernetes cluster is available and correctly configured.

3. **Check Service Dependencies**: Ensure that all service dependencies are available.

Example error:

```
Error from server (BadRequest): error when creating "k8s/dev/deployment.yaml": Deployment.apps "my-service" is invalid: spec.template.spec.containers[0].image: Invalid value: "berrys/my-service:latest": tag "latest" not found
```

Solution: Ensure that the Docker image exists in the registry with the specified tag.

### Database Migration Fails

**Issue**: Database migration fails with errors.

**Solutions**:

1. **Check Migration Scripts**: Ensure that the migration scripts are correct and up to date.

2. **Check Database Connection**: Ensure that the database is available and correctly configured.

3. **Check Database State**: Ensure that the database is in the expected state for the migration.

Example error:

```
Error: Can't locate revision identified by '1234567890ab'
```

Solution: Ensure that the migration history is consistent across environments.

### Deployment Verification Fails

**Issue**: Deployment verification fails with errors.

**Solutions**:

1. **Check Service Health**: Ensure that the service is running and healthy.

2. **Check Health Endpoint**: Ensure that the health endpoint is implemented correctly.

3. **Check Service URL**: Ensure that the service URL is correct and accessible.

Example error:

```
Health check failed with status code 500
```

Solution: Fix the service issue causing the health check to fail.

## GitHub Actions Issues

### Workflow Syntax Errors

**Issue**: Workflow file has syntax errors.

**Solutions**:

1. **Check YAML Syntax**: Ensure that the YAML syntax is correct.

2. **Check Workflow Syntax**: Ensure that the workflow syntax follows the GitHub Actions schema.

3. **Validate Workflow File**: Use a YAML validator to check the workflow file.

Example error:

```
Error: Workflow is not valid. .github/workflows/my-service.yml: Unexpected value 'invalid_key'
```

Solution: Fix the syntax error in the workflow file.

### Workflow Permission Issues

**Issue**: Workflow fails due to permission issues.

**Solutions**:

1. **Check Repository Permissions**: Ensure that the workflow has the necessary permissions to access the repository.

2. **Check Secret Access**: Ensure that the workflow has access to the necessary secrets.

3. **Check Token Permissions**: Ensure that the GitHub token has the necessary permissions.

Example error:

```
Error: Resource not accessible by integration
```

Solution: Configure the necessary permissions in the repository settings.

### Workflow Resource Limits

**Issue**: Workflow fails due to resource limits.

**Solutions**:

1. **Check Job Duration**: Ensure that jobs do not exceed the maximum duration.

2. **Check Workflow Usage**: Ensure that the workflow does not exceed the usage limits.

3. **Optimize Workflow**: Optimize the workflow to use fewer resources.

Example error:

```
Error: Job was cancelled because it reached the maximum execution time of 360 minutes
```

Solution: Optimize the job to complete within the time limit or split it into smaller jobs.

## Getting Help

If you encounter issues that are not covered in this guide, you can:

1. **Check GitHub Actions Documentation**: Refer to the [GitHub Actions documentation](https://docs.github.com/en/actions) for general information about GitHub Actions.

2. **Check Tool Documentation**: Refer to the documentation for the specific tools used in the pipeline.

3. **Search Issue Tracker**: Search the issue tracker for similar issues and solutions.

4. **Contact DevOps Team**: Contact the DevOps team for assistance with pipeline issues.

5. **Create Issue**: Create an issue in the issue tracker with a detailed description of the problem, including error messages and steps to reproduce.
