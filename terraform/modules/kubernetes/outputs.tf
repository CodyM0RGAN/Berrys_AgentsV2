/**
 * # Kubernetes Module Outputs
 *
 * This file defines the outputs for the Kubernetes module.
 */

output "namespace_names" {
  description = "Names of the created Kubernetes namespaces"
  value       = { for env, ns in kubernetes_namespace.berrys : env => ns.metadata[0].name }
}

output "service_account_name" {
  description = "Name of the CI/CD service account"
  value       = kubernetes_service_account.ci_cd.metadata[0].name
}

output "storage_class_standard" {
  description = "Name of the standard storage class"
  value       = kubernetes_storage_class.standard.metadata[0].name
}

output "storage_class_fast" {
  description = "Name of the fast storage class"
  value       = kubernetes_storage_class.fast.metadata[0].name
}

output "config_maps" {
  description = "Map of environment config maps"
  value       = { for env, cm in kubernetes_config_map.environment_config : env => cm.metadata[0].name }
}
