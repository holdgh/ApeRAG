#!/bin/bash

# 加载配置文件
source ./config.sh

echo "卸载数据库集群..."

# 根据配置卸载数据库集群
[ "$ENABLE_POSTGRESQL" = true ] && echo "卸载PostgreSQL集群..." && helm uninstall pg-cluster --namespace $NAMESPACE 2>/dev/null || true
[ "$ENABLE_REDIS" = true ] && echo "卸载Redis集群..." && helm uninstall redis-cluster --namespace $NAMESPACE 2>/dev/null || true
[ "$ENABLE_ELASTICSEARCH" = true ] && echo "卸载Elasticsearch集群..." && helm uninstall es-cluster --namespace $NAMESPACE 2>/dev/null || true
[ "$ENABLE_QDRANT" = true ] && echo "卸载Qdrant集群..." && helm uninstall qdrant-cluster --namespace $NAMESPACE 2>/dev/null || true
[ "$ENABLE_MONGODB" = true ] && echo "卸载MongoDB集群..." && helm uninstall mongodb-cluster --namespace $NAMESPACE 2>/dev/null || true
[ "$ENABLE_NEO4J" = true ] && echo "卸载Neo4j集群..." && helm uninstall neo4j-cluster --namespace $NAMESPACE 2>/dev/null || true

echo "数据库集群已卸载"
echo "如需卸载数据库插件，请运行 cleanup.sh" 