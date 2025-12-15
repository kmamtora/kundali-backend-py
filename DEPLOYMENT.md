# Deployment Guide

This document provides instructions for deploying the Enterprise FastAPI application to Kubernetes using either Kustomize or Helm.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Option 1: Kustomize Deployment](#option-1-kustomize-deployment)
- [Option 2: Helm Deployment](#option-2-helm-deployment)
- [Post-Deployment](#post-deployment)
- [Monitoring and Maintenance](#monitoring-and-maintenance)

## Prerequisites

Before deploying, ensure you have:

1. **Kubernetes Cluster** (1.19+)
   - Access to a Kubernetes cluster
   - `kubectl` configured with cluster access

2. **External Dependencies**
   - PostgreSQL database (accessible from cluster)
   - Redis instance (accessible from cluster)

3. **Container Image**
   - Build and push the Docker image to your registry:
   ```bash
   docker build -t your-registry/enterprise-api:v1.0.0 .
   docker push your-registry/enterprise-api:v1.0.0
   ```

4. **Deployment Tools**
   - For Kustomize: `kubectl` (1.14+) or `kustomize` CLI
   - For Helm: `helm` (3.0+)

## Deployment Options

You can deploy using either:
- **Kustomize**: Simpler, declarative approach with environment overlays
- **Helm**: More flexible with templating and package management

## Option 1: Kustomize Deployment

### Step 1: Configure Secrets

Create a Kubernetes secret with your credentials:

```bash
# For development
kubectl create namespace development

kubectl create secret generic dev-enterprise-api-secrets \
  --from-literal=DATABASE_URL='postgresql+asyncpg://user:password@postgres:5432/enterprise_api' \
  --from-literal=SECRET_KEY='your-strong-secret-key-minimum-32-characters-long' \
  --from-literal=REDIS_URL='redis://redis:6379/0' \
  --from-literal=CELERY_BROKER_URL='redis://redis:6379/0' \
  --from-literal=CELERY_RESULT_BACKEND='redis://redis:6379/0' \
  --from-literal=RATE_LIMIT_STORAGE_URL='redis://redis:6379/0' \
  --namespace=development
```

### Step 2: Update Image Reference

Edit `k8s/overlays/development/kustomization.yaml` to use your image:

```yaml
images:
- name: enterprise-api
  newName: your-registry/enterprise-api
  newTag: v1.0.0
```

### Step 3: Deploy

```bash
# Preview the deployment
kubectl kustomize k8s/overlays/development

# Apply the deployment
kubectl apply -k k8s/overlays/development
```

### Step 4: Verify Deployment

```bash
# Check pods
kubectl get pods -n development -l app=enterprise-api

# Check services
kubectl get svc -n development

# View logs
kubectl logs -n development -l app=enterprise-api,component=api --tail=50
```

### Deploying to Other Environments

**Staging:**
```bash
kubectl create namespace staging
# Create secrets for staging
kubectl apply -k k8s/overlays/staging
```

**Production:**
```bash
kubectl create namespace production
# Create secrets for production
kubectl apply -k k8s/overlays/production
```

## Option 2: Helm Deployment

### Step 1: Configure Values

Create a custom values file or use the provided environment-specific files:

```bash
# Copy and edit for your environment
cp helm/enterprise-api/values-dev.yaml my-values.yaml
```

Edit `my-values.yaml` to set:
- Image repository and tag
- Database URL
- Secret key
- Redis URL
- Other environment-specific settings

### Step 2: Install with Helm

**Development:**
```bash
helm install dev-api ./helm/enterprise-api \
  -f ./helm/enterprise-api/values-dev.yaml \
  --set image.repository=your-registry/enterprise-api \
  --set image.tag=v1.0.0 \
  --set secrets.databaseUrl='postgresql+asyncpg://user:password@postgres:5432/enterprise_api' \
  --set secrets.secretKey='your-strong-secret-key-minimum-32-characters-long' \
  --namespace development \
  --create-namespace
```

**Production:**
```bash
helm install prod-api ./helm/enterprise-api \
  -f ./helm/enterprise-api/values-prod.yaml \
  --set image.repository=your-registry/enterprise-api \
  --set image.tag=v1.0.0 \
  --set secrets.existingSecret=prod-secrets \
  --namespace production \
  --create-namespace
```

### Step 3: Verify Installation

```bash
# Check Helm release
helm list -n development

# Check pods
kubectl get pods -n development -l app.kubernetes.io/name=enterprise-api

# View logs
kubectl logs -n development -l app.kubernetes.io/name=enterprise-api,component=api --tail=50
```

### Upgrading with Helm

```bash
helm upgrade dev-api ./helm/enterprise-api \
  -f ./helm/enterprise-api/values-dev.yaml \
  --set image.tag=v1.1.0 \
  --namespace development
```

### Uninstalling

```bash
helm uninstall dev-api --namespace development
```

## Post-Deployment

### 1. Initialize Database

Run database migrations:

```bash
# Get a pod name
POD=$(kubectl get pod -n development -l app=enterprise-api,component=api -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec -n development $POD -- alembic upgrade head
```

### 2. Create Superuser

```bash
kubectl exec -n development $POD -- python -m scripts.create_superuser
```

### 3. Test the API

Port forward to access the API:

```bash
kubectl port-forward -n development svc/enterprise-api 8000:80
```

Then access:
- API: http://localhost:8000/api/v1
- Health: http://localhost:8000/health/live
- Docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics

### 4. Configure Ingress (Optional)

If using Ingress, ensure you have an Ingress controller installed:

```bash
# For Helm deployment, enable ingress
helm upgrade dev-api ./helm/enterprise-api \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=api-dev.example.com \
  --namespace development
```

## Monitoring and Maintenance

### Health Checks

The application exposes health check endpoints:
- **Liveness**: `/health/live` - Application is running
- **Readiness**: `/health/ready` - Application is ready to serve traffic

### Metrics

Prometheus metrics are available at `/metrics`

To enable ServiceMonitor (requires Prometheus Operator):

```bash
# For Helm
helm upgrade prod-api ./helm/enterprise-api \
  --set serviceMonitor.enabled=true \
  --namespace production
```

### Logs

View logs for different components:

```bash
# API logs
kubectl logs -n production -l component=api --tail=100 -f

# Worker logs
kubectl logs -n production -l component=worker --tail=100 -f

# Beat scheduler logs
kubectl logs -n production -l component=beat --tail=100 -f
```

### Scaling

**Manual scaling:**
```bash
kubectl scale deployment enterprise-api --replicas=5 -n production
```

**Auto-scaling (Helm):**
```bash
helm upgrade prod-api ./helm/enterprise-api \
  --set api.autoscaling.enabled=true \
  --set api.autoscaling.minReplicas=3 \
  --set api.autoscaling.maxReplicas=10 \
  --namespace production
```

### Rolling Updates

**Kustomize:**
```bash
# Update image tag in kustomization.yaml, then:
kubectl apply -k k8s/overlays/production
```

**Helm:**
```bash
helm upgrade prod-api ./helm/enterprise-api \
  --set image.tag=v1.1.0 \
  --namespace production
```

### Rollback

**Kustomize:**
```bash
kubectl rollout undo deployment/enterprise-api -n production
```

**Helm:**
```bash
helm rollback prod-api -n production
```

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod to see events
kubectl describe pod <pod-name> -n development

# Check logs
kubectl logs <pod-name> -n development

# Check previous container logs if pod is restarting
kubectl logs <pod-name> -n development --previous
```

### Database Connection Issues

1. Verify DATABASE_URL is correct
2. Check network connectivity:
   ```bash
   kubectl exec -n development <pod-name> -- nc -zv postgres-host 5432
   ```
3. Verify database credentials

### Redis Connection Issues

1. Verify REDIS_URL is correct
2. Check network connectivity:
   ```bash
   kubectl exec -n development <pod-name> -- nc -zv redis-host 6379
   ```

### Configuration Issues

```bash
# View ConfigMap
kubectl get configmap -n development -o yaml

# View Secret (base64 encoded)
kubectl get secret -n development -o yaml
```

## Security Best Practices

1. **Never commit secrets** to version control
2. **Use external secret management** (AWS Secrets Manager, HashiCorp Vault, etc.)
3. **Rotate secrets regularly**
4. **Use RBAC** to restrict access
5. **Enable network policies** to restrict traffic
6. **Scan images** for vulnerabilities
7. **Keep Kubernetes updated**
8. **Use specific image tags** (avoid `latest`)

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
      
      - name: Deploy with Kustomize
        run: |
          cd k8s/overlays/production
          kustomize edit set image enterprise-api=${{ secrets.REGISTRY }}/enterprise-api:${{ github.ref_name }}
          kubectl apply -k .
```

### ArgoCD Example

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: enterprise-api-prod
  namespace: argocd
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

## Support

For issues and questions:
- Check the logs first
- Review the README files in `k8s/` and `helm/enterprise-api/`
- Open an issue in the repository

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize Documentation](https://kustomize.io/)
- [Helm Documentation](https://helm.sh/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
