 # ApeRAG Build Guide

This document describes how to build and deploy ApeRAG images.

## Image Repositories

ApeRAG images are published to two registries:

### Docker Hub
- Backend: `docker.io/apecloud/aperag`
- Frontend: `docker.io/apecloud/aperag-frontend`

### GitHub Container Registry (GHCR)
- Backend: `ghcr.io/apecloud/aperag`
- Frontend: `ghcr.io/apecloud/aperag-frontend`

## Building Images Locally

### Backend Image

```bash
# Build backend image
docker build -f Dockerfile -t apecloud/aperag:latest .

# Run backend image
docker run -p 8000:8000 apecloud/aperag:latest
```

### Frontend Image

```bash
# Build frontend image
cd frontend
docker build -f Dockerfile.prod -t apecloud/aperag-frontend:latest .

# Run frontend image
docker run -p 3000:3000 \
  -e APERAG_CONSOLE_SERVICE_HOST=host.docker.internal \
  -e APERAG_CONSOLE_SERVICE_PORT=8000 \
  apecloud/aperag-frontend:latest
```

Or use the provided Makefile:

```bash
cd frontend
make -f Makefile.docker build
make -f Makefile.docker run
```

## Multi-platform Builds

To build for multiple platforms (AMD64 and ARM64):

```bash
# Backend
docker buildx build --platform linux/amd64,linux/arm64 \
  -f Dockerfile -t apecloud/aperag:latest . --push

# Frontend
cd frontend
docker buildx build --platform linux/amd64,linux/arm64 \
  -f Dockerfile.prod -t apecloud/aperag-frontend:latest . --push
```

## GitHub Actions Workflows

### Automatic Builds

The following workflows automatically build and push images:

1. **`build-images.yml`** - Builds both backend and frontend images on:
   - Push to `main` branch
   - New tags (releases)
   - Pull requests (build only, no push)

2. **`release-image.yml`** - Official release workflow triggered by:
   - Manual workflow dispatch
   - GitHub releases

### CI/CD Checks

- **`cicd-push.yml`** - Runs on every push, includes image build checks
- **`cicd-pull-request.yml`** - Runs on approved PRs, includes image build checks

## Deployment

### Helm Chart

The Helm chart has been updated to support the new frontend architecture:

```bash
# Deploy with default values
helm install aperag deploy/aperag

# Deploy with custom frontend image
helm install aperag deploy/aperag \
  --set frontend.image.repository=ghcr.io/apecloud/aperag-frontend \
  --set frontend.image.tag=v1.0.0
```

### Docker Compose

For local development, you can use Docker Compose with the new images:

```yaml
version: '3.8'
services:
  backend:
    image: apecloud/aperag:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///app/db.sqlite3
  
  frontend:
    image: apecloud/aperag-frontend:latest
    ports:
      - "3000:3000"
    environment:
      - APERAG_CONSOLE_SERVICE_HOST=backend
      - APERAG_CONSOLE_SERVICE_PORT=8000
    depends_on:
      - backend
```

## Troubleshooting

### Common Issues

1. **Frontend build fails**: Ensure Node.js 20+ is available in the build environment
2. **Backend build fails**: Check that all Python dependencies are properly locked in `uv.lock`
3. **Multi-platform build issues**: Ensure Docker Buildx is properly configured

### Debug Commands

```bash
# Check image contents
docker run --rm -it apecloud/aperag:latest /bin/bash
docker run --rm -it apecloud/aperag-frontend:latest /bin/sh

# Check image layers
docker history apecloud/aperag:latest
docker history apecloud/aperag-frontend:latest
```