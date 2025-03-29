#!/bin/bash
# Production Deployment Script for Berrys_AgentsV2
# This script executes the deployment steps for the Production Deployment and Scaling milestone

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Logging function
log() {
  echo -e "${GREEN}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
}

# Warning function
warn() {
  echo -e "${YELLOW}[WARN] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
}

# Error function
error() {
  echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
  exit 1
}

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
  error "kubectl is not installed. Please install kubectl before running this script."
fi

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
  error "terraform is not installed. Please install terraform before running this script."
fi

# Check for required environment variables
if [ -z "$DEPLOYMENT_ENV" ]; then
  warn "DEPLOYMENT_ENV not set. Defaulting to 'production'."
  export DEPLOYMENT_ENV="production"
fi

# Default values for auto-scaling and cloud features
if [ -z "$ENABLE_AUTOSCALING" ]; then
  warn "ENABLE_AUTOSCALING not set. Defaulting to 'false'."
  export ENABLE_AUTOSCALING="false"
fi

# Verify current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$TERRAFORM_DIR")")")"

log "Using project root: $PROJECT_ROOT"
log "Using Terraform directory: $TERRAFORM_DIR"
log "Auto-scaling enabled: $ENABLE_AUTOSCALING"

# Check if current user has necessary permissions
if [ "$DEPLOYMENT_ENV" == "production" ]; then
  if ! kubectl auth can-i create namespace --all-namespaces &> /dev/null; then
    error "Insufficient Kubernetes permissions. You need admin privileges to deploy to production."
  fi
fi

# Step 1: Initialize and apply Terraform configurations
deploy_infrastructure() {
  log "Step 1: Deploying infrastructure with Terraform"
  
  cd "$TERRAFORM_DIR"
  
  log "Initializing Terraform..."
  terraform init || error "Failed to initialize Terraform"
  
  log "Validating Terraform configurations..."
  terraform validate || error "Terraform validation failed"
  
  log "Planning Terraform deployment..."
  terraform plan -var="enable_autoscaling=${ENABLE_AUTOSCALING}" -out=tfplan || error "Terraform plan failed"
  
  log "Applying Terraform configurations..."
  terraform apply tfplan || error "Terraform apply failed"
  
  log "Infrastructure deployment completed successfully"
}

# Step 2: Set up Kubernetes namespace and resources
setup_kubernetes() {
  log "Step 2: Setting up Kubernetes resources"
  
  log "Checking if namespace exists..."
  if ! kubectl get namespace berrys-production &> /dev/null; then
    log "Creating namespace 'berrys-production'..."
    kubectl create namespace berrys-production || error "Failed to create namespace"
  else
    log "Namespace 'berrys-production' already exists."
  fi
  
  log "Applying base configurations..."
  kubectl apply -f "$TERRAFORM_DIR/base-configs.yaml" || error "Failed to apply base configurations"
  
  # Update the autoscaling-config configmap with the appropriate value
  log "Applying autoscaling ConfigMap..."
  sed "s/enable-autoscaling: \"false\"/enable-autoscaling: \"$ENABLE_AUTOSCALING\"/g" "$TERRAFORM_DIR/autoscaling-configs.yaml" | kubectl apply -f - || error "Failed to apply autoscaling configs"
  
  # Only apply the HPA resources if auto-scaling is enabled
  if [ "$ENABLE_AUTOSCALING" == "true" ]; then
    log "Auto-scaling is enabled, applying HPA resources..."
    kubectl apply -f "$TERRAFORM_DIR/autoscaling-configs.yaml" || error "Failed to apply autoscaling configs"
  else
    log "Auto-scaling is disabled, skipping HPA resources..."
  fi

  log "Creating ConfigMaps and Secrets..."
  # Apply Prometheus configuration
  kubectl apply -f "$TERRAFORM_DIR/prometheus-values.yaml" -n monitoring || warn "Failed to apply Prometheus configuration"
  
  log "Kubernetes resources setup completed successfully"
}

# Step 3: Deploy services in order
deploy_services() {
  log "Step 3: Deploying services"
  
  # Deploy shared libraries first
  log "Deploying shared libraries..."
  
  # Deploy database services
  log "Deploying database services..."
  
  # Deploy core services
  log "Deploying core services..."
  services=(
    "model-orchestration"
    "agent-orchestrator"
    "tool-integration"
    "planning-system"
    "project-coordinator"
    "api-gateway"
    "web-dashboard"
  )
  
  for service in "${services[@]}"; do
    log "Deploying $service..."
    # Check if GitHub CLI is available for deployment workflow
    if command -v gh &> /dev/null; then
      gh workflow run "$service-deploy.yml" -f environment=production -f deployment_strategy=blue-green -f enable_autoscaling=$ENABLE_AUTOSCALING || warn "Failed to trigger deployment workflow for $service"
    else
      # Fallback to kubectl for deployment
      if [ -f "$PROJECT_ROOT/services/$service/Dockerfile" ]; then
        # Use environment variables in the deployment
        cat "$TERRAFORM_DIR/manifests/$service.yaml" | \
        sed "s/ENABLE_AUTOSCALING/$ENABLE_AUTOSCALING/g" | \
        kubectl apply -f - -n berrys-production || warn "Failed to deploy $service"
      else
        warn "Deployment manifest for $service not found"
      fi
    fi
  done
  
  log "Services deployed successfully"
}

# Step 4: Apply database migrations
apply_database_migrations() {
  log "Step 4: Applying database migrations"
  
  services_with_migrations=(
    "agent-orchestrator"
    "model-orchestration"
    "project-coordinator"
    "service-integration"
    "tool-integration"
    "web-dashboard"
  )
  
  for service in "${services_with_migrations[@]}"; do
    log "Applying migrations for $service..."
    
    # Check if the service pod is running
    if kubectl get pods -n berrys-production | grep -q "$service"; then
      kubectl exec -it $(kubectl get pods -n berrys-production | grep "$service" | head -n 1 | awk '{print $1}') -n berrys-production -- alembic upgrade head || warn "Failed to apply migrations for $service"
    else
      warn "No pod found for $service, creating migration job..."
      
      # Create a job to run migrations
      cat << EOF | kubectl apply -f - -n berrys-production
apiVersion: batch/v1
kind: Job
metadata:
  name: $service-migration-$(date +%s)
  namespace: berrys-production
spec:
  template:
    spec:
      containers:
      - name: $service-migration
        image: berrys/$service:latest
        command: ["alembic", "upgrade", "head"]
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: ENABLE_AUTOSCALING
          value: "$ENABLE_AUTOSCALING"
      restartPolicy: Never
  backoffLimit: 2
EOF
    fi
  done
  
  log "Database migrations applied successfully"
}

# Step 5: Configure monitoring
setup_monitoring() {
  log "Step 5: Setting up monitoring"
  
  # Apply Grafana dashboards
  log "Applying Grafana dashboards..."
  kubectl create configmap grafana-dashboards --from-file="$TERRAFORM_DIR/grafana-dashboards/" -n monitoring --dry-run=client -o yaml | kubectl apply -f - || warn "Failed to apply Grafana dashboards"
  
  # Setup Prometheus adapter for custom metrics (only if auto-scaling is enabled)
  if [ "$ENABLE_AUTOSCALING" == "true" ]; then
    log "Auto-scaling is enabled, setting up Prometheus adapter for custom metrics..."
    kubectl apply -f "$TERRAFORM_DIR/prometheus-adapter.yaml" -n monitoring || warn "Failed to setup Prometheus adapter"
  else
    log "Auto-scaling is disabled, skipping Prometheus adapter setup..."
  fi
  
  # Set up alerts
  log "Setting up alerting rules..."
  kubectl apply -f "$TERRAFORM_DIR/alerting-rules.yaml" -n monitoring || warn "Failed to apply alerting rules"
  
  log "Monitoring setup completed successfully"
}

# Step 6: Verify deployment
verify_deployment() {
  log "Step 6: Verifying deployment"
  
  # Check all deployments
  log "Checking all deployments..."
  kubectl get deployments -n berrys-production
  
  # Check all services
  log "Checking all services..."
  kubectl get svc -n berrys-production
  
  # Check all pods
  log "Checking all pods..."
  kubectl get pods -n berrys-production
  
  # Check HPA resources (only if auto-scaling is enabled)
  if [ "$ENABLE_AUTOSCALING" == "true" ]; then
    log "Checking Horizontal Pod Autoscalers..."
    kubectl get hpa -n berrys-production
  else
    log "Auto-scaling is disabled, skipping HPA verification..."
  fi
  
  log "Deployment verification completed"
}

# Main deployment function
deploy() {
  log "Starting deployment process for environment: $DEPLOYMENT_ENV"
  log "Auto-scaling enabled: $ENABLE_AUTOSCALING"
  
  # Execute deployment steps
  deploy_infrastructure
  setup_kubernetes
  deploy_services
  apply_database_migrations
  setup_monitoring
  verify_deployment
  
  log "Deployment process completed successfully!"
  log "Please check the verify_deployment output above to confirm all resources are running as expected."
  
  if [ "$ENABLE_AUTOSCALING" == "false" ]; then
    log "Auto-scaling is disabled. To enable auto-scaling, set ENABLE_AUTOSCALING=true and rerun the deployment script."
    log "Note: Auto-scaling requires a Kubernetes cluster with the Metrics Server and Prometheus Adapter installed."
  fi
}

# Execute the main function
deploy
