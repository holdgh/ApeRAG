#!/bin/bash

# KubeBlocks数据库安装脚本
# 安装所有数据库集群

# 硬编码命名空间
NAMESPACE="rag"

echo "安装所有数据库集群..."

# 直接安装所有数据库集群
helm upgrade --install pg-cluster kubeblocks/postgresql-cluster -f ./postgresql/values.yaml --namespace $NAMESPACE
helm upgrade --install redis-cluster kubeblocks/redis-cluster -f ./redis/values.yaml --namespace $NAMESPACE
helm upgrade --install es-cluster kubeblocks/elasticsearch-cluster -f ./elasticsearch/values.yaml --namespace $NAMESPACE
helm upgrade --install qdrant-cluster kubeblocks/qdrant-cluster -f ./qdrant/values.yaml --namespace $NAMESPACE
helm upgrade --install mongodb-cluster kubeblocks/mongodb-cluster -f ./mongodb/values.yaml --namespace $NAMESPACE
helm upgrade --install neo4j-cluster kubeblocks/neo4j-cluster -f ./neo4j/values.yaml --namespace $NAMESPACE

echo "所有数据库集群安装完成!"
echo "使用以下命令查看安装的集群状态:"
echo "kubectl get clusters -n $NAMESPACE" 