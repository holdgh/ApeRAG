#!/bin/bash

# Database configuration file
# Modify this file to control which databases to install/uninstall

# Set to true to enable the database, false to disable
ENABLE_POSTGRESQL=true
ENABLE_REDIS=true
ENABLE_ELASTICSEARCH=true
ENABLE_QDRANT=true
ENABLE_MONGODB=true
ENABLE_NEO4J=true

# Namespace configuration
NAMESPACE="rag"
# Addon version
ADDON_CLUSTER_CHART_VERSION="1.0.0-alpha.0"
# Helm repository
HELM_REPO="https://apecloud.github.io/helm-charts"