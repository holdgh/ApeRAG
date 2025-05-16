# KubeBlocks Database Deployment Guide

This project provides configurations and tools for quickly deploying and managing various databases in Kubernetes clusters using KubeBlocks.

## Project Overview

KubeBlocks is a cloud-native data infrastructure platform that helps you easily manage various databases on Kubernetes. This project contains pre-configured database deployment templates, allowing you to deploy various common databases with one click.

## Supported Databases

This project installs all of the following databases by default:

- **PostgreSQL** - Powerful open-source relational database
- **Redis** - High-performance key-value storage database
- **Elasticsearch** - Distributed search and analytics engine
- **Qdrant** - Vector search engine
- **MongoDB** - Document database
- **Neo4j** - Graph database

## Prerequisites

- Kubernetes cluster (v1.19+)
- Helm 3.2.0+
- KubeBlocks Operator installed

## Namespace Information

This project uses the following fixed namespaces:
- **kb-system** - For installing KubeBlocks addons
- **rag** - For deploying database clusters

## Usage

### Step 1: Pre-check and Install Addons

Run the prepare script to add the repository and install all database addons:

```bash
# Execute prepare and addon installation
./01-prepare.sh
```

This script will:
- Add the KubeBlocks Helm repository
- Create necessary namespaces
- Install all database addons

### Step 2: Install Database Clusters

Install all database clusters:

```bash
# Install database clusters
./02-install-database.sh
```

This script will install all supported database clusters.

## Uninstallation

To uninstall deployed databases, use the uninstallation script:

```bash
# Uninstall databases
./03-uninstall-database.sh
```

This script will prompt you:
- To confirm uninstallation (this will delete all data)
- Whether to only uninstall database clusters, keeping KubeBlocks addons

To completely remove all addons, run:

```bash
# Clean up all addons
./04-cleanup.sh
```

## Custom Configuration

The `values.yaml` file in each database directory contains detailed configuration options for that database:

```bash
# For example, edit PostgreSQL configuration
vim postgresql/values.yaml
```

Main configuration items include:
- Version
- Deployment mode (e.g., standalone mode, replication mode, etc.)
- Resource configuration (CPU, memory, storage)
- High availability options

## References

- [KubeBlocks Official Documentation](https://kubeblocks.io/docs/)
- [KubeBlocks GitHub Repository](https://github.com/apecloud/kubeblocks)
- [Helm Documentation](https://helm.sh/docs/)

## License

Copyright © 2024

Licensed under the Apache License, Version 2.0
