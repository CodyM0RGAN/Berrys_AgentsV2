# Deployment Guide

This guide provides detailed information about the deployment process for the Berrys_AgentsV2 system. It explains how services are deployed to different environments, how deployments are verified, and how to troubleshoot deployment issues.

## Table of Contents

- [Overview](#overview)
- [Deployment Environments](#deployment-environments)
- [Deployment Process](#deployment-process)
- [Deployment Configuration](#deployment-configuration)
- [Deployment Verification](#deployment-verification)
- [Rollback Mechanism](#rollback-mechanism)
- [Manual Deployments](#manual-deployments)
- [Troubleshooting](#troubleshooting)

## Overview

The Berrys_AgentsV2 system uses a continuous deployment approach, where code changes are automatically deployed to development environments after passing quality gates. Deployments to higher environments (QA, production) follow a promotion path and may require manual approval.

The deployment process is implemented using GitHub Actions and Kubernetes. It includes:

1. **Building and pushing Docker images**
2. **Updating Kubernetes configurations**
3. **Running database migrations**
4. **Deploying to Kubernetes**
5. **Verifying deployments**
6. **Rolling back failed deployments**

## Deployment Environments

The system supports the following deployment environments:

### Development (dev)

- **Purpose**: Testing new features and bug fixes
- **Deployment Trigger**: Automatic on merge to main branch or manual
- **Data**: Development data, may be reset periodically
- **URL**: https://dev-api.berrys.ai

### Quality Assurance (qa)

- **Purpose**: Testing integration and user acceptance
- **Deployment Trigger**: Automatic after successful dev deployment or manual
- **Data**: Stable test data, not reset frequently
- **URL**: https://qa-api.berrys.ai

### Production (prod)

- **Purpose**: Serving real users
- **Deployment Trigger**: Manual only
- **Data**: Production data, never reset
- **URL**: https://api.berrys.ai

## Deployment Process

The deployment process follows these steps:

### 1. Build and Push Docker Image

The service code is built into a Docker image and pushed to the Docker registry:

```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v4
  with:
    context: ${{ inputs.working_directory }}
    push: true
    tags: ${{ inputs.docker_image }}:${{ inputs.docker_tag }},${{ inputs.docker_image }}:${{ inputs.environment }}
    cache-from: type=registry,ref=${{ inputs.docker_image }}:buildcache
    cache-to: type=registry,ref=${{ inputs.docker_image }}:buildcache,mode=max
```

### 2. Update Deployment Configuration

The Kubernetes deployment configuration is updated with the new image tag and environment-specific settings:

```yaml
- name: Update deployment configuration
  run: |
    echo "Updating deployment configuration for ${{ inputs.service_name }} in ${{ inputs.environment }}..."
    
    # Create deployment directory if it doesn't exist
    mkdir -p k8s/${{ inputs.environment }}
    
    # Create or update deployment.yaml
    cat > k8s/${{ inputs.environment }}/deployment.yaml << EOF
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: ${{ inputs.service_name }}
      namespace: berrys-${{ inputs.environment }}
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: ${{ inputs.service_name }}
      template:
        metadata:
          labels:
            app: ${{ inputs.service_name }}
        spec:
          containers:
          - name: ${{ inputs.service_name }}
            image: ${{ inputs.docker_image }}:${{ inputs.docker_tag }}
            ports:
            - containerPort: 8000
            env:
            - name: ENVIRONMENT
              value: ${{ inputs.environment }}
    EOF
    
    # Create or update service.yaml
    cat > k8s/${{ inputs.environment }}/service.yaml << EOF
    apiVersion: v1
    kind: Service
    metadata:
      name: ${{ inputs.service_name }}
      namespace: berrys-${{ inputs.environment }}
    spec:
      selector:
        app: ${{ inputs.service_name }}
      ports:
      - port: 80
        targetPort: 8000
      type: ClusterIP
    EOF
```

### 3. Run Database Migrations

If the service has database migrations, they are run before deploying the new version:

```yaml
- name: Run database migrations
  if: ${{ inputs.run_migrations }}
  run: |
    echo "Running database migrations for ${{ inputs.service_name }} in ${{ inputs.environment }}..."
    
    # Create migration job
    cat > k8s/${{ inputs.environment }}/migration-job.yaml << EOF
    apiVersion: batch/v1
    kind: Job
    metadata:
      name: ${{ inputs.service_name }}-migration-${{ github.run_id }}
      namespace: berrys-${{ inputs.environment }}
    spec:
      template:
        spec:
          containers:
          - name: migration
            image: ${{ inputs.docker_image }}:${{ inputs.docker_tag }}
            command: ["alembic", "upgrade", "head"]
            env:
            - name: ENVIRONMENT
              value: ${{ inputs.environment }}
          restartPolicy: Never
      backoffLimit: 3
    EOF
    
    # Apply migration job
    kubectl apply -f k8s/${{ inputs.environment }}/migration-job.yaml --kubeconfig=kubeconfig.yaml
    
    # Wait for migration job to complete
    kubectl wait --for=condition=complete job/${{ inputs.service_name }}-migration-${{ github.run_id }} --namespace=berrys-${{ inputs.environment }} --timeout=${{ inputs.deploy_timeout }}s --kubeconfig=kubeconfig.yaml
```

### 4. Deploy to Kubernetes

The service is deployed to Kubernetes using the updated configuration:

```yaml
- name: Deploy to Kubernetes
  id: deploy
  run: |
    echo "Deploying ${{ inputs.service_name }} to ${{ inputs.environment }}..."
    
    # Apply deployment and service
    kubectl apply -f k8s/${{ inputs.environment }}/deployment.yaml --kubeconfig=kubeconfig.yaml
    kubectl apply -f k8s/${{ inputs.environment }}/service.yaml --kubeconfig=kubeconfig.yaml
    
    # Wait for deployment to be ready
    kubectl rollout status deployment/${{ inputs.service_name }} --namespace=berrys-${{ inputs.environment }} --timeout=${{ inputs.deploy_timeout }}s --kubeconfig=kubeconfig.yaml
```

### 5. Verify Deployment

After deployment, the service is verified to ensure it is running correctly:

```yaml
- name: Verify deployment
  id: verify
  if: steps.deploy.outcome == 'success'
  run: |
    echo "Verifying deployment of ${{ inputs.service_name }} to ${{ inputs.environment }}..."
    
    # Get service URL
    SERVICE_URL="${{ steps.deploy.outputs.service_url }}"
    
    # Check if service is responding
    MAX_RETRIES=10
    RETRY_INTERVAL=5
    
    for i in $(seq 1 $MAX_RETRIES); do
      echo "Attempt $i of $MAX_RETRIES..."
      if curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health" | grep -q "200"; then
        echo "Service is responding!"
        echo "verify_success=true" >> $GITHUB_OUTPUT
        break
      else
        echo "Service is not responding yet. Waiting $RETRY_INTERVAL seconds..."
        sleep $RETRY_INTERVAL
      fi
      
      if [ $i -eq $MAX_RETRIES ]; then
        echo "Service failed to respond after $MAX_RETRIES attempts."
        echo "verify_success=false" >> $GITHUB_OUTPUT
      fi
    done
```

### 6. Rollback on Failure

If the deployment fails, it is automatically rolled back to the previous version:

```yaml
- name: Rollback deployment on failure
  if: failure() && steps.deploy.outcome == 'success'
  run: |
    echo "Rolling back deployment of ${{ inputs.service_name }} in ${{ inputs.environment }}..."
    
    # Rollback to previous revision
    kubectl rollout undo deployment/${{ inputs.service_name }} --namespace=berrys-${{ inputs.environment }} --kubeconfig=kubeconfig.yaml
    
    # Wait for rollback to complete
    kubectl rollout status deployment/${{ inputs.service_name }} --namespace=berrys-${{ inputs.environment }} --timeout=60s --kubeconfig=kubeconfig.yaml
```

## Deployment Configuration

The deployment configuration is defined in the service-specific workflow file. It includes:

### Environment Variables

```yaml
env:
  SERVICE_NAME: tool-integration
  WORKING_DIRECTORY: services/tool-integration
  PYTHON_VERSION: '3.10'
```

### Deployment Jobs

```yaml
deploy-dev:
  name: Deploy to Dev
  needs: [test, quality]
  if: |
    (github.event_name == 'push' && github.ref == 'refs/heads/main') ||
    (github.event_name == 'workflow_dispatch' && github.event.inputs.deploy_environment == 'dev')
  uses: ./.github/workflows/templates/deploy.yml
  with:
    service_name: ${{ env.SERVICE_NAME }}
    environment: dev
    working_directory: ${{ env.WORKING_DIRECTORY }}
    docker_image: berrys/${{ env.SERVICE_NAME }}
    docker_tag: ${{ github.sha }}
    deploy_timeout: 300
    run_migrations: true
  secrets: inherit
```

### Deployment Parameters

The deployment template accepts the following parameters:

- **service_name**: Name of the service to deploy
- **environment**: Environment to deploy to (dev, qa, prod)
- **working_directory**: Directory containing the service code
- **docker_image**: Docker image name
- **docker_tag**: Docker image tag
- **deploy_timeout**: Deployment timeout in seconds
- **run_migrations**: Whether to run database migrations

## Deployment Verification

After deployment, the service is verified to ensure it is running correctly. The verification process includes:

1. **Health Check**: Checking the service's health endpoint
2. **Verification Report**: Generating a verification report

The verification is performed by the deployment-verifier.py script, which:

1. Sends requests to the service's health endpoint
2. Checks the response status code
3. Generates a verification report

Example verification command:

```bash
python .github/scripts/ci/deployment-verifier.py \
  --service-url https://api.berrys.ai/my-service \
  --health-endpoint /health \
  --timeout 300 \
  --interval 5 \
  --output-file deployment-verification.json \
  --headers '{"Authorization": "Bearer token"}'
```

## Rollback Mechanism

If a deployment fails, it is automatically rolled back to the previous version. The rollback process includes:

1. **Rollback Command**: Running the `kubectl rollout undo` command
2. **Rollback Verification**: Waiting for the rollback to complete
3. **Rollback Notification**: Notifying the team of the rollback

Example rollback command:

```bash
kubectl rollout undo deployment/my-service --namespace=berrys-dev
```

## Manual Deployments

In addition to automated deployments, you can also trigger manual deployments using the GitHub Actions workflow dispatch feature. This is useful for:

1. **Deploying to specific environments**: Deploying to QA or production environments
2. **Deploying specific versions**: Deploying a specific version of the service
3. **Testing deployments**: Testing the deployment process

To trigger a manual deployment:

1. Go to the GitHub repository
2. Click on the "Actions" tab
3. Select the service workflow (e.g., "Tool Integration CI/CD")
4. Click on "Run workflow"
5. Select the branch to deploy
6. Select the environment to deploy to
7. Click on "Run workflow"

## Troubleshooting

### Common Issues

#### Deployment Fails with "ImagePullBackOff" Error

This error occurs when Kubernetes cannot pull the Docker image. To fix this:

1. Check that the Docker image exists in the registry
2. Check that the image tag is correct
3. Check that the Kubernetes cluster has access to the Docker registry
4. Check that the image name and tag in the deployment configuration match the image in the registry

#### Deployment Fails with "CrashLoopBackOff" Error

This error occurs when the service container crashes repeatedly. To fix this:

1. Check the container logs for error messages
2. Check that the service configuration is correct
3. Check that the service dependencies are available
4. Check that the service has the necessary permissions

#### Deployment Fails with "Timeout" Error

This error occurs when the deployment takes too long to complete. To fix this:

1. Check that the service is starting correctly
2. Check that the service dependencies are available
3. Check that the service is not stuck in a loop
4. Increase the deployment timeout

#### Deployment Verification Fails

This error occurs when the service is deployed but does not respond to health checks. To fix this:

1. Check that the service is running
2. Check that the health endpoint is implemented correctly
3. Check that the service is accessible from the verification script
4. Check that the service is not returning errors

### Deployment Logs

To view deployment logs, you can:

1. **GitHub Actions Logs**: View the logs in the GitHub Actions workflow
2. **Kubernetes Logs**: View the logs in the Kubernetes cluster
3. **Verification Reports**: View the verification reports in the GitHub Actions artifacts

Example Kubernetes log command:

```bash
kubectl logs deployment/my-service --namespace=berrys-dev
```

### Deployment Status

To check the deployment status, you can:

1. **GitHub Actions Status**: Check the status in the GitHub Actions workflow
2. **Kubernetes Status**: Check the status in the Kubernetes cluster
3. **Service Health**: Check the service health endpoint

Example Kubernetes status command:

```bash
kubectl get deployment my-service --namespace=berrys-dev
```

### Manual Rollback

If you need to manually roll back a deployment, you can:

1. **Use the Kubernetes CLI**: Run the `kubectl rollout undo` command
2. **Deploy a Previous Version**: Manually deploy a previous version of the service
3. **Revert the Code Change**: Revert the code change and trigger a new deployment

Example manual rollback command:

```bash
kubectl rollout undo deployment/my-service --namespace=berrys-dev
```
