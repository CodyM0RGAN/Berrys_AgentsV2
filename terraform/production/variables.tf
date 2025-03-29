/**
 * # Production Environment Variables
 *
 * This file defines the variables for the production environment.
 */

variable "kubeconfig_path" {
  description = "Path to the kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

variable "resource_group_name" {
  description = "Azure resource group name"
  type        = string
  default     = "berrys-production"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus2"
}

variable "tenant_id" {
  description = "Azure tenant ID"
  type        = string
  sensitive   = true
}

variable "service_principal_object_id" {
  description = "Service principal object ID"
  type        = string
  sensitive   = true
}

variable "docker_username" {
  description = "Docker registry username"
  type        = string
  sensitive   = true
}

variable "docker_password" {
  description = "Docker registry password"
  type        = string
  sensitive   = true
}

variable "docker_email" {
  description = "Docker registry email"
  type        = string
  sensitive   = true
}

variable "letsencrypt_email" {
  description = "Email address for Let's Encrypt notifications"
  type        = string
  default     = "devops@berrys.ai"
}

variable "resource_quotas" {
  description = "Resource quotas for production environment"
  type        = map(string)
  default = {
    production_cpu_request    = "16"
    production_memory_request = "32Gi"
    production_cpu_limit      = "32"
    production_memory_limit   = "64Gi"
  }
}

variable "environment_configs" {
  description = "Production environment-specific configuration values"
  type        = map(string)
  default = {
    production_log_level              = "INFO"
    production_tracing_enabled        = "true"
    production_max_worker_connections = "1500"
    production_database_host          = "postgres-production.database.azure.com"
    production_redis_host             = "redis-production.redis.cache.windows.net"
    production_mongodb_host           = "mongodb-production.documents.azure.com"
  }
}

variable "vault_address" {
  description = "Address of the HashiCorp Vault server"
  type        = string
  default     = "https://vault.berrys.ai"
}

variable "kubernetes_host" {
  description = "Kubernetes API server host"
  type        = string
  sensitive   = true
}

variable "kubernetes_ca_cert" {
  description = "Kubernetes CA certificate"
  type        = string
  sensitive   = true
}

variable "token_reviewer_jwt" {
  description = "JWT token for the service account to be used by Vault to validate service account tokens"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Base domain name for all services"
  type        = string
  default     = "berrys.ai"
}

variable "ssl_min_protocol_version" {
  description = "Minimum TLS protocol version"
  type        = string
  default     = "TLS1_2"
}

variable "network_acls" {
  description = "Network ACLs for the Key Vault"
  type = object({
    default_action = string
    bypass         = string
    ip_rules       = list(string)
  })
  default = {
    default_action = "Deny"
    bypass         = "AzureServices"
    ip_rules       = ["0.0.0.0/0"] # This should be restricted to actual IPs in production
  }
}

variable "backup_enabled" {
  description = "Whether to enable backup for resources"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

variable "alert_email_addresses" {
  description = "Email addresses to receive alerts"
  type        = list(string)
  default     = ["alerts@berrys.ai", "devops@berrys.ai"]
}

variable "metric_alerts" {
  description = "Map of metric alerts to create"
  type = map(object({
    metric_name        = string
    operator           = string
    threshold          = number
    aggregation        = string
    window_size        = string
    evaluation_frequency = string
    severity           = number
  }))
  default = {
    high_cpu = {
      metric_name        = "CpuPercentage"
      operator           = "GreaterThan"
      threshold          = 80
      aggregation        = "Average"
      window_size        = "PT5M"
      evaluation_frequency = "PT1M"
      severity           = 2
    },
    high_memory = {
      metric_name        = "MemoryPercentage"
      operator           = "GreaterThan"
      threshold          = 80
      aggregation        = "Average"
      window_size        = "PT5M"
      evaluation_frequency = "PT1M"
      severity           = 2
    },
    high_error_rate = {
      metric_name        = "Http5xx"
      operator           = "GreaterThan"
      threshold          = 5
      aggregation        = "Count"
      window_size        = "PT5M"
      evaluation_frequency = "PT1M"
      severity           = 1
    }
  }
}
