/**
 * # Kubernetes Cluster Module
 *
 * This module provisions a Kubernetes cluster with all necessary resources for the Berrys_AgentsV2 platform.
 */

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

resource "kubernetes_namespace" "berrys" {
  for_each = toset(var.environments)

  metadata {
    name = "berrys-${each.key}"
    labels = {
      environment = each.key
      managed-by  = "terraform"
      project     = "berrys-agents"
    }
  }
}

# Network policies to enforce service isolation
resource "kubernetes_network_policy" "namespace_isolation" {
  for_each = toset(var.environments)

  metadata {
    name      = "namespace-isolation"
    namespace = kubernetes_namespace.berrys[each.key].metadata[0].name
  }

  spec {
    pod_selector {}

    ingress {
      from {
        namespace_selector {
          match_labels = {
            environment = each.key
          }
        }
      }
    }

    policy_types = ["Ingress"]
  }
}

# Resource quotas for each namespace
resource "kubernetes_resource_quota" "namespace_quota" {
  for_each = toset(var.environments)

  metadata {
    name      = "namespace-quota"
    namespace = kubernetes_namespace.berrys[each.key].metadata[0].name
  }

  spec {
    hard = {
      "requests.cpu"    = lookup(var.resource_quotas, "${each.key}_cpu_request", "10")
      "requests.memory" = lookup(var.resource_quotas, "${each.key}_memory_request", "20Gi")
      "limits.cpu"      = lookup(var.resource_quotas, "${each.key}_cpu_limit", "20")
      "limits.memory"   = lookup(var.resource_quotas, "${each.key}_memory_limit", "40Gi")
      "pods"            = "100"
      "services"        = "50"
    }
  }
}

# Default resource limits for pods in each namespace
resource "kubernetes_limit_range" "default_limits" {
  for_each = toset(var.environments)

  metadata {
    name      = "default-limits"
    namespace = kubernetes_namespace.berrys[each.key].metadata[0].name
  }

  spec {
    limit {
      type = "Container"
      default = {
        cpu    = "100m"
        memory = "256Mi"
      }
      default_request = {
        cpu    = "50m"
        memory = "128Mi"
      }
    }
  }
}

# Secret for Docker registry authentication
resource "kubernetes_secret" "docker_registry" {
  for_each = toset(var.environments)

  metadata {
    name      = "docker-registry"
    namespace = kubernetes_namespace.berrys[each.key].metadata[0].name
  }

  type = "kubernetes.io/dockerconfigjson"

  data = {
    ".dockerconfigjson" = jsonencode({
      auths = {
        "https://index.docker.io/v1/" = {
          username = var.docker_username
          password = var.docker_password
          email    = var.docker_email
          auth     = base64encode("${var.docker_username}:${var.docker_password}")
        }
      }
    })
  }
}

# Storage classes for different types of persistence
resource "kubernetes_storage_class" "standard" {
  metadata {
    name = "berrys-standard"
  }

  storage_provisioner = "kubernetes.io/azure-disk"
  reclaim_policy      = "Retain"
  parameters = {
    storageaccounttype = "Standard_LRS"
    kind               = "Managed"
  }
}

resource "kubernetes_storage_class" "fast" {
  metadata {
    name = "berrys-fast"
  }

  storage_provisioner = "kubernetes.io/azure-disk"
  reclaim_policy      = "Retain"
  parameters = {
    storageaccounttype = "Premium_LRS"
    kind               = "Managed"
  }
}

# Role-based access control for CI/CD
resource "kubernetes_cluster_role" "ci_cd_role" {
  metadata {
    name = "berrys-ci-cd-role"
  }

  rule {
    api_groups = ["", "apps", "batch", "extensions"]
    resources  = ["deployments", "services", "pods", "jobs", "cronjobs", "configmaps", "secrets"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }
}

resource "kubernetes_cluster_role_binding" "ci_cd_binding" {
  metadata {
    name = "berrys-ci-cd-binding"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.ci_cd_role.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = "berrys-ci-cd"
    namespace = "kube-system"
  }
}

resource "kubernetes_service_account" "ci_cd" {
  metadata {
    name      = "berrys-ci-cd"
    namespace = "kube-system"
  }
}

# Create ConfigMaps for environment-specific configurations
resource "kubernetes_config_map" "environment_config" {
  for_each = toset(var.environments)

  metadata {
    name      = "environment-config"
    namespace = kubernetes_namespace.berrys[each.key].metadata[0].name
  }

  data = {
    "ENVIRONMENT"             = each.key
    "LOG_LEVEL"               = lookup(var.environment_configs, "${each.key}_log_level", "INFO")
    "METRICS_ENABLED"         = "true"
    "TRACING_ENABLED"         = lookup(var.environment_configs, "${each.key}_tracing_enabled", "true")
    "DATABASE_HOST"           = lookup(var.environment_configs, "${each.key}_database_host", "postgres-${each.key}")
    "REDIS_HOST"              = lookup(var.environment_configs, "${each.key}_redis_host", "redis-${each.key}")
    "MONGODB_HOST"            = lookup(var.environment_configs, "${each.key}_mongodb_host", "mongodb-${each.key}")
    "MAX_WORKER_CONNECTIONS"  = lookup(var.environment_configs, "${each.key}_max_worker_connections", "1000")
    "PROMETHEUS_SCRAPE_PATH"  = "/metrics"
    "HEALTH_CHECK_PATH"       = "/health"
  }
}
