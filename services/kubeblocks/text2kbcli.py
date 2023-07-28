import asyncio
import json
import logging
import os

from typing import Optional, List

from langchain.llms.base import BaseLLM
from llama_index import Prompt
import config.settings as settings
from query.query import QueryWithEmbedding
from readers.base_embedding import get_default_embedding_model
from readers.local_path_embedding import LocalPathEmbedding
from vectorstore.connector import VectorStoreConnectorAdaptor

from services.kubeblocks.base import KubeBlocks

logger = logging.getLogger(__name__)

KBCLI_ADDON_DESCRIBE_SCHEMA = '''
kbcli addon describe mongodb
the command can describe an addon specification.
'''

KBCLI_ADDON_DESCRIBE_DOC = '''

Addon command.

* [kbcli addon describe](kbcli_addon_describe.md)	 - Describe an addon specification.
* [kbcli addon disable](kbcli_addon_disable.md)	 - Disable an addon.
* [kbcli addon enable](kbcli_addon_enable.md)	 - Enable an addon.
* [kbcli addon list](kbcli_addon_list.md)	 - List addons.


---
title: kbcli addon describe
---

Describe an addon specification.

```
kbcli addon describe ADDON_NAME [flags]
```

### Options

```
  -h, --help   help for describe
```

### Options inherited from parent commands

```
      --as string                      Username to impersonate for the operation. User could be a regular user or a service account in a namespace.
      --as-group stringArray           Group to impersonate for the operation, this flag can be repeated to specify multiple groups.
      --as-uid string                  UID to impersonate for the operation.
      --cache-dir string               Default cache directory (default "$HOME/.kube/cache")
      --certificate-authority string   Path to a cert file for the certificate authority

'''

DEFAULT_TEXT_TO_KBCLI_TMPL = (
    "Given an input action, generate the answer in kbcli format, and add some explanations"
    "kbcli is a command line interface (CLI) tool for KubeBlocks."
    "KubeBlocks is an open-source, cloud-native data infrastructure designed to help application developers and "
    "platform engineers manage database and analytical workloads on Kubernetes."
    "Be careful to only use the command options and arguments that are relevant for the task at hand. Pay attention "
    "to the order in which the options and arguments should be passed in the command. If you are not sure about the "
    "command syntax, analyse the input example and imitate the example. Note that the second word of the command can "
    "only be the following words: addon, alert, bench, builder, class, cluster, clusterdefinition, clusterversion, "
    "dashboard, fault, infra, kubeblocks, migration, options, playground, plugin, report, version."
    "Here we give a examples of generating a kbcli: "
    "Question: generate a kbcli command to describe an addon specification, the name of the addon is mongodb.\n"
    "related documents: {doc_addon_describe}\n"
    "Answer: the kbcli is {answer_addon_describe}\n"
    "Use the following format:\n"
    "Question: Question here\n"
    "related documents: Documents here\n"
    "Answer: Final answer here\n"
    "Question: {query_str}\n"
    "related documents: {doc_about_query}\n"
    "Answer: "
)

TEXT_TO_CLUSTER_PROMPT = Prompt(
    DEFAULT_TEXT_TO_KBCLI_TMPL,
    stop_token="\nResult:",
    prompt_type="text_to_cluster",
)


# get all filenames end with ".md"
def list_markdown_files(directory: str):
    markdown_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                markdown_files.append(os.path.join(root, file))
    return markdown_files


# store files to one specific collection in default vector db
def inflate_doc(file_paths: List[str], collection_id: str):
    vectordb_ctx = json.loads(settings.VECTOR_DB_CONTEXT)
    vector_db_collection_id = collection_id
    vectordb_ctx["collection"] = vector_db_collection_id
    adaptor = VectorStoreConnectorAdaptor(settings.VECTOR_DB_TYPE, vectordb_ctx)
    for file_path in file_paths:
        try:
            loader = LocalPathEmbedding(input_files=[file_path],
                                        vector_store_adaptor=adaptor,
                                        )
            loader.load_data()
        except Exception as e:
            logger.error(f"text2kbcli add kbcli doc {file_path} to vector db error:{e}")
            return False
    return True


class Text2KBCLI(KubeBlocks):
    def __init__(self,
                 chat_type: Optional[str] = "text2kbcli",
                 llm: Optional[BaseLLM] = None,
                 ):
        super().__init__(chat_type, llm)
        self.embedding_model, self.vector_size = get_default_embedding_model()

    def predict(self, query):
        vectordb_ctx = json.loads(settings.VECTOR_DB_CONTEXT)
        vector_db_collection_id = "text2kbcli"
        vectordb_ctx["collection"] = vector_db_collection_id
        adaptor = VectorStoreConnectorAdaptor(settings.VECTOR_DB_TYPE, vectordb_ctx)
        query_vector = self.embedding_model.get_text_embedding(query)
        query_embedding = QueryWithEmbedding(query=query, top_k=3, embedding=query_vector)

        results = adaptor.connector.search(
            query_embedding,
            collection_name=vector_db_collection_id,
            query_vector=query_embedding.embedding,
            with_vectors=True,
            limit=query_embedding.top_k,
            consistency="majority",
            search_params={"hnsw_ef": 128, "exact": False},
            score_threshold=0.5,
        )

        answer_text = results.get_packed_answer(2000)
        response, _ = self.llm_predict.predict(
            prompt=TEXT_TO_CLUSTER_PROMPT,
            doc_addon_describe=KBCLI_ADDON_DESCRIBE_DOC,
            answer_addon_describe=KBCLI_ADDON_DESCRIBE_SCHEMA,
            doc_about_query=answer_text,
            query_str=query,
        )
        return response


# initialize：store kbcli documents to collections named "text2kbcli" in vector db
# if __name__ == "__main__":
    # kbcli_md = "/Users/lyf/kubeblocks/docs/user_docs/cli/"
    # kbcli_md_list = list_markdown_files(directory=kbcli_md)
    # h=inflate_doc(file_paths=kbcli_md_list, collection_id="text2kbcli")
    # print(h)


