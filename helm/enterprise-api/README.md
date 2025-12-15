# Enterprise API Helm Chart

A Helm chart for deploying the Enterprise FastAPI application on Kubernetes.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- PostgreSQL database (external or in-cluster)
- Redis (external or in-cluster)

## Installing the Chart

To install the chart with the release name `my-release`:

```bash
helm install my-release ./helm/enterprise-api
```

## Installing with Custom Values

For development environment:

```bash
helm install my-release ./helm/enterprise-api -f ./helm/enterprise-api/values-dev.yaml
```

For production environment:

```bash
helm install my-release ./helm/enterprise-api -f ./helm/enterprise-api/values-prod.yaml
```

## Uninstalling the Chart

To uninstall/delete the `my-release` deployment:

```bash
helm uninstall my-release
```

## Configuration

The following table lists the configurable parameters of the Enterprise API chart and their default values.

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.environment` | Environment name | `production` |

### Image Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Image repository | `enterprise-api` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `image.tag` | Image tag | `latest` |

### API Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `api.enabled` | Enable API deployment | `true` |
| `api.replicaCount` | Number of API replicas | `2` |
| `api.resources.requests.cpu` | CPU request | `250m` |
| `api.resources.requests.memory` | Memory request | `512Mi` |
| `api.resources.limits.cpu` | CPU limit | `1000m` |
| `api.resources.limits.memory` | Memory limit | `1Gi` |
| `api.autoscaling.enabled` | Enable HPA | `false` |
| `api.autoscaling.minReplicas` | Minimum replicas | `2` |
| `api.autoscaling.maxReplicas` | Maximum replicas | `10` |

### Worker Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `worker.enabled` | Enable worker deployment | `true` |
| `worker.replicaCount` | Number of worker replicas | `2` |
| `worker.concurrency` | Celery worker concurrency | `4` |
| `worker.resources.requests.cpu` | CPU request | `250m` |
| `worker.resources.requests.memory` | Memory request | `512Mi` |

### Service Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `80` |
| `service.targetPort` | Container port | `8000` |

### Ingress Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `false` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.hosts[0].host` | Hostname | `api.example.com` |

### Configuration Parameters

See `values.yaml` for the complete list of configuration parameters.

## Secrets Management

By default, the chart creates a Secret with placeholder values. For production:

1. Create your own Secret:

```bash
kubectl create secret generic enterprise-api-secrets \
  --from-literal=DATABASE_URL='postgresql+asyncpg://user:pass@host:5432/db' \
  --from-literal=SECRET_KEY='your-secret-key' \
  --from-literal=REDIS_URL='redis://redis:6379/0'
```

2. Set `secrets.existingSecret` to use your Secret:

```bash
helm install my-release ./helm/enterprise-api \
  --set secrets.existingSecret=enterprise-api-secrets
```

## Monitoring

### Prometheus

To enable Prometheus monitoring:

```yaml
serviceMonitor:
  enabled: true
  labels:
    prometheus: kube-prometheus
```

### Health Checks

The chart includes liveness and readiness probes:

- Liveness: `/health/live`
- Readiness: `/health/ready`

## Autoscaling

To enable horizontal pod autoscaling:

```yaml
api:
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
```

## Examples

### Development Deployment

```bash
helm install dev-api ./helm/enterprise-api \
  -f ./helm/enterprise-api/values-dev.yaml \
  --set image.tag=dev \
  --namespace development \
  --create-namespace
```

### Production Deployment

```bash
helm install prod-api ./helm/enterprise-api \
  -f ./helm/enterprise-api/values-prod.yaml \
  --set image.tag=v1.0.0 \
  --set secrets.existingSecret=prod-secrets \
  --namespace production \
  --create-namespace
```

### Upgrade Deployment

```bash
helm upgrade prod-api ./helm/enterprise-api \
  -f ./helm/enterprise-api/values-prod.yaml \
  --set image.tag=v1.1.0
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -l app.kubernetes.io/name=enterprise-api
```

### View Logs

```bash
# API logs
kubectl logs -l app.kubernetes.io/name=enterprise-api,component=api

# Worker logs
kubectl logs -l app.kubernetes.io/name=enterprise-api,component=worker
```

### Check Configuration

```bash
kubectl get configmap enterprise-api-config -o yaml
```

## Support

For issues and questions, please open an issue in the repository.
