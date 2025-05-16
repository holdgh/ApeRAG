#!/bin/bash

# 加载配置文件
source ./config.sh

echo "卸载KubeBlocks数据库插件..."

# 根据配置卸载数据库插件
[ "$ENABLE_POSTGRESQL" = true ] && echo "卸载PostgreSQL插件..." && helm uninstall kb-addon-postgresql --namespace kb-system 2>/dev/null || true
[ "$ENABLE_REDIS" = true ] && echo "卸载Redis插件..." && helm uninstall kb-addon-redis --namespace kb-system 2>/dev/null || true
[ "$ENABLE_ELASTICSEARCH" = true ] && echo "卸载Elasticsearch插件..." && helm uninstall kb-addon-elasticsearch --namespace kb-system 2>/dev/null || true
[ "$ENABLE_QDRANT" = true ] && echo "卸载Qdrant插件..." && helm uninstall kb-addon-qdrant --namespace kb-system 2>/dev/null || true
[ "$ENABLE_MONGODB" = true ] && echo "卸载MongoDB插件..." && helm uninstall kb-addon-mongodb --namespace kb-system 2>/dev/null || true
[ "$ENABLE_NEO4J" = true ] && echo "卸载Neo4j插件..." && helm uninstall kb-addon-neo4j --namespace kb-system 2>/dev/null || true

echo "数据库插件卸载完成!" 