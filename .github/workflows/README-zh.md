# GitHub Workflows 说明

## 镜像构建Workflows对比

### 1. `build-images.yml` - 日常开发构建 (仅GHCR)

**用途**: 现代化的、轻量级的镜像构建流程，适合日常开发，只推送到GHCR

**触发条件**:
- ✅ 推送到 `main` 分支 → 自动构建并推送镜像到GHCR
- ✅ 创建 tag (v*) → 自动构建并推送带版本号的镜像到GHCR
- ✅ Pull Request → 只构建验证，不推送

**特点**:
- 🚀 快速、简洁
- 🏗️ 使用GitHub托管的runner (ubuntu-latest)
- 🔄 自动化程度高，无需手动干预
- 📦 只推送到GitHub Container Registry (GHCR)
- 🏷️ 自动生成标签 (branch名、PR号、版本号等)
- 💰 成本较低 (使用GitHub免费runner)
- 🔒 无需Docker Hub认证

**推荐使用场景**:
- 日常开发分支合并
- 自动化CI/CD流程
- 快速验证构建
- 内部使用和测试

### 2. `release-image.yml` - 正式发布构建 (Docker Hub + GHCR)

**用途**: 企业级的、功能完整的发布流程，适合正式版本发布

**触发条件**:
- ✅ 手动触发 (workflow_dispatch) → 可选择构建特定镜像
- ✅ GitHub Release发布 → 自动构建所有镜像

**特点**:
- 🏢 企业级功能完整
- 🖥️ 使用自托管runner (GKE/EKS)
- 🎯 支持选择性构建 (只构建backend/frontend/llmserver)
- 📢 集成消息通知 (飞书)
- 🧪 集成E2E测试
- 📊 详细的构建结果追踪
- 💸 成本较高 (自托管runner)
- 📦 同时推送到Docker Hub和GHCR

**推荐使用场景**:
- 正式版本发布
- 需要选择性构建特定组件
- 需要完整的发布流程和通知
- 公开发布到Docker Hub

## 当前Secret配置状态

### ✅ 已有的Secrets:
- `DOCKER_REGISTRY_USER` / `DOCKER_REGISTRY_PASSWORD` - Docker Hub认证 (用于release-image.yml) ✅
- `PERSONAL_ACCESS_TOKEN` - GitHub访问令牌 ✅
- `GITHUB_TOKEN` - 自动提供，用于GHCR ✅

### ℹ️ Secret使用说明:
- `build-images.yml`: 只需要 `GITHUB_TOKEN` (自动提供)
- `release-image.yml`: 需要 `DOCKER_REGISTRY_USER/PASSWORD` + `GITHUB_TOKEN`

## 使用建议

### 推荐的工作流程:

1. **日常开发**: 使用 `build-images.yml` (仅GHCR)
   ```bash
   # 推送到main分支，自动触发构建并推送到GHCR
   git push origin main
   
   # 创建tag，自动构建版本镜像并推送到GHCR
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **正式发布**: 使用 `release-image.yml` (Docker Hub + GHCR)
   ```bash
   # 方式1: 创建GitHub Release (推荐)
   # 在GitHub界面创建Release，自动触发完整发布流程
   
   # 方式2: 手动触发
   # 在GitHub Actions界面手动运行workflow
   ```

### 镜像地址:

**GitHub Container Registry (GHCR)** - 日常开发:
- `ghcr.io/apecloud/aperag:latest` (后端)  
- `ghcr.io/apecloud/aperag-frontend:latest` (前端)

**Docker Hub** - 正式发布:
- `docker.io/apecloud/aperag:latest` (后端)
- `docker.io/apecloud/aperag-frontend:latest` (前端)

## 成本优化建议

### 当前配置:
- `build-images.yml`: 使用GitHub免费runner + 免费GHCR ✅ 成本极低
- `release-image.yml`: 使用自托管runner ⚠️ 成本高

### 优化建议:
1. **日常开发使用build-images.yml**: 快速、免费、无需额外认证
2. **重要发布使用release-image.yml**: 功能完整、公开发布
3. **内部测试优先使用GHCR镜像**: 减少Docker Hub拉取限制

## 故障排除

### 常见问题:

1. **GHCR推送失败**:
   - 确保仓库设置中启用了"Actions"权限
   - 检查 `GITHUB_TOKEN` 权限
   - 确认包可见性设置正确

2. **Docker Hub认证失败** (仅release-image.yml):
   - 确保 `DOCKER_REGISTRY_USER` 和 `DOCKER_REGISTRY_PASSWORD` 正确设置
   
3. **自托管runner不可用** (仅release-image.yml):
   - 检查GKE/EKS集群状态
   - 确认runner标签配置正确

### 调试命令:
```bash
# 本地测试构建
docker build -f Dockerfile -t test-backend .
docker build -f frontend/Dockerfile.prod -t test-frontend ./frontend

# 检查GHCR镜像
docker pull ghcr.io/apecloud/aperag:latest
docker pull ghcr.io/apecloud/aperag-frontend:latest

# 检查镜像
docker images | grep apecloud
``` 