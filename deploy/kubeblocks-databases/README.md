# KubeBlocks Databases Helm Chart

This Helm chart deploys and manages multiple database clusters (PostgreSQL, Redis, Elasticsearch, Qdrant) using [KubeBlocks](https://kubeblocks.io/).

## Prerequisites

*   Kubernetes cluster (version compatible with KubeBlocks)
*   [Helm](https://helm.sh/docs/intro/install/) (version 3+) installed.
*   [KubeBlocks](https://kubeblocks.io/docs/preview/user_docs/installation) installed in your Kubernetes cluster.
*   `kubectl` configured to interact with your cluster.


## Configuration

The primary way to configure the deployments is through the `values.yaml` file.

### Global Settings

These settings apply to all database clusters deployed by this chart:

```yaml
global:
  namespace: "demo"
  terminationPolicy: "Delete" # Options: DoNotTerminate, Delete, WipeOut
```

### Per-Database Settings

Each database (PostgreSQL, Redis, Elasticsearch, Qdrant) has its own configuration block. Here's an example for PostgreSQL:

```yaml
postgresql:
  enabled: true              # Set to true to deploy this database, false to skip
  name: "pg-cluster"         # Name of the KubeBlocks Cluster resource
  serviceVersion: "14.7.2"   # Database engine version
  disableExporter: false     # true to disable metrics exporter, false to enable
  replicas: 2                # Number of replicas for the main component
  resources:                 # CPU and Memory requests/limits
    limits:
      cpu: "0.5"
      memory: "0.5Gi"
    requests:
      cpu: "0.5"
      memory: "0.5Gi"
  storage: "20Gi"            # Storage size for the data volume (e.g., PVC)
```

Refer to `values.yaml` for the full set of configurable options for each database.

**Key configurable parameters for each database:**

*   `enabled`: (boolean) Deploy this database cluster.
*   `name`: (string) Name for the KubeBlocks `Cluster` resource.
*   `serviceVersion`: (string) Specific version of the database engine.
*   `disableExporter`: (boolean) Enable/disable the metrics exporter. (Note: For Elasticsearch, this might be handled differently by its `componentDef`).
*   `replicas`: (integer) Number of replicas for the primary database component.
*   `resources`: (object) Standard Kubernetes resource requests and limits.
*   `storage`: (string) Storage capacity for persistent volumes (e.g., "10Gi", "100Gi").
*   `topology`: (string, for Redis) e.g., "standalone", "replication".
*   `componentDef`: (string, for Elasticsearch) e.g., "elasticsearch-8".


## Installation

```bash
helm repo add kubeblocks https://apecloud.github.io/helm-charts
helm repo update

helm upgrade --install kb-addon-elasticsearch kubeblocks/elasticsearch --namespace kb-system --version 1.0.0-alpha.0
helm upgrade --install kb-addon-qdrant kubeblocks/qdrant --namespace kb-system --version 1.0.0-alpha.0
helm upgrade --install kb-addon-postgresql kubeblocks/postgresql --namespace kb-system --version 1.0.0-alpha.0
helm upgrade --install kb-addon-redis kubeblocks/redis --namespace kb-system --version 1.0.0-alpha.0
```

```bash
helm install kb-databases ./kubeblocks-databases -n demo --create-namespace
```

## Verification

After installation, you can check the status of the deployed KubeBlocks clusters:

```bash
kubectl get clusters -n demo
kubectl get pods -n demo
```


You should see the `Cluster` resources for the enabled databases and their corresponding pods. The `NOTES.txt` output from Helm will also provide some of this information.

```bash
kubectl get clusters -n demo
NAME               CLUSTER-DEFINITION   TERMINATION-POLICY   STATUS     AGE
es-cluster                              Delete               Running    121m
pg-cluster         postgresql           Delete               Creating   121m
qdrant-cluster     qdrant               Delete               Running    121m
redis-standalone   redis                Delete               Running    121m

kubectl get pods -n demo
NAME                       READY   STATUS    RESTARTS   AGE
es-cluster-mdit-0          3/3     Running   0          110m
pg-cluster-postgresql-0    5/5     Running   0          121m
qdrant-cluster-qdrant-0    2/2     Running   0          117m
redis-standalone-redis-0   3/3     Running   0          121m
```

## Uninstallation

To uninstall the deployed database clusters:

```bash
helm uninstall kb-databases -n demo
```
This will remove all Kubernetes resources associated with this Helm release, including the KubeBlocks `Cluster` objects. Depending on the `terminationPolicy` and KubeBlocks behavior, PVCs might also be deleted.
