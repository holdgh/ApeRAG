# KubeBlocks Databases Helm Chart

This Helm chart deploys and manages multiple database clusters (PostgreSQL, Redis, Elasticsearch, Qdrant) using [KubeBlocks](https://kubeblocks.io/).

## Prerequisites

*   Kubernetes cluster (version compatible with KubeBlocks)
*   [Helm](https://helm.sh/docs/intro/install/) (version 3+) installed.
*   [KubeBlocks](https://kubeblocks.io/docs/preview/user_docs/installation) installed in your Kubernetes cluster.
*   `kubectl` configured to interact with your cluster.

## Chart Structure

```
kubeblocks-databases/
├── Chart.yaml          # Information about the chart
├── values.yaml         # Default configuration values
├── README.md           # This file
├── NOTES.txt           # Post-installation notes
└── templates/          # Directory containing template files
    ├── postgresql-cluster.yaml
    ├── redis-cluster.yaml
    ├── elasticsearch-cluster.yaml
    └── qdrant-cluster.yaml
```

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

1.  **Navigate to the chart directory:**
    If this chart is in a local directory named `kubeblocks-databases`:
    ```bash
    cd path/to/kubeblocks-databases
    ```

2.  **Customize `values.yaml` (Optional):**
    Modify `kubeblocks-databases/values.yaml` to suit your needs (e.g., change versions, resource allocations, enable/disable specific databases).
    Alternatively, you can override values using the `--set` flag during installation or by providing a custom values file with `-f my-values.yaml`.

3.  **Install the chart:**
    ```bash
    helm install <release-name> ./kubeblocks-databases -n <namespace-from-values-yaml> --create-namespace
    ```
    Replace `<release-name>` with a name for your Helm release (e.g., `my-kb-dbs`).
    Replace `<namespace-from-values-yaml>` with the namespace specified in `global.namespace` in your `values.yaml` (e.g., `demo`). The `--create-namespace` flag will create the namespace if it doesn't exist.

    Example:
    ```bash
    helm install kb-databases ./kubeblocks-databases -n demo --create-namespace
    ```

## Verification

After installation, you can check the status of the deployed KubeBlocks clusters:

```bash
kubectl get clusters -n <namespace-from-values-yaml>
kubectl get pods -n <namespace-from-values-yaml>
```

Example:
```bash
kubectl get clusters -n demo
kubectl get pods -n demo
```

You should see the `Cluster` resources for the enabled databases and their corresponding pods. The `NOTES.txt` output from Helm will also provide some of this information.

## Usage Examples

### Deploying only PostgreSQL and Redis

Modify `values.yaml`:
```yaml
# ...
postgresql:
  enabled: true
  # ... other pg settings
redis:
  enabled: true
  topology: standalone # Or replication, as needed
  # ... other redis settings
elasticsearch:
  enabled: false # Disable Elasticsearch
  # ...
qdrant:
  enabled: false # Disable Qdrant
  # ...
```
Then run `helm upgrade` or `helm install` as appropriate.

### Changing PostgreSQL Resources

Modify `values.yaml`:
```yaml
postgresql:
  enabled: true
  name: "pg-cluster"
  # ...
  resources:
    limits:
      cpu: "1"
      memory: "2Gi"
    requests:
      cpu: "1"
      memory: "2Gi"
  storage: "50Gi"
  # ...
```
Then apply the changes:
```bash
helm upgrade <release-name> ./kubeblocks-databases -n <namespace-from-values-yaml>
```
Example:
```bash
helm upgrade kb-databases ./kubeblocks-databases -n demo
```

## Uninstallation

To uninstall the deployed database clusters:

```bash
helm uninstall <release-name> -n <namespace-from-values-yaml>
```
Example:
```bash
helm uninstall kb-databases -n demo
```
This will remove all Kubernetes resources associated with this Helm release, including the KubeBlocks `Cluster` objects. Depending on the `terminationPolicy` and KubeBlocks behavior, PVCs might also be deleted.

## Notes

*   Ensure the KubeBlocks operator and the required `ClusterDefinition` CRDs (e.g., for postgresql, redis, elasticsearch, qdrant) are installed and available in your Kubernetes cluster before deploying this chart.
*   The `storageClassName` for PersistentVolumeClaims is currently set to `""` (empty string) in the templates, which typically means the default storage class in your Kubernetes cluster will be used. If you need to specify a particular storage class, you may need to modify the templates or add a configuration option to `values.yaml` for each database's `volumeClaimTemplates.spec`.
