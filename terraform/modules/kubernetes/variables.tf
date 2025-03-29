/**
 * # Kubernetes Module Variables
 *
 * This file defines the variables for the Kubernetes module.
 */

variable "kubeconfig_path" {
  description = "Path to the kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

variable "environments" {
  description = "List of environments to create namespaces for"
  type        = list(string)
  default     = ["development", "staging", "production"]
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

variable "resource_quotas" {
  description = "Resource quotas for each environment"
  type        = map(string)
  default = {
    development_cpu_request    = "4"
    development_memory_request = "8Gi"
    development_cpu_limit      = "8"
    development_memory_limit   = "16Gi"
    
    staging_cpu_request    = "8"
    staging_memory_request = "16Gi"
    staging_cpu_limit      = "16"
    staging_memory_limit   = "32Gi"
    
    production_cpu_request    = "12"
    production_memory_request = "24Gi"
    production_cpu_limit      = "24"
    production_memory_limit   = "48Gi"
  }
}

variable "environment_configs" {
  description = "Environment-specific configuration values"
  type        = map(string)
  default = {
    development_log_level              = "DEBUG"
    development_tracing_enabled        = "true"
    development_max_worker_connections = "500"
    
    staging_log_level              = "INFO"
    staging_tracing_enabled        = "true" 
    staging_max_worker_connections = "750"
    
    production_log_level              = "INFO"
    production_tracing_enabled        = "true"
    production_max_worker_connections = "1000"
  }
}
