/**
 * # Production Environment Infrastructure
 *
 * This file defines the production environment infrastructure using Terraform.
 */

terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.65.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10.0"
    }
    vault = {
      source  = "hashicorp/vault"
      version = "~> 3.18.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "berrys-terraform-state"
    storage_account_name = "berrystfstate"
    container_name       = "terraformstate"
    key                  = "production.tfstate"
  }
}

provider "azurerm" {
  features {}
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig_path
  }
}

provider "vault" {
  address = var.vault_address
}

# Use the Kubernetes module to configure the production environment
module "kubernetes" {
  source = "../modules/kubernetes"

  environments     = ["production"]
  kubeconfig_path  = var.kubeconfig_path
  docker_username  = var.docker_username
  docker_password  = var.docker_password
  docker_email     = var.docker_email
  resource_quotas  = var.resource_quotas
  environment_configs = var.environment_configs
}

# Deploy monitoring stack with Prometheus and Grafana
resource "helm_release" "prometheus" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = module.kubernetes.namespace_names["production"]
  version    = "45.1.1"

  values = [
    file("${path.module}/prometheus-values.yaml")
  ]
}

# Deploy Istio service mesh for canary deployments and blue/green
resource "helm_release" "istio_base" {
  name       = "istio-base"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "base"
  namespace  = "istio-system"
  version    = "1.17.2"

  create_namespace = true
}

resource "helm_release" "istiod" {
  name       = "istiod"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "istiod"
  namespace  = "istio-system"
  version    = "1.17.2"

  depends_on = [helm_release.istio_base]
}

resource "helm_release" "istio_ingress" {
  name       = "istio-ingress"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "gateway"
  namespace  = "istio-system"
  version    = "1.17.2"

  depends_on = [helm_release.istiod]
}

# Deploy cert-manager for SSL certificate management
resource "helm_release" "cert_manager" {
  name       = "cert-manager"
  repository = "https://charts.jetstack.io"
  chart      = "cert-manager"
  namespace  = "cert-manager"
  version    = "v1.11.1"

  create_namespace = true

  set {
    name  = "installCRDs"
    value = "true"
  }
}

# Production cluster issuer for Let's Encrypt
resource "kubernetes_manifest" "cluster_issuer" {
  manifest = {
    apiVersion = "cert-manager.io/v1"
    kind       = "ClusterIssuer"
    metadata = {
      name = "letsencrypt-prod"
    }
    spec = {
      acme = {
        server = "https://acme-v02.api.letsencrypt.org/directory"
        email  = var.letsencrypt_email
        privateKeySecretRef = {
          name = "letsencrypt-prod"
        }
        solvers = [
          {
            http01 = {
              ingress = {
                class = "istio"
              }
            }
          }
        ]
      }
    }
  }

  depends_on = [helm_release.cert_manager]
}

# Deploy external DNS for automatic DNS configuration
resource "helm_release" "external_dns" {
  name       = "external-dns"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "external-dns"
  namespace  = "kube-system"
  version    = "6.13.1"

  values = [
    file("${path.module}/external-dns-values.yaml")
  ]
}

# Deploy NetworkPolicy controller for enhanced security
resource "helm_release" "calico" {
  name       = "calico"
  repository = "https://docs.projectcalico.org/charts"
  chart      = "tigera-operator"
  namespace  = "kube-system"
  version    = "v3.25.1"
}

# Azure Key Vault integration for secret management
resource "azurerm_key_vault" "berrys_kv" {
  name                = "berrys-kv-prod"
  resource_group_name = var.resource_group_name
  location            = var.location
  tenant_id           = var.tenant_id
  sku_name            = "standard"

  access_policy {
    tenant_id = var.tenant_id
    object_id = var.service_principal_object_id

    key_permissions = [
      "Get", "List", "Create", "Delete", "Update", "Recover", "Backup", "Restore"
    ]

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Recover", "Backup", "Restore"
    ]

    certificate_permissions = [
      "Get", "List", "Create", "Delete", "Update", "Recover", "Backup", "Restore"
    ]
  }

  tags = {
    environment = "production"
    managed-by  = "terraform"
    project     = "berrys-agents"
  }
}

# Deploy sealed-secrets for Kubernetes secret encryption
resource "helm_release" "sealed_secrets" {
  name       = "sealed-secrets"
  repository = "https://bitnami-labs.github.io/sealed-secrets"
  chart      = "sealed-secrets"
  namespace  = "kube-system"
  version    = "2.7.3"
}

# Deploy HashiCorp Vault for secret management
resource "helm_release" "vault" {
  name       = "vault"
  repository = "https://helm.releases.hashicorp.com"
  chart      = "vault"
  namespace  = "vault"
  version    = "0.23.0"

  create_namespace = true

  values = [
    file("${path.module}/vault-values.yaml")
  ]
}

# Create vault policy for services
resource "vault_policy" "services" {
  name = "berrys-services"

  policy = <<EOT
# Allow services to read their own secrets
path "secret/production/{{identity.entity.aliases.auth_kubernetes_berrys_production.metadata.service_account_name}}" {
  capabilities = ["read"]
}

# Allow services to read common secrets
path "secret/production/common" {
  capabilities = ["read"]
}
EOT

  depends_on = [helm_release.vault]
}

# Create kubernetes auth backend for Vault
resource "vault_auth_backend" "kubernetes" {
  type = "kubernetes"
  path = "kubernetes/berrys-production"

  depends_on = [helm_release.vault]
}

# Configure kubernetes auth backend
resource "vault_kubernetes_auth_backend_config" "kubernetes" {
  backend                = vault_auth_backend.kubernetes.path
  kubernetes_host        = var.kubernetes_host
  kubernetes_ca_cert     = var.kubernetes_ca_cert
  token_reviewer_jwt     = var.token_reviewer_jwt
  disable_iss_validation = "true"

  depends_on = [vault_auth_backend.kubernetes]
}
