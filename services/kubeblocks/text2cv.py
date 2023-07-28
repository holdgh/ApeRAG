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

QDRANT_CLUSTERVERSION_SCHEMA = '''
apiVersion: apps.kubeblocks.io/v1alpha1
kind: ClusterVersion
metadata:
  name: qdrant-1.1.0
  labels:
    helm.sh/chart: qdrant-0.6.0-alpha.36
    app.kubernetes.io/name: qdrant
    app.kubernetes.io/instance: release-name
    app.kubernetes.io/version: "1.1.0"
    app.kubernetes.io/managed-by: Helm
spec:
  clusterDefinitionRef: qdrant
  componentVersions:
    - componentDefRef: qdrant
      versionsContext:
        initContainers:
        - name: qdrant-tools
          image: docker.io/apecloud/curl-jq:latest
        containers:
          - name: qdrant
            image:  docker.io/qdrant/qdrant:latest
'''
REDIS_CLUSTERVERSION_SCHEMA = '''
apiVersion: apps.kubeblocks.io/v1alpha1
kind: ClusterVersion
metadata:
  name: redis-7.0.6
  labels:
    helm.sh/chart: redis-0.6.0-alpha.36
    app.kubernetes.io/name: redis
    app.kubernetes.io/instance: release-name
    app.kubernetes.io/version: "7.0.6"
    app.kubernetes.io/managed-by: Helm
spec:
  clusterDefinitionRef: redis
  componentVersions:
  - componentDefRef: redis
    versionsContext:
      containers:
      - name: redis
        image: registry.cn-hangzhou.aliyuncs.com/apecloud/redis-stack-server:7.0.6-RC8
        imagePullPolicy: IfNotPresent
    systemAccountSpec:
      cmdExecutorConfig:
        image: registry.cn-hangzhou.aliyuncs.com/apecloud/redis-stack-server:7.0.6-RC8
  - componentDefRef: redis-sentinel
    versionsContext:
      initContainers:
        - name: init-redis-sentinel
          image: registry.cn-hangzhou.aliyuncs.com/apecloud/redis-stack-server:7.0.6-RC8
          imagePullPolicy: IfNotPresent
      containers:
        - name: redis-sentinel
          image: registry.cn-hangzhou.aliyuncs.com/apecloud/redis-stack-server:7.0.6-RC8
          imagePullPolicy: IfNotPresent
'''

DEFAULT_TEXT_TO_CV_TMPL = (
    "Given an input question, generate the answer in YAML format."
    "The cluster version YAML is a dialect in YAML format. "
    "A cluster version YAML has fixed schema, or specification."
    "cluster version declares the versions of image components in a database cluster instance."
    "The major part of a component version is k8s componentVersions. \n"
    "Here we give 2 examples of generating a cluster version YAML: "
    "Question: Generate a qdrant cluster version for me, "
    "the fields in the spec can be the default values of qdrant."
    "Answer: the qdrant cluster version YAML is {schema_qdrant}\n"
    "Question: Generate a redis cluster version for me, "
    "the fields in the spec can be the default values of redis."
    "Answer: the redis cluster version YAML is {schema_redis}\n"
    "Use the following format:\n"
    "Question: Question here\n"
    "Answer: Final answer here\n"
    "Question: {query_str}\n"
    "Answer: "
)

TEXT_TO_CV_PROMPT = Prompt(
    DEFAULT_TEXT_TO_CV_TMPL,
    stop_token="\nResult:",
    prompt_type="text_to_cv",
)


class Text2CV(KubeBlocks):
    def __init__(self,
                 chat_type: Optional[str] = "text2cv",
                 llm: Optional[BaseLLM] = None,
                 ):
        super().__init__(chat_type, llm)

    def predict(self, query):
        response, _ = self.llm_predict.predict(
            prompt=TEXT_TO_CV_PROMPT,
            query_str=query,
            schema_qdrant=QDRANT_CLUSTERVERSION_SCHEMA,
            schema_redis=REDIS_CLUSTERVERSION_SCHEMA,
        )
        return response


