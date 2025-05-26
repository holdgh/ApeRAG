# ApeRAG Helm Chart

This Helm chart deploys ApeRAG application on Kubernetes.

## Default Configuration

By default, this chart uses images from GitHub Container Registry (GHCR):

- Backend: `ghcr.io/apecloud/aperag:latest`
- Frontend: `ghcr.io/apecloud/aperag-frontend:latest`

## Installation

```bash
# Add the chart repository (if using a repository)
helm repo add aperag https://your-repo-url

# Install the chart
helm install aperag ./deploy/aperag

# Or with custom values
helm install aperag ./deploy/aperag -f custom-values.yaml
```

## Configuration

### Image Configuration

You can override the default image settings in your `values.yaml`:

```yaml
image:
  registry: ghcr.io  # Default registry
  repository: apecloud/aperag
  tag: "latest"
  pullPolicy: IfNotPresent

frontend:
  image:
    registry: ghcr.io  # Default registry
    repository: apecloud/aperag-frontend
    tag: "latest"
```

### Using Different Registry

To use Docker Hub or other registries:

```yaml
image:
  registry: docker.io
  repository: apecloud/aperag
  tag: "v1.0.0"

frontend:
  image:
    registry: docker.io
    repository: apecloud/aperag-frontend
    tag: "v1.0.0"
```

### Image Pull Secrets

If you need to access private images from GHCR or other registries, configure imagePullSecrets:

```yaml
# Create a secret for GHCR access
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=your-github-username \
  --docker-password=your-github-token \
  --docker-email=your-email@example.com

# Then reference it in values.yaml
imagePullSecrets:
  - name: ghcr-secret
```

For public images, no imagePullSecrets are required.

## Environment Variables

All environment variables are managed through the `aperag-env` Secret. See `aperag-secret.yaml` template for configuration options.

## Components

- **Django**: Main application server
- **Celery Worker**: Background task processor
- **Celery Beat**: Scheduled task scheduler
- **Flower**: Celery monitoring tool
- **Frontend**: React-based web interface

## Requirements

- Kubernetes 1.19+
- Helm 3.0+
- PostgreSQL database
- Redis cache
- Vector database (Qdrant recommended)
- Elasticsearch (optional)
