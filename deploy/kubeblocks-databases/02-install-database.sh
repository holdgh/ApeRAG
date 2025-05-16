#!/bin/bash

# KubeBlocks database installation script
# Install all database clusters

# Load configuration file
source ./00-config.sh

echo "Installing database clusters..."

# Install database clusters based on configuration
[ "$ENABLE_POSTGRESQL" = true ] && echo "Installing PostgreSQL cluster..." && helm upgrade --install pg-cluster kubeblocks/postgresql-cluster -f ./postgresql/values.yaml --namespace $NAMESPACE
[ "$ENABLE_REDIS" = true ] && echo "Installing Redis cluster..." && helm upgrade --install redis-cluster kubeblocks/redis-cluster -f ./redis/values.yaml --namespace $NAMESPACE
[ "$ENABLE_ELASTICSEARCH" = true ] && echo "Installing Elasticsearch cluster..." && helm upgrade --install es-cluster kubeblocks/elasticsearch-cluster -f ./elasticsearch/values.yaml --namespace $NAMESPACE
[ "$ENABLE_QDRANT" = true ] && echo "Installing Qdrant cluster..." && helm upgrade --install qdrant-cluster kubeblocks/qdrant-cluster -f ./qdrant/values.yaml --namespace $NAMESPACE
[ "$ENABLE_MONGODB" = true ] && echo "Installing MongoDB cluster..." && helm upgrade --install mongodb-cluster kubeblocks/mongodb-cluster -f ./mongodb/values.yaml --namespace $NAMESPACE
[ "$ENABLE_NEO4J" = true ] && echo "Installing Neo4j cluster..." && helm upgrade --install neo4j-cluster kubeblocks/neo4j-cluster -f ./neo4j/values.yaml --namespace $NAMESPACE

echo "Database clusters installation completed!"
echo "Use the following command to check the status of installed clusters:"
echo "kubectl get clusters -n $NAMESPACE" 