#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Load configuration file
source "$SCRIPT_DIR/00-config.sh"

# Check dependencies
echo "Checking dependencies..."
command -v kubectl >/dev/null 2>&1 || { echo "Error: kubectl command not found"; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "Error: helm command not found"; exit 1; }

echo "Checking if Kubernetes is available..."
if ! kubectl cluster-info &>/dev/null; then
    echo "Error: Kubernetes cluster is not accessible. Please ensure you have proper access to a Kubernetes cluster."
    exit 1
fi
echo "Kubernetes cluster is accessible."

echo "Checking if KubeBlocks is already installed in kb-system namespace..."
if kubectl get namespace kb-system &>/dev/null &&
   kubectl get deployment -n kb-system &>/dev/null; then
    echo "KubeBlocks is already installed in kb-system namespace."
    exit 0
fi

# Function for installing KubeBlocks
install_kubeblocks() {
    echo "Ready to install KubeBlocks."

    # Install CSI Snapshotter CRDs
    kubectl create -f https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/v8.2.0/client/config/crd/snapshot.storage.k8s.io_volumesnapshotclasses.yaml
    kubectl create -f https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/v8.2.0/client/config/crd/snapshot.storage.k8s.io_volumesnapshots.yaml
    kubectl create -f https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/v8.2.0/client/config/crd/snapshot.storage.k8s.io_volumesnapshotcontents.yaml

    # Add and update Piraeus repository
    helm repo add piraeus-charts https://piraeus.io/helm-charts/
    helm repo update

    # Install snapshot controller
    helm install snapshot-controller piraeus-charts/snapshot-controller -n kb-system --create-namespace

    # Install KubeBlocks CRDs
    kubectl create -f https://github.com/apecloud/kubeblocks/releases/download/v${KB_VERSION}/kubeblocks_crds.yaml

    # Add and update KubeBlocks repository
    helm repo add kubeblocks $HELM_REPO
    helm repo update

    # Install KubeBlocks
    helm install kubeblocks kubeblocks/kubeblocks --namespace kb-system --create-namespace --version=${KB_VERSION}

    # Verify installation
    echo "Waiting for KubeBlocks to be ready..."
    kubectl wait --for=condition=ready pods -l app=snapshot-controller -n kb-system --timeout=120s
    kubectl wait --for=condition=ready pods -l app.kubernetes.io/instance=kubeblocks -n kb-system --timeout=300s
    echo "KubeBlocks installation complete!"
}

# Call the function to install KubeBlocks
install_kubeblocks