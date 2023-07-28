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

QDRANT_CLUSTERDEFINTION_SCHEMA = '''apiVersion: apps.kubeblocks.io/v1alpha1
kind: ClusterDefinition
metadata:
  name: qdrant
  labels:
    helm.sh/chart: qdrant-0.6.0-alpha.36
    app.kubernetes.io/name: qdrant
    app.kubernetes.io/instance: release-name
    app.kubernetes.io/version: "1.1.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: qdrant
  connectionCredential:
    username: root
    password: "$(RANDOM_PASSWD)"
    endpoint: "$(SVC_FQDN):$(SVC_PORT_tcp-qdrant)"
    host: "$(SVC_FQDN)"
    port: "$(SVC_PORT_tcp-qdrant)"
  componentDefs:
    - name: qdrant
      workloadType: Stateful
      characterType: qdrant
      probes:
      monitor:
        builtIn: false
        exporterConfig:
          scrapePath: /metrics
          scrapePort: 6333
      logConfigs:
      scriptSpecs:
      - name: qdrant-scripts
        templateRef: qdrant-scripts
        namespace: default
        volumeName: scripts
        defaultMode: 493
      configSpecs:
        - name: qdrant-config-template
          templateRef: qdrant-config-template
          volumeName: qdrant-config
          namespace: default
      service:
        ports:
          - name: tcp-qdrant
            port: 6333
            targetPort: tcp-qdrant
          - name: grpc-qdrant
            port: 6334
            targetPort: grpc-qdrant
      volumeTypes:
        - name: data
          type: data
      podSpec:
        securityContext:
          fsGroup: 1001
        initContainers:
        - name: qdrant-tools
          command:
          - /bin/sh
          - -c
          - |
            cp /bin/jq /qdrant/tools/jq
            cp /bin/curl /qdrant/tools/curl
          imagePullPolicy: IfNotPresent
          terminationMessagePath: /dev/termination-log
          terminationMessagePolicy: File
          volumeMounts:
          - mountPath: /qdrant/tools
            name: tools
        containers:
          - name: qdrant
            imagePullPolicy: IfNotPresent
            securityContext:
              runAsUser: 0
            livenessProbe:
              failureThreshold: 3
              httpGet:
                path: /
                port: tcp-qdrant
                scheme: HTTP
              periodSeconds: 15
              successThreshold: 1
              timeoutSeconds: 10
            readinessProbe:
              exec:
                command:
                - /bin/sh
                - -c
                - |
                  consensus_status=`/qdrant/tools/curl -s http://localhost:6333/cluster | /qdrant/tools/jq -r .result.consensus_thread_status.consensus_thread_status`
                  if [ "$consensus_status" != "working" ]; then
                    echo "consensus stopped"
                    exit 1
                  fi
              failureThreshold: 2
              initialDelaySeconds: 5
              periodSeconds: 15
              successThreshold: 1
              timeoutSeconds: 3
            startupProbe:
              failureThreshold: 18
              httpGet:
                path: /
                port: tcp-qdrant
                scheme: HTTP
              periodSeconds: 10
              successThreshold: 1
              timeoutSeconds: 3
            lifecycle:
              preStop:
                exec:
                  command: ["/qdrant/scripts/pre-stop.sh"]
            terminationMessagePath: /dev/termination-log
            terminationMessagePolicy: File
            volumeMounts:
              - mountPath: /qdrant/config/
                name: qdrant-config
              - mountPath: /qdrant/storage
                name: data
              - mountPath: /qdrant/scripts
                name: scripts
              - mountPath: /etc/annotations
                name: annotations
              - mountPath: /qdrant/tools
                name: tools
            dnsPolicy: ClusterFirst
            enableServiceLinks: true
            ports:
              - name: tcp-qdrant
                containerPort: 6333
              - name: grpc-qdrant
                containerPort: 6334
              - name: tcp-metrics
                containerPort: 9091
              - name: p2p
                containerPort: 6335
            command: ["/bin/sh", "-c"]
            args: ["/qdrant/scripts/setup.sh"]
            env:
            - name: QDRANT__TELEMETRY_DISABLED
              value: "true"
        volumes:
        - name: annotations
          downwardAPI:
            items:
            - path: "component-replicas"
              fieldRef:
                fieldPath: metadata.annotations['apps.kubeblocks.io/component-replicas']
        - emptyDir: {}
          name: tools'''

DEFAULT_TEXT_TO_CD_TMPL = (
    "Given an input question, generate the answer in YAML format."
    "The cluster definition YAML is a dialect in YAML format. "
    "A cluster definition YAML has fixed schema, or specification."
    "Cluster definition declares the components of a database cluster instance."
    "Each component has a definition in componentDef spec. "
    "The major part of a component definition is k8s podSpec. \n"
    "Here we give an example of generating a cluster definition YAML: "
    "Question: Generate a qdrant cluster definition for me, "
    "the fields in the spec can be the default values of qdrant."
    "Answer: the qdrant clusterdefinition YAML is {schema_qdrant}\n"
    "Use the following format:\n"
    "Question: Question here\n"
    "Answer: Final answer here\n"
    "Question: {query_str}\n"
    "Answer: "
)

TEXT_TO_CD_PROMPT = Prompt(
    DEFAULT_TEXT_TO_CD_TMPL,
    stop_token="\nResult:",
    prompt_type="text_to_cd",
)


class Text2CD(KubeBlocks):
    def __init__(self,
                 chat_type: Optional[str] = "text2cd",
                 llm: Optional[BaseLLM] = None,
                 ):
        super().__init__(chat_type, llm)

    # todo：split cd into many parts,
    def predict(self, query):
        response, _ = self.llm_predict.predict(
            prompt=TEXT_TO_CD_PROMPT,
            query_str=query,
            schema_qdrant=QDRANT_CLUSTERDEFINTION_SCHEMA,
        )
        return response


