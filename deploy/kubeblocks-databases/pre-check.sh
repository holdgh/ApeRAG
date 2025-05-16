#!/bin/bash

# 检查依赖工具
command -v kubectl >/dev/null 2>&1 || { echo "错误: 未找到kubectl命令"; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "错误: 未找到helm命令"; exit 1; }

NAMESPACE="rag"
HELM_REPO="https://apecloud.github.io/helm-charts"
ADDON_CLUSTER_CHART_VERSION="1.0.0-alpha.0"

# 添加和更新Helm仓库
echo "添加和更新KubeBlocks Helm仓库..."
helm repo add kubeblocks 
helm repo update $HELM_REPO

echo "Addon命名空间: kb-system"
echo "数据库命名空间: $NAMESPACE"
echo "插件版本: $ADDON_CLUSTER_CHART_VERSION"

# 创建命名空间
echo "创建命名空间..."
kubectl create namespace kb-system 2>/dev/null || true
kubectl create namespace $NAMESPACE 2>/dev/null || true

# 安装所有数据库插件
echo "安装KubeBlocks数据库插件..."

# 安装所有数据库addon
helm upgrade --install kb-addon-postgresql kubeblocks/postgresql --namespace kb-system --version $ADDON_CLUSTER_CHART_VERSION
helm upgrade --install kb-addon-redis kubeblocks/redis --namespace kb-system --version $ADDON_CLUSTER_CHART_VERSION
helm upgrade --install kb-addon-elasticsearch kubeblocks/elasticsearch --namespace kb-system --version $ADDON_CLUSTER_CHART_VERSION
helm upgrade --install kb-addon-qdrant kubeblocks/qdrant --namespace kb-system --version $ADDON_CLUSTER_CHART_VERSION
helm upgrade --install kb-addon-mongodb kubeblocks/mongodb --namespace kb-system --version $ADDON_CLUSTER_CHART_VERSION
helm upgrade --install kb-addon-neo4j kubeblocks/neo4j --namespace kb-system --version $ADDON_CLUSTER_CHART_VERSION

echo "所有KubeBlocks数据库插件安装完成!"
echo "现在您可以运行 install-database.sh 安装数据库集群" 