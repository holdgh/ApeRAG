# Using KubeBlocks to Deploy and Manage Databases

Learn how to quickly deploy and manage various databases in a Kubernetes (K8s) environment through KubeBlocks.

## Introduction to KubeBlocks

KubeBlocks is a production-ready, open-source toolkit that runs any database—SQL, NoSQL, vector, or document—on Kubernetes.  
It scales smoothly from quick dev tests to full production clusters, making it a solid choice for RAG workloads like FastGPT that need several data stores working together.

## Prerequisites

Make sure the following tools are installed and configured:

* **Kubernetes cluster**  
  * A running Kubernetes cluster is required.  
  * For local development or demos you can use [Minikube](https://minikube.sigs.k8s.io/docs/start/) (needs ≥ 2 CPUs, ≥ 2 GB RAM, and Docker/VM-driver support).  
  * Any standard cloud or on-premises Kubernetes cluster (EKS, GKE, AKS, etc.) also works.

* **kubectl**  
  * The Kubernetes command-line interface.  
  * Follow the official guide: [Install and Set Up kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl).

* **Helm**  
  * Kubernetes package manager used by the scripts below.  
  * Install it via the official instructions: [Installing Helm](https://helm.sh/docs/intro/install/).

## Quick Start

### Deployment Steps

1. **Configure the databases you want**  
    Edit `00-config.sh` file. Based on your requirements, set the variable to `true` for the databases you want to install. 
    For example, to install PostgreSQL and Neo4j:

   ```bash
   ENABLE_POSTGRESQL=true
   ENABLE_REDIS=false
   ENABLE_ELASTICSEARCH=false
   ENABLE_QDRANT=false
   ENABLE_MONGODB=false
   ENABLE_NEO4J=true
   ```

2. **Prepare the environment and install KubeBlocks add-ons**

   ```bash
   bash ./01-prepare.sh
   ```

   *What the script does*  
   `01-prepare.sh` performs basic pre-checks (Helm, kubectl, cluster reachability), adds the KubeBlocks Helm repo, and installs any core CRDs or controllers that KubeBlocks itself needs. It also installs the addons for every database you enabled in `00-config.sh`, but **does not** create the actual database clusters yet.

3. **(Optional) Modify database settings**  
   Before deployment you can edit the `values.yaml` file inside each `<db>/` directory to change `version`, `replicas`, `CPU`, `memory`, `storage size`, etc.

4. **Install the database clusters**

```bash
bash ./02-install-database.sh
```

*What the script does*  
`02-install-database.sh` **actually deploys the chosen databases to Kubernetes**.

When the script completes, confirm that the clusters are up:
```bash
kubectl get clusters -n rag
```

### Uninstalling

1. **Remove the database clusters**

   ```bash
   bash ./03-uninstall-database.sh
   ```

   The script deletes the database clusters that were enabled in `00-config.sh`.

2. **Clean up KubeBlocks add-ons**

   ```bash
   bash ./04-cleanup.sh
   ```

   This removes the addons installed by `01-prepare.sh`.
