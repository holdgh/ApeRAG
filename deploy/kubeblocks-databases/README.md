# KubeBlocks 数据库部署指南

本项目提供了使用 KubeBlocks 在 Kubernetes 集群中快速部署和管理多种数据库的配置和工具。

## 项目概述

KubeBlocks 是一个云原生数据基础设施平台，帮助您在 Kubernetes 上轻松管理各类数据库。本项目包含了预配置的数据库部署模板，让您可以一键部署各种常用数据库。

## 支持的数据库

本项目默认安装以下所有数据库：

- **PostgreSQL** - 强大的开源关系型数据库
- **Redis** - 高性能键值存储数据库
- **Elasticsearch** - 分布式搜索和分析引擎
- **Qdrant** - 向量搜索引擎
- **MongoDB** - 文档型数据库
- **Neo4j** - 图数据库

## 目录结构

```
kubeblocks-databases/
├── README.md                  # 使用指南
├── pre-check.sh               # 预检查和安装数据库插件脚本
├── install-database.sh        # 安装数据库集群脚本
├── uninstall-database.sh      # 卸载数据库脚本
├── postgresql/                # PostgreSQL 配置
│   └── values.yaml           # 集群配置文件
├── redis/                     # Redis 配置
│   └── values.yaml           # 集群配置文件
├── elasticsearch/             # Elasticsearch 配置和脚本
│   ├── install.sh            # 安装脚本
│   ├── uninstall.sh          # 卸载脚本
│   └── values.yaml           # 集群配置
├── qdrant/                    # Qdrant 配置和脚本
│   ├── install.sh            # 安装脚本
│   ├── uninstall.sh          # 卸载脚本
│   └── values.yaml           # 集群配置
├── mongodb/                   # MongoDB 配置和脚本
│   ├── install.sh            # 安装脚本
│   ├── uninstall.sh          # 卸载脚本
│   └── values.yaml           # 集群配置
└── neo4j/                     # Neo4j 配置和脚本
    ├── install.sh            # 安装脚本
    ├── uninstall.sh          # 卸载脚本
    └── values.yaml           # 集群配置
```

## 安装前提条件

- Kubernetes 集群 (v1.19+)
- Helm 3.2.0+
- 已安装 KubeBlocks Operator

## 命名空间说明

本项目使用以下固定的命名空间：
- **kb-system** - 用于安装KubeBlocks插件
- **rag** - 用于部署数据库集群

## 使用方法

### 步骤1: 前置检查和安装插件

运行预检查脚本，添加仓库并安装所有数据库插件：

```bash
# 执行预检查和插件安装
./pre-check.sh
```

此脚本将：
- 添加 KubeBlocks Helm 仓库
- 创建必要的命名空间
- 安装所有数据库插件

### 步骤2: 安装数据库集群

安装所有数据库集群：

```bash
# 安装数据库集群
./install-database.sh
```

此脚本将安装所有支持的数据库集群。

## 卸载方法

要卸载已部署的数据库，请使用卸载脚本：

```bash
# 卸载数据库
./uninstall-database.sh
```

此脚本将提示您：
- 是否确认卸载（这将删除所有数据）
- 是否仅卸载数据库集群，保留 KubeBlocks 插件

## 自定义配置

每个数据库目录中的 `values.yaml` 文件包含了该数据库的详细配置选项：

```bash
# 例如，编辑 PostgreSQL 的配置
vim postgresql/values.yaml
```

主要配置项包括：
- 版本
- 部署模式（如单机模式、复制模式等）
- 资源配置（CPU、内存、存储）
- 高可用选项

## 参考链接

- [KubeBlocks 官方文档](https://kubeblocks.io/docs/)
- [KubeBlocks GitHub 仓库](https://github.com/apecloud/kubeblocks)
- [Helm 文档](https://helm.sh/docs/)

## 许可证

Copyright © 2024

Licensed under the Apache License, Version 2.0
