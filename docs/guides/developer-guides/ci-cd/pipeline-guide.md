# CI/CD Pipeline Guide

This guide provides an overview of the CI/CD pipeline for the Berrys_AgentsV2 system. It explains how the pipeline is structured, how it works, and how to use it effectively.

## Table of Contents

- [Overview](#overview)
- [Pipeline Structure](#pipeline-structure)
- [Workflow Templates](#workflow-templates)
- [Service Workflows](#service-workflows)
- [Main Workflow](#main-workflow)
- [Pipeline Stages](#pipeline-stages)
- [Pipeline Scripts](#pipeline-scripts)
- [Using the Pipeline](#using-the-pipeline)
- [Customizing the Pipeline](#customizing-the-pipeline)
- [Best Practices](#best-practices)

## Overview

The Berrys_AgentsV2 CI/CD pipeline is implemented using GitHub Actions. It provides automated building, testing, quality checking, and deployment of services to different environments. The pipeline is designed to be:

- **Modular**: Each service has its own workflow file that inherits from common templates.
- **Standardized**: All services follow the same pipeline structure and quality standards.
- **Flexible**: Services can customize the pipeline to meet their specific needs.
- **Efficient**: The pipeline uses caching and parallelization to minimize execution time.
- **Reliable**: The pipeline includes comprehensive error handling and reporting.

## Pipeline Structure

The pipeline is organized as follows:

```
.github/
  workflows/
    templates/
      build.yml       # Template for building services
      test.yml        # Template for testing services
      quality.yml     # Template for quality checking services
      deploy.yml      # Template for deploying services
    main.yml          # Main workflow that triggers service workflows
    service1.yml      # Workflow for service1
    service2.yml      # Workflow for service2
    ...
  scripts/
    ci/
      test-collector.py       # Script for collecting test results
      coverage-reporter.py    # Script for generating coverage reports
      quality-checker.py      # Script for checking code quality
      deployment-verifier.py  # Script for verifying deployments
```

## Workflow Templates

The pipeline uses workflow templates to standardize the build, test, quality, and deployment processes across all services. These templates are defined in the `.github/workflows/templates/` directory.

### Build Template

The build template (`build.yml`) is responsible for building a service. It:

1. Sets up the required Python version
2. Installs dependencies
3. Verifies imports
4. Builds the service
5. Caches build artifacts

### Test Template

The test template (`test.yml`) is responsible for testing a service. It:

1. Sets up the required Python version
2. Installs dependencies
3. Sets up the test environment
4. Runs tests with coverage
5. Processes test results
6. Uploads test artifacts

### Quality Template

The quality template (`quality.yml`) is responsible for checking the quality of a service. It:

1. Sets up the required Python version
2. Installs dependencies
3. Sets up the quality check environment
4. Runs linting tools (flake8, pylint, black, isort, mypy)
5. Runs security tools (bandit, safety)
6. Processes quality check results
7. Uploads quality check artifacts

### Deploy Template

The deploy template (`deploy.yml`) is responsible for deploying a service to an environment. It:

1. Builds and pushes a Docker image
2. Sets up kubectl
3. Updates deployment configuration
4. Runs database migrations (if needed)
5. Deploys to Kubernetes
6. Verifies the deployment
7. Rolls back the deployment if it fails

## Service Workflows

Each service has its own workflow file that uses the workflow templates. These workflow files are defined in the `.github/workflows/` directory. For example, the workflow file for the `tool-integration` service is defined in `.github/workflows/tool-integration.yml`.

A service workflow typically includes the following jobs:

1. **Build**: Builds the service
2. **Test**: Tests the service
3. **Quality**: Checks the quality of the service
4. **Report**: Generates reports from test and quality check results
5. **Deploy-Dev**: Deploys the service to the development environment
6. **Deploy-QA**: Deploys the service to the QA environment
7. **Deploy-Prod**: Deploys the service to the production environment
8. **Verify-Deployment**: Verifies that the deployment was successful

## Main Workflow

The main workflow (`main.yml`) is responsible for triggering the service workflows when changes are made to shared components or CI/CD configuration. It:

1. Triggers service workflows
2. Collects reports from service workflows
3. Generates consolidated reports

## Pipeline Stages

The pipeline consists of the following stages:

### 1. Build

The build stage is responsible for building the service. It:

- Installs dependencies
- Verifies imports
- Builds the service
- Caches build artifacts

### 2. Test

The test stage is responsible for testing the service. It:

- Sets up the test environment
- Runs tests with coverage
- Processes test results
- Uploads test artifacts

### 3. Quality

The quality stage is responsible for checking the quality of the service. It:

- Sets up the quality check environment
- Runs linting tools (flake8, pylint, black, isort, mypy)
- Runs security tools (bandit, safety)
- Processes quality check results
- Uploads quality check artifacts

### 4. Report

The report stage is responsible for generating reports from test and quality check results. It:

- Collects test results
- Collects quality check results
- Generates test reports
- Generates coverage reports
- Uploads reports

### 5. Deploy

The deploy stage is responsible for deploying the service to an environment. It:

- Builds and pushes a Docker image
- Updates deployment configuration
- Runs database migrations (if needed)
- Deploys to Kubernetes
- Verifies the deployment
- Rolls back the deployment if it fails

## Pipeline Scripts

The pipeline uses several scripts to process results and generate reports. These scripts are defined in the `.github/scripts/ci/` directory.

### Test Collector

The test collector script (`test-collector.py`) is responsible for collecting test results from multiple services and generating a consolidated report. It:

- Finds test result files
- Parses test results
- Generates a consolidated report in JSON, HTML, or Markdown format

### Coverage Reporter

The coverage reporter script (`coverage-reporter.py`) is responsible for collecting coverage results from multiple services and generating a consolidated report. It:

- Finds coverage result files
- Parses coverage results
- Generates a coverage chart
- Generates a consolidated report in JSON, HTML, or Markdown format

### Quality Checker

The quality checker script (`quality-checker.py`) is responsible for collecting quality check results from multiple services and generating a consolidated report. It:

- Finds quality check result files
- Parses quality check results
- Generates a consolidated report in JSON, HTML, or Markdown format

### Deployment Verifier

The deployment verifier script (`deployment-verifier.py`) is responsible for verifying that a deployed service is running correctly. It:

- Checks the health endpoint of the service
- Retries if the health check fails
- Generates a verification report

## Using the Pipeline

### Triggering the Pipeline

The pipeline is triggered automatically when:

- Changes are pushed to the `main` branch
- A pull request is opened or updated
- The workflow is manually triggered

### Viewing Pipeline Results

Pipeline results can be viewed in the GitHub Actions tab of the repository. This includes:

- Workflow runs
- Job logs
- Artifacts (test results, coverage reports, quality check reports)

### Manually Triggering the Pipeline

The pipeline can be manually triggered using the GitHub Actions UI. This is useful for:

- Deploying a specific version of a service
- Testing the pipeline without making changes
- Deploying to a specific environment

To manually trigger the pipeline:

1. Go to the GitHub Actions tab of the repository
2. Select the workflow to trigger
3. Click the "Run workflow" button
4. Select the branch to run the workflow on
5. Optionally, select the environment to deploy to
6. Click the "Run workflow" button

## Customizing the Pipeline

### Service-Specific Configuration

Services can customize the pipeline by providing service-specific configuration in their workflow file. This includes:

- Python version
- Coverage threshold
- Test parallelism
- Linting and security check configuration
- Deployment configuration

### Adding a New Service

To add a new service to the pipeline:

1. Create a new workflow file for the service in the `.github/workflows/` directory
2. Configure the workflow to use the workflow templates
3. Customize the workflow as needed

### Modifying the Pipeline

To modify the pipeline:

1. Update the workflow templates in the `.github/workflows/templates/` directory
2. Update the scripts in the `.github/scripts/ci/` directory
3. Update the main workflow in `.github/workflows/main.yml`

## Best Practices

### Code Quality

- Write tests for all code
- Maintain high code coverage
- Follow code style guidelines
- Fix linting and security issues promptly

### Pipeline Usage

- Run the pipeline locally before pushing changes
- Review pipeline results carefully
- Fix pipeline failures promptly
- Use the pipeline for all deployments

### Pipeline Maintenance

- Keep pipeline configuration up to date
- Monitor pipeline performance
- Optimize pipeline execution time
- Document pipeline changes
