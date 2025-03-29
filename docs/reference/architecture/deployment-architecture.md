# Deployment Architecture

**Last Modified:** 2025-03-29  
**Completion Date:** 2025-03-29  
**Doc Type:** Reference  

---

## Overview

This document describes the deployment architecture for the Berrys_AgentsV2 platform across various environments. It covers infrastructure components, configurations, and deployment patterns used to ensure scalability, reliability, and security.

## Deployment Environments

The platform supports multiple deployment environments with increasing levels of infrastructure resources and security controls:

```mermaid
graph TD
    A[Local Development] --> B[Development]
    B --> C[Staging]
    C --> D[Production]
    
    style A fill:#d0e0ff,stroke:#0066cc
    style B fill:#ffe0d0,stroke:#cc6600
    style C fill:#ffffd0,stroke:#cccc00
    style D fill:#d0ffd0,stroke:#00cc00
```

### Environment Characteristics

| Environment | Purpose | Scaling | Data | Access |
|-------------|---------|---------|------|--------|
| Local Development | Individual developer work | Single-node | Ephemeral, sample data | Developer only |
| Development | Team integration | Limited scaling | Refreshable test data | Team members |
| Staging | Pre-production validation | Production-like | Anonymized production data | Authorized team |
| Production | Live operation | Full auto-scaling | Real production data | End-users, admins |

## Infrastructure Architecture

### Production Environment

The production environment uses a Kubernetes-based architecture on AWS:

```mermaid
graph TD
    subgraph "AWS Cloud"
        subgraph "VPC"
            subgraph "Public Subnets"
                LB[Load Balancer]
                BAS[Bastion Host]
            end
            
            subgraph "Private Subnets"
                subgraph "EKS Cluster"
                    NG1[Node Group 1]
                    NG2[Node Group 2]
                    NG3[Node Group 3]
                end
            end
            
            subgraph "Database Subnets"
                RDS[RDS PostgreSQL]
                ES[ElastiCache Redis]
            end
        end
        
        S3[S3 Buckets]
        ECR[Container Registry]
        IAM[IAM Roles]
        CW[CloudWatch]
        R53[Route 53]
    end
    
    USER[End Users] --> R53
    R53 --> LB
    LB --> NG1
    LB --> NG2
    LB --> NG3
    
    NG1 --> RDS
    NG2 --> RDS
    NG3 --> RDS
    
    NG1 --> ES
    NG2 --> ES
    NG3 --> ES
    
    NG1 --> S3
    NG2 --> S3
    NG3 --> S3
    
    NG1 --> ECR
    NG2 --> ECR
    NG3 --> ECR
    
    IAM --> NG1
    IAM --> NG2
    IAM --> NG3
    
    NG1 --> CW
    NG2 --> CW
    NG3 --> CW
    
    ADMIN[Administrators] --> BAS
    BAS --> NG1
    
    style USER fill:#d0e0ff,stroke:#0066cc
    style ADMIN fill:#d0e0ff,stroke:#0066cc
    style LB fill:#ffe0d0,stroke:#cc6600
    style BAS fill:#ffe0d0,stroke:#cc6600
    style NG1 fill:#ffe0d0,stroke:#cc6600
    style NG2 fill:#ffe0d0,stroke:#cc6600
    style NG3 fill:#ffe0d0,stroke:#cc6600
    style RDS fill:#d0ffd0,stroke:#00cc00
    style ES fill:#d0ffd0,stroke:#00cc00
    style S3 fill:#d0ffd0,stroke:#00cc00
    style ECR fill:#d0ffd0,stroke:#00cc00
    style IAM fill:#d0ffd0,stroke:#00cc00
    style CW fill:#d0ffd0,stroke:#00cc00
    style R53 fill:#d0ffd0,stroke:#00cc00
```

### Kubernetes Architecture

The EKS cluster is organized into namespaces with the following components:

```mermaid
graph TD
    subgraph "EKS Cluster"
        subgraph "kube-system Namespace"
            KP[Kube Proxy]
            CNI[AWS CNI]
            CC[Cluster Autoscaler]
            EB[AWS EBS CSI Driver]
        end
        
        subgraph "monitoring Namespace"
            PROM[Prometheus]
            GRAF[Grafana]
            AM[Alertmanager]
            LOKI[Loki]
        end
        
        subgraph "ingress Namespace"
            IC[Ingress Controller]
            CM[Cert Manager]
            EP[External DNS]
        end
        
        subgraph "default Namespace"
            API[API Gateway]
            AO[Agent Orchestrator]
            PS[Planning System]
            MO[Model Orchestration]
            TI[Tool Integration]
            PC[Project Coordinator]
            SI[Service Integration]
            WD[Web Dashboard]
        end
    end
    
    style KP fill:#ffe0d0,stroke:#cc6600
    style CNI fill:#ffe0d0,stroke:#cc6600
    style CC fill:#ffe0d0,stroke:#cc6600
    style EB fill:#ffe0d0,stroke:#cc6600
    style PROM fill:#ffe0d0,stroke:#cc6600
    style GRAF fill:#ffe0d0,stroke:#cc6600
    style AM fill:#ffe0d0,stroke:#cc6600
    style LOKI fill:#ffe0d0,stroke:#cc6600
    style IC fill:#ffe0d0,stroke:#cc6600
    style CM fill:#ffe0d0,stroke:#cc6600
    style EP fill:#ffe0d0,stroke:#cc6600
    style API fill:#ffe0d0,stroke:#cc6600
    style AO fill:#ffe0d0,stroke:#cc6600
    style PS fill:#ffe0d0,stroke:#cc6600
    style MO fill:#ffe0d0,stroke:#cc6600
    style TI fill:#ffe0d0,stroke:#cc6600
    style PC fill:#ffe0d0,stroke:#cc6600
    style SI fill:#ffe0d0,stroke:#cc6600
    style WD fill:#ffe0d0,stroke:#cc6600
```

### Node Group Configuration

The EKS cluster uses node groups with different characteristics to optimize resource allocation:

| Node Group | Instance Type | Purpose | Scaling |
|------------|--------------|---------|---------|
| General | t3.xlarge | API Gateway, Web Dashboard | 2-5 nodes |
| Compute | c5.2xlarge | Model Orchestration, Planning System | 3-10 nodes |
| Memory | r5.2xlarge | Agent Orchestrator, Project Coordinator | 2-8 nodes |

## Service Deployment

### Kubernetes Deployment Configuration

Each service is deployed using Kubernetes manifests:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-orchestrator
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent-orchestrator
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: agent-orchestrator
    spec:
      containers:
      - name: agent-orchestrator
        image: ${ECR_REPOSITORY}/agent-orchestrator:${VERSION}
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "1000m"
            memory: "2Gi"
        readinessProbe:
          httpGet:
            path: /health/readiness
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health/liveness
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 15
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
        - name: LOG_LEVEL
          value: "INFO"
        - name: MODEL_ORCHESTRATION_URL
          value: "http://model-orchestration.default.svc.cluster.local:8080"
        - name: TOOL_INTEGRATION_URL
          value: "http://tool-integration.default.svc.cluster.local:8080"
        - name: PLANNING_SYSTEM_URL
          value: "http://planning-system.default.svc.cluster.local:8080"
```

### Service Exposure

Services are exposed through a multi-tier approach:

```mermaid
flowchart LR
    subgraph "External"
        USER[User]
    end
    
    subgraph "DNS & Load Balancing"
        R53[Route 53 DNS]
        ALB[Application Load Balancer]
    end
    
    subgraph "Kubernetes"
        ING[Ingress]
        SVC[Service]
        POD[Pods]
    end
    
    USER --> R53
    R53 --> ALB
    ALB --> ING
    ING --> SVC
    SVC --> POD
    
    style USER fill:#d0e0ff,stroke:#0066cc
    style R53 fill:#ffe0d0,stroke:#cc6600
    style ALB fill:#ffe0d0,stroke:#cc6600
    style ING fill:#ffe0d0,stroke:#cc6600
    style SVC fill:#ffe0d0,stroke:#cc6600
    style POD fill:#ffe0d0,stroke:#cc6600
```

### Internal Service Communication

Services communicate internally using Kubernetes services:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: agent-orchestrator
  namespace: default
spec:
  selector:
    app: agent-orchestrator
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

## Scaling Configuration

### Horizontal Pod Autoscaling

Services scale based on CPU and memory utilization:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-orchestrator
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-orchestrator
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Cluster Autoscaling

Node groups scale automatically based on pod scheduling requirements:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-config
  namespace: kube-system
data:
  config.yaml: |
    ---
    scaleDownUnneededTime: 5m
    scaleDownDelayAfterAdd: 5m
    scaleDownUtilizationThreshold: 0.5
```

## Database Architecture

### RDS Configuration

The PostgreSQL database uses a multi-AZ deployment with read replicas:

```mermaid
graph TD
    subgraph "Primary Region"
        Primary[(Primary DB)]
        Standby[(Standby DB)]
        Primary <-.-> Standby
        
        Primary --> ReadReplica1[(Read Replica 1)]
        Primary --> ReadReplica2[(Read Replica 2)]
    end
    
    subgraph "Secondary Region"
        CrossRegionReplica[(Cross-Region Replica)]
    end
    
    Primary --> CrossRegionReplica
    
    style Primary fill:#d0ffd0,stroke:#00cc00
    style Standby fill:#ffe0d0,stroke:#cc6600
    style ReadReplica1 fill:#ffe0d0,stroke:#cc6600
    style ReadReplica2 fill:#ffe0d0,stroke:#cc6600
    style CrossRegionReplica fill:#ffe0d0,stroke:#cc6600
```

### ElastiCache Configuration

Redis is deployed as a cluster with replication:

```mermaid
graph TD
    subgraph "Redis Cluster"
        Master[(Master)]
        
        Master --> Replica1[(Replica 1)]
        Master --> Replica2[(Replica 2)]
        
        subgraph "Shard 1"
            Master
            Replica1
        end
        
        subgraph "Shard 2"
            Master2[(Master)]
            Replica3[(Replica 1)]
            Replica4[(Replica 2)]
            
            Master2 --> Replica3
            Master2 --> Replica4
        end
    end
    
    style Master fill:#d0ffd0,stroke:#00cc00
    style Replica1 fill:#ffe0d0,stroke:#cc6600
    style Replica2 fill:#ffe0d0,stroke:#cc6600
    style Master2 fill:#d0ffd0,stroke:#00cc00
    style Replica3 fill:#ffe0d0,stroke:#cc6600
    style Replica4 fill:#ffe0d0,stroke:#cc6600
```

## Network Architecture

### Network Security

The network is secured through multiple layers:

```mermaid
graph TD
    subgraph "Internet"
        USER[Users]
    end
    
    subgraph "VPC"
        subgraph "Public Subnet"
            WAF[AWS WAF]
            ALB[Load Balancer]
        end
        
        subgraph "Private Subnet"
            SG1[Security Group]
            EKS[EKS Nodes]
        end
        
        subgraph "Database Subnet"
            SG2[Security Group]
            RDS[RDS Database]
            ES[ElastiCache]
        end
    end
    
    USER --> WAF
    WAF --> ALB
    ALB --> SG1
    SG1 --> EKS
    EKS --> SG2
    SG2 --> RDS
    SG2 --> ES
    
    style USER fill:#d0e0ff,stroke:#0066cc
    style WAF fill:#ffe0d0,stroke:#cc6600
    style ALB fill:#ffe0d0,stroke:#cc6600
    style SG1 fill:#ffe0d0,stroke:#cc6600
    style EKS fill:#ffe0d0,stroke:#cc6600
    style SG2 fill:#ffe0d0,stroke:#cc6600
    style RDS fill:#d0ffd0,stroke:#00cc00
    style ES fill:#d0ffd0,stroke:#00cc00
```

### Network Policies

Kubernetes network policies control pod-to-pod communication:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agent-orchestrator-policy
spec:
  podSelector:
    matchLabels:
      app: agent-orchestrator
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: model-orchestration
    ports:
    - protocol: TCP
      port: 8080
  - to:
    - podSelector:
        matchLabels:
          app: tool-integration
    ports:
    - protocol: TCP
      port: 8080
```

## High Availability and Disaster Recovery

### High Availability Architecture

The system is designed for high availability across multiple layers:

| Layer | HA Strategy | Recovery Time Objective |
|-------|-------------|-------------------------|
| Load Balancing | Multi-AZ ALB | < 1 minute |
| Kubernetes | Multi-AZ EKS, multiple nodes | < 1 minute |
| Application | Multiple pods, readiness/liveness probes | < 30 seconds |
| Database | Multi-AZ RDS with automated failover | < 2 minutes |
| Cache | Multi-AZ ElastiCache with replication | < 1 minute |
| Object Storage | S3 with cross-region replication | Zero downtime |

### Disaster Recovery Strategy

The DR strategy uses a warm standby approach:

```mermaid
graph TD
    subgraph "Primary Region"
        PA[Active Environment]
    end
    
    subgraph "Secondary Region"
        SB[Standby Environment]
    end
    
    PA -->|Continuous Replication| SB
    PA -->|Regular Backups| S3B[S3 Backup Bucket]
    S3B -->|Cross-Region Replication| S3DR[DR S3 Bucket]
    S3DR --> SB
    
    style PA fill:#d0ffd0,stroke:#00cc00
    style SB fill:#ffe0d0,stroke:#cc6600
    style S3B fill:#d0ffd0,stroke:#00cc00
    style S3DR fill:#ffe0d0,stroke:#cc6600
```

### Backup Strategy

Data is protected through a comprehensive backup approach:

| Data Type | Backup Frequency | Retention Period | Storage |
|-----------|------------------|------------------|---------|
| Database | Daily full backup | 30 days | S3 |
| Database | Transaction logs | 7 days | S3 |
| ElastiCache | Daily snapshot | 7 days | S3 |
| Configuration | On change | 90 days | S3 |
| User data | Daily incremental | 90 days | S3 |

## Infrastructure as Code

All infrastructure is defined as code using Terraform:

```hcl
module "eks" {
  source = "./modules/eks"
  
  cluster_name    = "berrys-agents-v2-${var.environment}"
  cluster_version = "1.22"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids
  
  node_groups = {
    general = {
      instance_types = ["t3.xlarge"]
      min_size       = 2
      max_size       = 5
      desired_size   = 2
    }
    
    compute = {
      instance_types = ["c5.2xlarge"]
      min_size       = 3
      max_size       = 10
      desired_size   = 3
    }
    
    memory = {
      instance_types = ["r5.2xlarge"]
      min_size       = 2
      max_size       = 8
      desired_size   = 2
    }
  }
}
```

## Deployment Pipeline

The deployment process follows a CI/CD pipeline:

```mermaid
graph TD
    A[Code Repository] --> B[Build & Test]
    B --> C[Container Image Creation]
    C --> D[Image Repository]
    D --> E[Deploy to Development]
    E --> F[Automated Testing]
    F --> G[Deploy to Staging]
    G --> H[Integration Testing]
    H --> I{Approval}
    I -->|Approved| J[Deploy to Production]
    I -->|Rejected| K[Fix Issues]
    K --> B
    
    style A fill:#d0e0ff,stroke:#0066cc
    style B fill:#ffe0d0,stroke:#cc6600
    style C fill:#ffe0d0,stroke:#cc6600
    style D fill:#d0ffd0,stroke:#00cc00
    style E fill:#ffe0d0,stroke:#cc6600
    style F fill:#ffe0d0,stroke:#cc6600
    style G fill:#ffe0d0,stroke:#cc6600
    style H fill:#ffe0d0,stroke:#cc6600
    style I fill:#ffffd0,stroke:#cccc00
    style J fill:#d0ffd0,stroke:#00cc00
    style K fill:#ffd0d0,stroke:#cc0000
```

## References

- [System Overview](system-overview.md)
- [Communication Patterns](communication-patterns.md)
- [Data Flow](data-flow.md)
- [Security Model](security-model.md)
- [Production Deployment Guide](../../guides/deployment/production.md)
- [Deployment Workflow](../../guides/process-flows/deployment-workflow.md)
