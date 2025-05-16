#!/bin/bash

# Check dependencies
command -v kubectl >/dev/null 2>&1 || { echo "Error: kubectl command not found"; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "Error: helm command not found"; exit 1; }

# Load configuration file
source ./00-config.sh

# Add and update Helm repository
echo "Adding and updating KubeBlocks Helm repository..."
helm repo add kubeblocks $HELM_REPO
helm repo update

# Create namespaces
echo "Creating namespaces..."
kubectl create namespace kb-system 2>/dev/null || true
kubectl create namespace $NAMESPACE 2>/dev/null || true

# Install database addons
echo "Installing KubeBlocks database addons..."

# Install database addons based on configuration
[ "$ENABLE_POSTGRESQL" = true ] && echo "Installing PostgreSQL addon..." && helm upgrade --install kb-addon-postgresql kubeblocks/postgresql --namespace kb-system --version $ADDON_CLUSTER_CHART_VERSION
[ "$ENABLE_REDIS" = true ] && echo "Installing Redis addon..." && helm upgrade --install kb-addon-redis kubeblocks/redis --namespace kb-system --version $ADDON_CLUSTER_CHART_VERSION
[ "$ENABLE_ELASTICSEARCH" = true ] && echo "Installing Elasticsearch addon..." && helm upgrade --install kb-addon-elasticsearch kubeblocks/elasticsearch --namespace kb-system --version $ADDON_CLUSTER_CHART_VERSION
[ "$ENABLE_QDRANT" = true ] && echo "Installing Qdrant addon..." && helm upgrade --install kb-addon-qdrant kubeblocks/qdrant --namespace kb-system --version $ADDON_CLUSTER_CHART_VERSION
[ "$ENABLE_MONGODB" = true ] && echo "Installing MongoDB addon..." && helm upgrade --install kb-addon-mongodb kubeblocks/mongodb --namespace kb-system --version $ADDON_CLUSTER_CHART_VERSION
[ "$ENABLE_NEO4J" = true ] && echo "Installing Neo4j addon..." && helm upgrade --install kb-addon-neo4j kubeblocks/neo4j --namespace kb-system --version $ADDON_CLUSTER_CHART_VERSION

echo "KubeBlocks database addons installation completed!"
echo "Now you can run install-database.sh to install database clusters" 