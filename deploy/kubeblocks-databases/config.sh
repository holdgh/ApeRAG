#!/bin/bash

# 数据库配置文件
# 修改此文件可以控制安装/卸载哪些数据库

# 设置为true表示启用该数据库，false表示禁用
ENABLE_POSTGRESQL=true
ENABLE_REDIS=true
ENABLE_ELASTICSEARCH=true
ENABLE_QDRANT=true
ENABLE_MONGODB=true
ENABLE_NEO4J=true

# 命名空间配置
NAMESPACE="rag"
# 插件版本
ADDON_CLUSTER_CHART_VERSION="1.0.0-alpha.0"
# Helm仓库
HELM_REPO="https://apecloud.github.io/helm-charts" 