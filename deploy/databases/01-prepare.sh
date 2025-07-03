#!/bin/bash

# Get the directory where this script is located
DATABASE_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Load configuration file
source "$DATABASE_SCRIPT_DIR/00-config.sh"

check_dependencies

# Check if KubeBlocks is already installed, install it if it is not.
source "$DATABASE_SCRIPT_DIR/install-kubeblocks.sh"

# Create namespaces
print "Creating namespaces..."
kubectl create namespace $NAMESPACE 2>/dev/null || true

# Install database addons
print "Installing KubeBlocks database addons..."

# Add and update Helm repository
print "Adding and updating KubeBlocks Helm repository..."
helm repo add kubeblocks-addons $KUBEBLOCKS_ADDONS_HELM_REPO
helm repo update kubeblocks-addons

# postgresql, redis, mongodb are enabled by default in kubeblocks-addons
# qdrant is not enabled by default in kubeblocks-addons
# elasticsearch is not installed by default in kubeblocks-addons

# Install addons
[ "$ENABLE_ELASTICSEARCH" = true ] && print "Installing Elasticsearch addon..." && helm upgrade --install kb-addon-elasticsearch kubeblocks-addons/elasticsearch --namespace kb-system --version 0.9.1

# Enable addons
kbcli addon enable elasticsearch
kbcli addon enable qdrant

print_success "KubeBlocks database addons installation completed!"
print "Now you can run 02-install-database.sh to install database clusters"
