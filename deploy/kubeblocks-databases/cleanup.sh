#!/bin/bash

# 卸载所有数据库插件
echo "卸载所有KubeBlocks数据库插件..."

# 卸载所有数据库addon
helm uninstall kb-addon-postgresql --namespace kb-system 2>/dev/null || true
helm uninstall kb-addon-redis --namespace kb-system 2>/dev/null || true
helm uninstall kb-addon-elasticsearch --namespace kb-system 2>/dev/null || true
helm uninstall kb-addon-qdrant --namespace kb-system 2>/dev/null || true
helm uninstall kb-addon-mongodb --namespace kb-system 2>/dev/null || true
helm uninstall kb-addon-neo4j --namespace kb-system 2>/dev/null || true

echo "所有KubeBlocks数据库插件已卸载!" 