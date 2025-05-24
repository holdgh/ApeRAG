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

#### 使用 Makefile

```bash
cd frontend

# 查看可用命令
make help

# 构建镜像
make -f Makefile.docker build

# 构建并运行
make -f Makefile.docker run
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

## 运行镜像

### 单独运行后端

```bash
# 基础运行
docker run -p 8000:8000 aperag:latest

# 带环境变量运行
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///app/db.sqlite3 \
  -e DEBUG=True \
  aperag:latest

# 挂载数据卷
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env \
  aperag:latest
```

### 单独运行前端

```bash
# 基础运行
docker run -p 3000:3000 aperag-frontend:latest

# 连接到后端服务
docker run -p 3000:3000 \
  -e APERAG_CONSOLE_SERVICE_HOST=host.docker.internal \
  -e APERAG_CONSOLE_SERVICE_PORT=8000 \
  aperag-frontend:latest
```

## 构建优化技巧

### 1. 使用 .dockerignore

确保项目根目录和 `frontend/` 目录都有 `.dockerignore` 文件来减少构建上下文:

```bash
# 检查 .dockerignore 文件
cat .dockerignore
cat frontend/.dockerignore
```

### 2. 多阶段构建缓存

```bash
# 利用 Docker 层缓存
docker build \
  --cache-from aperag:latest \
  --cache-from aperag:builder \
  -f Dockerfile \
  -t aperag:latest .
```

### 3. 并行构建

```bash
# 同时构建前后端 (在不同终端中)
# 终端 1
docker build -f Dockerfile -t aperag:latest .

# 终端 2
cd frontend && docker build -f Dockerfile.prod -t aperag-frontend:latest .
```

### 4. 使用 BuildKit 特性

```bash
# 启用 BuildKit
export DOCKER_BUILDKIT=1

# 使用内联缓存
docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -f Dockerfile \
  -t aperag:latest .
```

## 平台特定说明

### Apple Silicon Mac (M1/M2/M3)

```bash
# 构建原生 ARM64 镜像 (推荐)
docker buildx build \
  --platform linux/arm64 \
  -f Dockerfile \
  -t aperag:arm64 \
  --load .

# 如果需要 AMD64 兼容性
docker buildx build \
  --platform linux/amd64 \
  -f Dockerfile \
  -t aperag:amd64 \
  --load .
```

### Intel Mac

```bash
# 默认构建 AMD64
docker build -f Dockerfile -t aperag:latest .

# 也可以构建 ARM64 (通过模拟)
docker buildx build \
  --platform linux/arm64 \
  -f Dockerfile \
  -t aperag:arm64 \
  --load .
```

### Linux x86_64

```bash
# 原生 AMD64 构建
docker build -f Dockerfile -t aperag:latest .

# 交叉编译 ARM64 (需要 qemu)
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
docker buildx build \
  --platform linux/arm64 \
  -f Dockerfile \
  -t aperag:arm64 \
  --load .
```

## 故障排除

### 常见问题

#### 1. 构建失败: "No space left on device"

```bash
# 清理 Docker 缓存
docker system prune -a

# 清理构建缓存
docker builder prune -a

# 检查磁盘空间
df -h
```

#### 2. 多平台构建失败

```bash
# 重新创建构建器
docker buildx rm multiplatform
docker buildx create --name multiplatform --use
docker buildx inspect --bootstrap
```

#### 3. 前端构建内存不足

```bash
# 增加 Node.js 内存限制
docker build \
  --build-arg NODE_OPTIONS="--max-old-space-size=4096" \
  -f frontend/Dockerfile.prod \
  -t aperag-frontend:latest \
  frontend/
```

#### 4. 网络连接问题

```bash
# 使用国内镜像源 (中国用户)
docker build \
  --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
  --build-arg NPM_REGISTRY=https://registry.npmmirror.com \
  -f Dockerfile \
  -t aperag:latest .
```

### 调试命令

```bash
# 查看镜像详情
docker inspect aperag:latest

# 查看镜像层
docker history aperag:latest

# 进入容器调试
docker run --rm -it aperag:latest /bin/bash
docker run --rm -it aperag-frontend:latest /bin/sh

# 查看构建日志
docker build --progress=plain -f Dockerfile -t aperag:debug .
```

## 性能优化

### 构建时间优化

```bash
# 使用并行构建
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --cache-from type=local,src=/tmp/.buildx-cache \
  --cache-to type=local,dest=/tmp/.buildx-cache \
  -f Dockerfile \
  -t aperag:latest .
```

### 镜像大小优化

```bash
# 查看镜像大小
docker images | grep aperag

# 分析镜像层大小
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  wagoodman/dive:latest aperag:latest
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

## 总结

本指南涵盖了在各种平台上构建 ApeRAG Docker 镜像的完整流程。对于日常开发，推荐使用:

1. **macOS**: 使用 Docker Desktop + Buildx 进行多平台构建
2. **Linux**: 使用 Docker Engine + Buildx
3. **Windows**: 使用 Docker Desktop + WSL2

构建的镜像名称与部署配置保持一致:
- 后端镜像: `aperag`
- 前端镜像: `aperag-frontend`

如果遇到问题，请参考故障排除部分或查看项目的 GitHub Issues。 