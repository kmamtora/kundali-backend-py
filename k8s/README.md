# Kubernetes Deployment with Kustomize

This directory contains Kubernetes manifests for deploying the Enterprise FastAPI application using Kustomize.

## Structure

```
k8s/
├── base/                           # Base Kubernetes manifests
│   ├── configmap.yaml             # Application configuration
│   ├── deployment.yaml            # API, Worker, and Beat deployments
│   ├── kustomization.yaml         # Base kustomization
│   ├── poddisruptionbudget.yaml   # PDB for high availability
│   ├── secret.yaml                # Sensitive configuration
│   ├── service.yaml               # Service definition
│   └── serviceaccount.yaml        # Service account
└── overlays/                       # Environment-specific overlays
    ├── development/               # Development environment
    │   └── kustomization.yaml
    ├── staging/                   # Staging environment
    │   └── kustomization.yaml
    └── production/                # Production environment
        └── kustomization.yaml
```

## Prerequisites

- Kubernetes cluster (1.19+)
- kubectl CLI tool
- kustomize CLI tool (or use `kubectl apply -k`)
- PostgreSQL database
- Redis instance

## Quick Start

### 1. Update Secrets

Before deploying, update the secrets in `base/secret.yaml` or create your own secret:

```bash
kubectl create secret generic enterprise-api-secrets \
  --from-literal=DATABASE_URL='postgresql+asyncpg://user:password@postgres:5432/enterprise_api' \
  --from-literal=SECRET_KEY='your-strong-secret-key-at-least-32-characters' \
  --from-literal=REDIS_URL='redis://redis:6379/0' \
  --namespace=your-namespace
```

### 2. Deploy to Development

```bash
# Preview what will be deployed
kubectl kustomize k8s/overlays/development

# Apply the configuration
kubectl apply -k k8s/overlays/development
```

### 3. Deploy to Staging

```bash
kubectl apply -k k8s/overlays/staging
```

### 4. Deploy to Production

```bash
kubectl apply -k k8s/overlays/production
```

## Environment Configurations

### Development

- **Namespace**: `development`
- **Replicas**: 1 API, 1 Worker
- **Resources**: Lower limits for cost efficiency
- **Debug**: Enabled
- **Docs**: Enabled
- **Image Tag**: `dev`

### Staging

- **Namespace**: `staging`
- **Replicas**: 2 API, 2 Worker
- **Resources**: Medium limits
- **Debug**: Disabled
- **Docs**: Enabled
- **Image Tag**: `staging`

### Production

- **Namespace**: `production`
- **Replicas**: 3 API, 3 Worker
- **Resources**: Higher limits for performance
- **Debug**: Disabled
- **Docs**: Disabled (security)
- **Image Tag**: `v1.0.0`
- **PDB**: Minimum 2 available pods

## Customization

### Updating Configuration

Edit the ConfigMap in `base/configmap.yaml` or use patches in overlays:

```yaml
# In overlays/production/kustomization.yaml
patches:
- patch: |-
    - op: replace
      path: /data/LOG_LEVEL
      value: "WARNING"
  target:
    kind: ConfigMap
    name: enterprise-api-config
```

### Changing Image Tag

Update the image tag in the overlay's `kustomization.yaml`:

```yaml
images:
- name: enterprise-api
  newName: your-registry/enterprise-api
  newTag: v1.2.3
```

### Scaling Replicas

Update replicas in the overlay's `kustomization.yaml`:

```yaml
replicas:
- name: enterprise-api
  count: 5
- name: enterprise-api-worker
  count: 5
```

## Deployment Commands

### View Generated Manifests

```bash
kubectl kustomize k8s/overlays/production
```

### Apply Configuration

```bash
kubectl apply -k k8s/overlays/production
```

### Delete Resources

```bash
kubectl delete -k k8s/overlays/production
```

### Diff Before Applying

```bash
kubectl diff -k k8s/overlays/production
```

## Monitoring

### Check Deployment Status

```bash
kubectl get deployments -n production -l app=enterprise-api
```

### View Pods

```bash
kubectl get pods -n production -l app=enterprise-api
```

### Check Logs

```bash
# API logs
kubectl logs -n production -l app=enterprise-api,component=api --tail=100 -f

# Worker logs
kubectl logs -n production -l app=enterprise-api,component=worker --tail=100 -f

# Beat logs
kubectl logs -n production -l app=enterprise-api,component=beat --tail=100 -f
```

### Check Service

```bash
kubectl get service -n production enterprise-api
```

### Port Forward for Testing

```bash
kubectl port-forward -n production svc/enterprise-api 8000:80
```

Then access the API at `http://localhost:8000`

## Health Checks

The deployments include health checks:

- **Liveness Probe**: `/health/live` - Checks if the application is running
- **Readiness Probe**: `/health/ready` - Checks if the application is ready to serve traffic

## Resource Management

### Resource Requests and Limits

Each environment has different resource configurations:

**Development:**
- API: 100m CPU / 256Mi Memory (request), 500m CPU / 512Mi Memory (limit)
- Worker: 100m CPU / 256Mi Memory (request), 500m CPU / 512Mi Memory (limit)

**Production:**
- API: 500m CPU / 1Gi Memory (request), 2000m CPU / 2Gi Memory (limit)
- Worker: 500m CPU / 1Gi Memory (request), 2000m CPU / 2Gi Memory (limit)

### Pod Disruption Budgets

Production environment includes PDBs to ensure high availability during:
- Node maintenance
- Cluster upgrades
- Voluntary disruptions

## Security

### Service Account

Each deployment uses a dedicated service account with minimal permissions.

### Security Context

Pods run with:
- Non-root user (UID 1000)
- Read-only root filesystem where possible
- Dropped capabilities

### Secrets Management

Secrets should be managed using:
- Kubernetes Secrets (encrypted at rest)
- External secret managers (AWS Secrets Manager, HashiCorp Vault, etc.)
- Sealed Secrets for GitOps workflows

## Troubleshooting

### Pods Not Starting

```bash
kubectl describe pod -n production <pod-name>
kubectl logs -n production <pod-name>
```

### Configuration Issues

```bash
kubectl get configmap -n production enterprise-api-config -o yaml
kubectl get secret -n production enterprise-api-secrets -o yaml
```

### Database Connection Issues

Check the DATABASE_URL in secrets and ensure:
- Database is accessible from the cluster
- Credentials are correct
- Network policies allow traffic

### Redis Connection Issues

Check the REDIS_URL in secrets and ensure:
- Redis is accessible from the cluster
- Network policies allow traffic

## CI/CD Integration

### GitOps with ArgoCD

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: enterprise-api-prod
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/enterprise-api
    targetRevision: main
    path: k8s/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### GitHub Actions

```yaml
- name: Deploy to Production
  run: |
    kubectl apply -k k8s/overlays/production
```

## Best Practices

1. **Never commit secrets**: Use external secret management
2. **Use specific image tags**: Avoid `latest` in production
3. **Set resource limits**: Prevent resource exhaustion
4. **Enable PDBs**: Ensure high availability
5. **Monitor deployments**: Use Prometheus and Grafana
6. **Test in staging**: Always test changes before production
7. **Use namespaces**: Isolate environments
8. **Implement RBAC**: Restrict access appropriately

## Support

For issues and questions, please open an issue in the repository.
