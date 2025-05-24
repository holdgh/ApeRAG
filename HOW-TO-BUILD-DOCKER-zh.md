# ApeRAG Docker 构建指南

本文档介绍如何在本地构建 ApeRAG 的 Docker 镜像。

## 前置要求

### macOS

```bash
# 安装 Docker Desktop for Mac
# 下载地址: https://www.docker.com/products/docker-desktop/

# 验证安装
docker --version
docker-compose --version

# 启用 Docker Buildx (多平台构建支持)
docker buildx create --name multiplatform --use
docker buildx inspect --bootstrap
```

### Linux (Ubuntu/Debian)

```bash
# 安装 Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 添加用户到 docker 组
sudo usermod -aG docker $USER
newgrp docker

# 安装 Docker Buildx
mkdir -p ~/.docker/cli-plugins/
curl -SL https://github.com/docker/buildx/releases/latest/download/buildx-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m) -o ~/.docker/cli-plugins/docker-buildx
chmod a+x ~/.docker/cli-plugins/docker-buildx

# 创建多平台构建器
docker buildx create --name multiplatform --use
```

### Windows

```bash
# 安装 Docker Desktop for Windows
# 下载地址: https://www.docker.com/products/docker-desktop/

# 在 PowerShell 中验证
docker --version
docker buildx version

# 创建多平台构建器
docker buildx create --name multiplatform --use
```

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/apecloud/ApeRAG.git
cd ApeRAG
```

### 2. 构建后端镜像

```bash
# 基础构建 (仅当前平台)
docker build -f Dockerfile -t aperag:local .

# 多平台构建 (推荐)
docker buildx build --platform linux/amd64,linux/arm64 \
  -f Dockerfile -t aperag:local --load .
```

### 3. 构建前端镜像

```bash
# 进入前端目录
cd frontend

# 基础构建
docker build -f Dockerfile.prod -t aperag-frontend:local .

# 多平台构建
docker buildx build --platform linux/amd64,linux/arm64 \
  -f Dockerfile.prod -t aperag-frontend:local --load .
```

## 详细构建说明

### 后端镜像构建

#### 标准构建

```bash
# 在项目根目录执行
docker build -f Dockerfile -t aperag:latest .

# 指定版本标签
docker build -f Dockerfile -t aperag:v1.0.0 .

# 查看构建的镜像
docker images | grep aperag
```

#### 优化构建 (使用缓存)

```bash
# 使用 BuildKit 缓存
export DOCKER_BUILDKIT=1

docker build \
  --cache-from aperag:latest \
  -f Dockerfile \
  -t aperag:latest .
```

#### 多平台构建

```bash
# 构建 AMD64 和 ARM64 版本
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f Dockerfile \
  -t aperag:multiplatform \
  --load .

# 仅构建 ARM64 (适用于 Apple Silicon Mac)
docker buildx build \
  --platform linux/arm64 \
  -f Dockerfile \
  -t aperag:arm64 \
  --load .
```

### 前端镜像构建

#### 标准构建

```bash
cd frontend

# 生产环境构建
docker build -f Dockerfile.prod -t aperag-frontend:latest .

# 开发环境构建 (如果有 Dockerfile.dev)
docker build -f Dockerfile -t aperag-frontend:dev .
```

#### 多平台构建

```bash
cd frontend

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f Dockerfile.prod \
  -t aperag-frontend:multiplatform \
  --load .
```

## 推送到镜像仓库

### GitHub Container Registry (推荐)

```bash
# 登录 GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# 标记镜像
docker tag aperag:latest ghcr.io/apecloud/aperag:latest
docker tag aperag-frontend:latest ghcr.io/apecloud/aperag-frontend:latest

# 推送
docker push ghcr.io/apecloud/aperag:latest
docker push ghcr.io/apecloud/aperag-frontend:latest
```

### Docker Hub

```bash
# 登录
docker login

# 标记镜像
docker tag aperag:latest apecloud/aperag:latest
docker tag aperag-frontend:latest apecloud/aperag-frontend:latest

# 推送
docker push apecloud/aperag:latest
docker push apecloud/aperag-frontend:latest
```

### 私有仓库

```bash
# 登录私有仓库
docker login your-registry.com

# 标记并推送
docker tag aperag:latest your-registry.com/apecloud/aperag:latest
docker push your-registry.com/apecloud/aperag:latest
```

## 与 Kubernetes 部署集成

构建完成的镜像可以直接用于 Kubernetes 部署:

```bash
# 使用本地构建的镜像部署到 Kubernetes
helm install aperag ./deploy/aperag \
  --set image.registry=localhost \
  --set image.repository=aperag \
  --set image.tag=latest \
  --set frontend.image.registry=localhost \
  --set frontend.image.repository=aperag-frontend \
  --set frontend.image.tag=latest
```