import json
import logging
from typing import Dict, Any

from kubechat.models import Collection, Document, DocumentStatus
from kubechat.source.base import Source
from kubechat.source.utils import gen_temporary_file, FeishuClient, Feishu2Markdown


logger = logging.getLogger(__name__)


class FeishuSource(Source):
    def __init__(self, collection: Collection, ctx: Dict[str, Any]):
        super().__init__(ctx)
        self.client = FeishuClient(ctx)
        self.space_id = ctx.get("space_id", "")
        self.node_id = ctx.get("node_id", "")
        self.collection = collection

    def get_node_documents(self, space_id, node_token):
        documents = []
        node_mapping = {}

        # find parent titles from bottom to top
        def get_parent_titles(current_node):
            result = []
            while True:
                parent_node = node_mapping.get(current_node["parent_node_token"], None)
                if not parent_node:
                    break
                result.insert(0, parent_node["title"])
                current_node = parent_node
            return result

        root_node = self.client.get_node(node_token)
        # iterate the nodes in the BFS(Breadth First Search) way
        nodes = [root_node]
        for node in nodes:
            node_token = node["node_token"]
            node_mapping[node_token] = node
            if node["has_child"]:
                nodes.extend(self.client.get_space_nodes(space_id, node_token))

            metadata = node.copy()
            metadata["titles"] = get_parent_titles(node)
            match node["obj_type"]:
                case "docx":
                    suffix = "md"
                case "doc":
                    suffix = "txt"
                case _:
                    logger.info("ignore unsupported node: %s", node["title"])
                    continue
            doc = Document(
                user=self.collection.user,
                name=node["title"] + f".{suffix}",
                status=DocumentStatus.PENDING,
                collection=self.collection,
                metadata=json.dumps(metadata),
                size=0,
            )
            documents.append(doc)
        return documents

    def scan_documents(self):
        return self.get_node_documents(self.space_id, self.node_id)

    def prepare_document(self, doc: Document):
        node = json.loads(doc.metadata)
        node_id = node["obj_token"]
        match node["obj_type"]:
            case "docx":
                blocks = self.client.get_docx_blocks(node_id)
                content = Feishu2Markdown(node_id, blocks).gen()
            case "doc":
                content = self.client.get_old_doc_plain_content(node_id)
            case _:
                raise Exception(f"unsupported node type: {node['obj_type']}")

        temp_file = gen_temporary_file(doc.name)
        temp_file.write(content.encode("utf-8"))
        temp_file.close()

        metadata = {}
        if node["titles"]:
            titles = " ".join(node["titles"])
            metadata = {
                "PARENT TITLES": titles
            }
        self.prepare_metadata_file(temp_file.name, doc, metadata)

        return temp_file.name

    def close(self):
        pass

    def sync_enabled(self):
        return True
