#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check dependencies
echo "Checking dependencies..."
command -v kubectl >/dev/null 2>&1 || { echo "Error: kubectl command not found"; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "Error: helm command not found"; exit 1; }

# Check if Kubernetes is available
echo "Checking if Kubernetes is available..."
kubectl cluster-info &>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: Kubernetes cluster is not accessible. Please ensure you have proper access to a Kubernetes cluster."
    exit 1
fi
echo "Kubernetes cluster is accessible."

# Check if KubeBlocks is already installed
echo "Checking if KubeBlocks is already installed in kb-system namespace..."
if kubectl get namespace kb-system &>/dev/null; then
    if kubectl get deployment -n kb-system &>/dev/null; then
        echo "KubeBlocks is already installed in kb-system namespace."
    else
        echo "Error: kb-system namespace exists but KubeBlocks Pods not found."
        exit 1
    fi
else
    echo "Error: kb-system namespace not found."
    exit 1
fi

# Load configuration file
source "$SCRIPT_DIR/00-config.sh"

# Add and update Helm repository
echo "Adding and updating KubeBlocks Helm repository..."
helm repo add kubeblocks $HELM_REPO
helm repo update

# Create namespaces
echo "Creating namespaces..."
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
echo "Now you can run 02-install-database.sh to install database clusters"