# Using Kubernetes to Deploy and Manage Databases

This document aims to help application developers quickly deploy and manage various database services in a Kubernetes (k8s) environment through KubeBlocks.

## Introduction to KubeBlocks

[KubeBlocks](https://kubeblocks.io/) is an open-source project designed to simplify running and managing various databases and analytical workloads on Kubernetes. It provides a unified approach to deploying and operating databases, whether for daily development testing or production-level deployment. KubeBlocks supports advanced operational capabilities such as high availability, backup and recovery, horizontal and vertical scaling, and monitoring.

With KubeBlocks, you can easily run a variety of data services including relational databases, NoSQL databases, vector databases, and streaming computation systems.

## Prerequisites

Ensure you have the following environment and tools:

* **Kubernetes cluster**:
    * A running Kubernetes cluster is required.
    * For local development and testing, consider using [Minikube](https://minikube.sigs.k8s.io/docs/start/). Minikube can quickly set up a single-node Kubernetes environment on your personal computer.
    * Of course, you can also use any standard Kubernetes cluster, such as those provided by cloud service providers (AWS EKS, Google GKE, Azure AKS) or self-built clusters.

* **`kubectl`**:
    * The Kubernetes command-line tool for interacting with your cluster.
    * Ensure `kubectl` is installed and configured to connect to your Kubernetes cluster.
    * Installation guide: [Install and Set Up kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)

* **`helm`**:
    * The package manager for Kubernetes, used to simplify application deployment and management.
    * Installation guide: [Installing Helm](https://helm.sh/docs/intro/install/)

## Quick Start

### Deployment Steps

1. **Configure Database Options**:
   Open the `00-config.sh` file. Based on your requirements, set the `ENABLE_DATABASE_TYPE` variable to `true` for the databases you want to install. For example, to install PostgreSQL and Redis:

   ```bash
   ENABLE_POSTGRESQL=true
   ENABLE_REDIS=true
   ENABLE_ELASTICSEARCH=false # Set to true or false as needed
   ENABLE_QDRANT=false      # Set to true or false as needed
   ENABLE_MONGODB=false     # Set to true or false as needed
   ENABLE_NEO4J=false       # Set to true or false as needed
   ```
   You can also modify other general configurations in this file, such as `NAMESPACE` (default is `rag`).

2. **Prepare Environment and Install KubeBlocks Addons**:
   Execute the script to add the Helm repository and install KubeBlocks Addons for the selected databases.

   ```bash
   bash ./01-prepare.sh
   ```

3. **(Optional) Customize Database Configuration**:
   Before executing the installation script, you can modify the `values.yaml` file in each database directory to adjust specific configurations for the database cluster, such as version, CPU, memory, storage space, etc. For example, to modify the storage size for PostgreSQL, edit the `postgresql/values.yaml` file.

4. **Install Database Clusters**:
   Execute the script to deploy the database clusters enabled in `00-config.sh`.

   ```bash
   bash ./02-install-database.sh
   ```
   After the script completes, it will prompt you on how to check the status of installed clusters:
   ```bash
   kubectl get clusters -n <NAMESPACE> # Replace <NAMESPACE> with the namespace configured in 00-config.sh
   ```

### Uninstalling Databases

1. **Uninstall Database Clusters**:
   If you need to remove installed database clusters, execute the following script. This operation will uninstall the corresponding clusters based on the enabled settings in `00-config.sh`.

   ```bash
   bash ./03-uninstall-database.sh
   ```

2. **Clean Up KubeBlocks Addons**:
   If you want to completely remove the KubeBlocks database Addons, execute the following script. This operation will uninstall the corresponding Addons based on the enabled settings in `00-config.sh`.

   ```bash
   bash ./04-cleanup.sh
   ```