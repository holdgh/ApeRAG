#!/bin/bash

# KubeBlocks数据库安装脚本
# 安装所有数据库集群

# 加载配置文件
source ./config.sh

echo "安装数据库集群..."

# 根据配置安装数据库集群
[ "$ENABLE_POSTGRESQL" = true ] && echo "安装PostgreSQL集群..." && helm upgrade --install pg-cluster kubeblocks/postgresql-cluster -f ./postgresql/values.yaml --namespace $NAMESPACE
[ "$ENABLE_REDIS" = true ] && echo "安装Redis集群..." && helm upgrade --install redis-cluster kubeblocks/redis-cluster -f ./redis/values.yaml --namespace $NAMESPACE
[ "$ENABLE_ELASTICSEARCH" = true ] && echo "安装Elasticsearch集群..." && helm upgrade --install es-cluster kubeblocks/elasticsearch-cluster -f ./elasticsearch/values.yaml --namespace $NAMESPACE
[ "$ENABLE_QDRANT" = true ] && echo "安装Qdrant集群..." && helm upgrade --install qdrant-cluster kubeblocks/qdrant-cluster -f ./qdrant/values.yaml --namespace $NAMESPACE
[ "$ENABLE_MONGODB" = true ] && echo "安装MongoDB集群..." && helm upgrade --install mongodb-cluster kubeblocks/mongodb-cluster -f ./mongodb/values.yaml --namespace $NAMESPACE
[ "$ENABLE_NEO4J" = true ] && echo "安装Neo4j集群..." && helm upgrade --install neo4j-cluster kubeblocks/neo4j-cluster -f ./neo4j/values.yaml --namespace $NAMESPACE

echo "数据库集群安装完成!"
echo "使用以下命令查看安装的集群状态:"
echo "kubectl get clusters -n $NAMESPACE" 