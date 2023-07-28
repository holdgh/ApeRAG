import asyncio
import json
import logging

from typing import Optional

from langchain import OpenAI
from langchain.llms.base import BaseLLM
from llama_index import Prompt
from llama_index.langchain_helpers.chain_wrapper import LLMPredictor

from services.kubeblocks.base import KubeBlocks

logger = logging.getLogger(__name__)

QDRANT_CLUSTER_SCHEMA = '''
apiVersion: apps.kubeblocks.io/v1alpha1
kind: Cluster
metadata:
  name: release-name-qdrant-cluster
  labels: 
    helm.sh/chart: qdrant-cluster-0.6.0-alpha.36
    app.kubernetes.io/name: qdrant-cluster
    app.kubernetes.io/instance: release-name
    app.kubernetes.io/version: "1.1.0"
    app.kubernetes.io/managed-by: Helm
spec:
  clusterDefinitionRef: qdrant # ref clusterdefinition.name
  clusterVersionRef: qdrant-1.1.0 # ref clusterversion.name
  terminationPolicy: Delete
  affinity:
  componentSpecs:
    - name: qdrant # user-defined
      componentDefRef: qdrant # ref clusterdefinition components.name
      monitor: false
      replicas: 1
      volumeClaimTemplates:
        - name: data # ref clusterdefinition components.containers.volumeMounts.name
          spec:
            storageClassName: 
            accessModes:
              - ReadWriteOnce
            resources:
              requests:
                storage: 10Gi
    '''

REDIS_CLUSTER_SCHEMA = '''
apiVersion: apps.kubeblocks.io/v1alpha1
kind: Cluster
metadata:
  name: release-name
  namespace: default
  labels: 
    helm.sh/chart: redis-cluster-0.6.0-alpha.36
    app.kubernetes.io/version: "7.0.6"
    app.kubernetes.io/instance: release-name
spec:
  clusterVersionRef: redis-7.0.6
  terminationPolicy: Delete  
  affinity:
    podAntiAffinity: Preferred
    topologyKeys:
      - kubernetes.io/hostname
    tenancy: SharedNode
  clusterDefinitionRef: redis  # ref clusterDefinition.name
  componentSpecs:
    - name: redis
      componentDefRef: redis # ref clusterDefinition componentDefs.name      
      monitor: false      
      replicas: 1
      enabledLogs:
        - running
      serviceAccountName: kb-release-name
      switchPolicy:
        type: Noop      
      resources:
        limits:
          cpu: "0.5"
          memory: "0.5Gi"
        requests:
          cpu: "0.5"
          memory: "0.5Gi"      
      volumeClaimTemplates:
        - name: data # ref clusterDefinition components.containers.volumeMounts.name
          spec:
            accessModes:
              - ReadWriteOnce
            resources:
              requests:
                storage: 20Gi      
      services:

'''

DEFAULT_TEXT_TO_CLUSTER_TMPL = (
    "Given an input question, generate the answer in YAML format."
    "The cluster YAML is a dialect in YAML format. "
    "A cluster YAML has fixed schema, or specification."
    "Cluster YAML declares the deployment state of a database cluster."
    "Each componentDef has some attributes. "
    "Here we give 2 examples of generating a cluster YAML: "
    "Question: Generate a qdrant cluster YAML for me, "
    "the fields in the spec can be the default values of qdrant."
    "Answer: the qdrant cluster YAML is {schema_redis}\n"
    "Question: Generate a redis cluster YAML for me, "
    "the fields in the spec can be the default values of redis."
    "Answer: the redis cluster YAML is {schema_qdrant}\n"
    "Use the following format:\n"
    "Question: Question here\n"
    "Answer: Final answer here\n"
    "Question: {query_str}\n"
    "Answer: "
)

TEXT_TO_CLUSTER_PROMPT = Prompt(
    DEFAULT_TEXT_TO_CLUSTER_TMPL,
    stop_token="\nResult:",
    prompt_type="text_to_cluster",
)


class Text2CLUSTER(KubeBlocks):
    def __init__(self,
                 chat_type: Optional[str] = "text2cluster",
                 llm: Optional[BaseLLM] = None,
                 ):
        super().__init__(chat_type, llm)

    def predict(self, query):
        response, _ = self.llm_predict.predict(
            prompt=TEXT_TO_CLUSTER_PROMPT,
            query_str=query,
            schema_qdrant=QDRANT_CLUSTER_SCHEMA,
            schema_redis=REDIS_CLUSTER_SCHEMA,
        )
        return response


