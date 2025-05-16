#!/bin/bash

# Load configuration file
source ./config.sh

echo "Uninstalling KubeBlocks database addons..."

# Uninstall database addons based on configuration
[ "$ENABLE_POSTGRESQL" = true ] && echo "Uninstalling PostgreSQL addon..." && helm uninstall kb-addon-postgresql --namespace kb-system 2>/dev/null || true
[ "$ENABLE_REDIS" = true ] && echo "Uninstalling Redis addon..." && helm uninstall kb-addon-redis --namespace kb-system 2>/dev/null || true
[ "$ENABLE_ELASTICSEARCH" = true ] && echo "Uninstalling Elasticsearch addon..." && helm uninstall kb-addon-elasticsearch --namespace kb-system 2>/dev/null || true
[ "$ENABLE_QDRANT" = true ] && echo "Uninstalling Qdrant addon..." && helm uninstall kb-addon-qdrant --namespace kb-system 2>/dev/null || true
[ "$ENABLE_MONGODB" = true ] && echo "Uninstalling MongoDB addon..." && helm uninstall kb-addon-mongodb --namespace kb-system 2>/dev/null || true
[ "$ENABLE_NEO4J" = true ] && echo "Uninstalling Neo4j addon..." && helm uninstall kb-addon-neo4j --namespace kb-system 2>/dev/null || true

echo "Database addons uninstallation completed!" 