# KubeBlocks 数据库部署指南

本项目提供了使用 KubeBlocks 在 Kubernetes 集群中快速部署和管理多种数据库的配置和工具。

## 项目概述

KubeBlocks 是一个云原生数据基础设施平台，帮助您在 Kubernetes 上轻松管理各类数据库。本项目包含了预配置的数据库部署模板，让您可以一键部署各种常用数据库。

## 支持的数据库

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
├── pre-install.sh             # 预安装环境设置脚本
├── install-all.sh             # 一键安装所有数据库脚本
├── uninstall-all.sh           # 一键卸载所有数据库脚本
├── postgresql/                # PostgreSQL 配置和脚本
│   ├── install.sh            # 安装脚本
│   ├── uninstall.sh          # 卸载脚本
│   └── values.yaml           # 集群配置
├── redis/                     # Redis 配置和脚本
│   ├── install.sh            # 安装脚本
│   ├── uninstall.sh          # 卸载脚本
│   └── values.yaml           # 集群配置
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

## 使用方法

### 步骤1: 预安装设置（仅需执行一次）

首次使用前，运行预安装设置脚本：

```bash
# 赋予执行权限
chmod +x pre-install.sh

# 执行预安装脚本
./pre-install.sh
```

该脚本将执行以下操作：
- 添加KubeBlocks Helm仓库
- 更新仓库信息
- 创建必要的命名空间

### 步骤2: 安装数据库

#### 安装单个数据库

每个数据库都可以独立安装和配置。进入对应数据库的目录，然后执行安装脚本：

```bash
# 进入要安装的数据库目录，例如PostgreSQL
cd postgresql

# 赋予脚本执行权限（如果需要）
chmod +x install.sh

# 执行安装脚本
./install.sh
```

#### 安装所有数据库

如果您需要安装所有支持的数据库，可以使用一键安装脚本：

```bash
# 赋予执行权限
chmod +x install-all.sh

# 执行安装脚本
./install-all.sh
```

> 注意：您可以在脚本中注释掉不需要安装的数据库。

### 自定义配置

每个数据库目录中的 `values.yaml` 文件包含了该数据库的配置选项。您可以在执行安装脚本前修改这些配置：

```bash
# 编辑配置文件
vim values.yaml

# 然后执行安装脚本
./install.sh
```

主要配置项包括：

- **版本**: 指定数据库版本
- **部署模式**: 如单机模式、复制模式等
- **资源配置**: CPU、内存和存储容量
- **高可用设置**: 副本数、故障恢复策略等
- **命名空间**: 在values文件中可以指定部署的命名空间

## 卸载方法

### 卸载单个数据库

要卸载特定数据库，进入对应数据库目录，然后执行卸载脚本：

```bash
# 进入要卸载的数据库目录，例如PostgreSQL
cd postgresql

# 赋予脚本执行权限（如果需要）
chmod +x uninstall.sh

# 执行卸载脚本
./uninstall.sh
```

### 卸载所有数据库

如果需要卸载所有数据库，可以使用一键卸载脚本：

```bash
# 赋予执行权限
chmod +x uninstall-all.sh

# 执行卸载脚本
./uninstall-all.sh
```

## 参考链接

- [KubeBlocks 官方文档](https://kubeblocks.io/docs/)
- [KubeBlocks GitHub 仓库](https://github.com/apecloud/kubeblocks)
- [Helm 文档](https://helm.sh/docs/)

## 许可证

Copyright © 2024

Licensed under the Apache License, Version 2.0
