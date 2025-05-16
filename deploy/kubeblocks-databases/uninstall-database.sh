#!/bin/bash

# 硬编码命名空间
NAMESPACE="rag"

echo "卸载所有数据库集群..."

# 卸载所有数据库集群
helm uninstall pg-cluster --namespace $NAMESPACE 2>/dev/null || true
helm uninstall redis-cluster --namespace $NAMESPACE 2>/dev/null || true
helm uninstall es-cluster --namespace $NAMESPACE 2>/dev/null || true
helm uninstall qdrant-cluster --namespace $NAMESPACE 2>/dev/null || true
helm uninstall mongodb-cluster --namespace $NAMESPACE 2>/dev/null || true
helm uninstall neo4j-cluster --namespace $NAMESPACE 2>/dev/null || true

echo "所有数据库集群已卸载"
echo "如需卸载数据库插件，请运行 cleanup.sh" 