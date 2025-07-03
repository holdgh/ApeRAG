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

# elasticsearch is not installed by default in kubeblocks-addons, install it first and then enable it
helm upgrade --install kb-addon-elasticsearch kubeblocks-addons/elasticsearch --namespace kb-system --version 0.9.1
kbcli addon enable elasticsearch

# postgresql is enabled by default in kubeblocks-addons, upgrade it first and then enable it
kbcli addon upgrade postgresql --version=0.9.5

# redis is enabled by default in kubeblocks-addons, upgrade it first and then enable it
kbcli addon upgrade redis --version=0.9.3

# mongodb is enabled by default in kubeblocks-addons, upgrade it first and then enable it
kbcli addon upgrade mongodb --version=0.9.1

# qdrant is not enabled by default in kubeblocks-addons, upgrade it first and then enable it
kbcli addon upgrade qdrant --version=0.9.2
kbcli addon enable qdrant

print_success "KubeBlocks database addons installation completed!"
print "Now you can run 02-install-database.sh to install database clusters"
