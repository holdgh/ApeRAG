# Using KubeBlocks to Deploy and Manage Databases

Learn how to quickly deploy and manage various database in a Kubernetes (k8s) environment through KubeBlocks.

## Introduction to KubeBlocksfferent data stores.

KubeBlocks is a production-ready, open-source toolkit that runs any database—SQL, NoSQL, vector, or document—on Kubernetes. 
It scales smoothly from quick dev tests to full production clusters, making it a solid choice for RAG workloads like FastGPT 
that need several data stores working together.

## Prerequisites

Ensure you have the following environment and tools:

* **`Kubernetes cluster`**:
    * A running Kubernetes cluster is required.
    * For local development and testing, consider using [Minikube](https://minikube.sigs.k8s.io/docs/start/). Minikube can quickly set up a single-node Kubernetes environment on your personal computer.
    * You can also use any standard Kubernetes cluster, such as those provided by cloud service providers (AWS EKS, Google GKE, Azure AKS) or self-built clusters.

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
   Open the `00-config.sh` file. Based on your requirements, set the variable to `true` for the databases you want to install. For example, to install PostgreSQL and Redis:

   ```bash
   ENABLE_POSTGRESQL=true
   ENABLE_REDIS=true
   ENABLE_ELASTICSEARCH=false # Set to true or false as needed
   ENABLE_QDRANT=false      # Set to true or false as needed
   ENABLE_MONGODB=false     # Set to true or false as needed
   ENABLE_NEO4J=false       # Set to true or false as needed
   ```

2. **Prepare Environment and Install KubeBlocks Addons**:
   Execute the script to add the Helm repository and install KubeBlocks Addons for the selected databases.
    TODO：explain 01-prepare.sh do the precheck job and installs some resources that kubeblocks need

   ```bash
   bash ./01-prepare.sh
   ```

3. **(Optional) Customize Database Configuration**:
   Before executing the installation script, you can modify the `values.yaml` file in each database directory to adjust specific configurations for the database cluster, such as version, CPU, memory, storage space, etc. For example, to modify the storage size for PostgreSQL, edit the `postgresql/values.yaml` file.

4. **Install Database Clusters**:
   Execute the script to deploy the database clusters.
TODO：explain 02-install-database.sh actually deploy database in kubernetes

   ```bash
   bash ./02-install-database.sh
   ```
   After the script completes, it will prompt you on how to check the status of installed clusters:
   ```bash
   kubectl get clusters -n rag
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