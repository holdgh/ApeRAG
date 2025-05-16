#!/bin/bash

# Load configuration file
source ./00-config.sh

echo "Uninstalling database clusters..."

# Uninstall database clusters based on configuration
[ "$ENABLE_POSTGRESQL" = true ] && echo "Uninstalling PostgreSQL cluster..." && helm uninstall pg-cluster --namespace $NAMESPACE 2>/dev/null || true
[ "$ENABLE_REDIS" = true ] && echo "Uninstalling Redis cluster..." && helm uninstall redis-cluster --namespace $NAMESPACE 2>/dev/null || true
[ "$ENABLE_ELASTICSEARCH" = true ] && echo "Uninstalling Elasticsearch cluster..." && helm uninstall es-cluster --namespace $NAMESPACE 2>/dev/null || true
[ "$ENABLE_QDRANT" = true ] && echo "Uninstalling Qdrant cluster..." && helm uninstall qdrant-cluster --namespace $NAMESPACE 2>/dev/null || true
[ "$ENABLE_MONGODB" = true ] && echo "Uninstalling MongoDB cluster..." && helm uninstall mongodb-cluster --namespace $NAMESPACE 2>/dev/null || true
[ "$ENABLE_NEO4J" = true ] && echo "Uninstalling Neo4j cluster..." && helm uninstall neo4j-cluster --namespace $NAMESPACE 2>/dev/null || true

echo "Database clusters uninstalled"
echo "To uninstall database addons, run cleanup.sh" 