import datetime
import io
import json
import logging
import os
from threading import Lock

import pytablewriter
from pydantic import BaseModel
from abc import ABC
from typing import Dict, Any

import requests

from kubechat.source.base import Source
from kubechat.models import Collection, Document, DocumentStatus
from kubechat.source.utils import gen_temporary_file, feishu_lang_code_mapping

logger = logging.getLogger(__name__)


class Space(BaseModel):
    description: str
    name: str
    id: str
    visibility: str


class UserAccessToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    name: str
    en_name: str
    avatar_url: str
    avatar_thumb: str
    avatar_middle: str
    avatar_big: str
    open_id: str
    union_id: str
    email: str
    enterprise_email: str
    user_id: str
    mobile: str
    tenant_key: str
    refresh_expires_in: int
    refresh_token: str
    sid: str


class Feishu2Markdown(ABC):
    def __init__(self, doc_id, blocks):
        self.text = ""
        self.block_map = {}
        self.doc_id = doc_id
        for block in blocks:
            self.block_map[block["block_id"]] = block

    def gen(self):
        self.handle_block(self.block_map[self.doc_id])
        return self.text

    # https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/data-structure/block#e8ce4e8e
    def handle_block(self, block):
        block_type = block["block_type"]
        match block_type:
            case 1:
                # page
                self.text += "# "
                self.parse_block_text(block["page"]["elements"], block.get("children", []))
            case 2:
                # text
                self.parse_block_text(block["text"]["elements"], block.get("children", []))
            case 3:
                # heading 1
                self.text += "# "
                self.parse_block_text(block["heading1"]["elements"], block.get("children", []))
            case 4:
                # heading 2
                self.text += "## "
                self.parse_block_text(block["heading2"]["elements"], block.get("children", []))
            case 5:
                # heading 3
                self.text += "### "
                self.parse_block_text(block["heading3"]["elements"], block.get("children", []))
            case 6:
                # heading 4
                self.text += "#### "
                self.parse_block_text(block["heading4"]["elements"], block.get("children", []))
            case 7:
                # heading 5
                self.text += "##### "
                self.parse_block_text(block["heading5"]["elements"], block.get("children", []))
            case 8:
                # heading 6
                self.text += "###### "
                self.parse_block_text(block["heading6"]["elements"], block.get("children", []))
            case 9:
                # heading 7
                self.text += "####### "
                self.parse_block_text(block["heading7"]["elements"], block.get("children", []))
            case 10:
                # heading 8
                self.text += "######## "
                self.parse_block_text(block["heading8"]["elements"], block.get("children", []))
            case 11:
                # heading 9
                self.text += "######### "
                self.parse_block_text(block["heading9"]["elements"], block.get("children", []))
            case 12:
                # bullet
                self.text += "- "
                self.parse_block_text(block["bullet"]["elements"], block.get("children", []))
                self.text += "\n"
            case 13:
                # ordered list
                # TODO optimize ordered list parsing
                self.text += "1. "
                self.parse_block_text(block["ordered"]["elements"], block.get("children", []))
                self.text += "\n"
            case 14:
                # code
                lang = feishu_lang_code_mapping[block["code"]["style"]["language"]]
                self.text += f"```{lang}\n"
                self.parse_block_text(block["code"]["elements"], block.get("children", []))
                self.text += "\n```\n"
            case 15:
                # quote
                self.text += "> "
                self.parse_block_text(block["quote"]["elements"], block.get("children", []))
            case 22:
                # divider
                self.text += "---\n"
            case 34:
                # quote container
                for child in block.get("children", []):
                    child_block = self.block_map[child]
                    self.text += "> "
                    self.handle_block(child_block)
            case _:
                print(f"Unhandled block type {block_type}")
                print(block)

    def parse_block_text(self, elements, children):
        inline = len(elements) > 1
        for element in elements:
            self.parse_block_text_element(element, inline)
        self.text += "\n"
        for child in children:
            child_block = self.block_map[child]
            self.handle_block(child_block)

    def parse_block_text_element(self, element, inline):
        text_run = element.get("text_run", "")
        if text_run:
            self.text += text_run["content"]

        mention_user = element.get("mention_user", "")
        if mention_user:
            self.text += mention_user["user_id"]

        mention_doc = element.get("mention_doc", "")
        if mention_doc:
            self.text += "[%s](%s)" % (mention_doc.get("title", ""), mention_doc.get("url", ""))

        equation = element.get("equation", "")
        if equation:
            symbol = "$$"
            if inline:
                symbol = "$"
            self.text += "%s%s%s" % (symbol, equation, symbol)

    @staticmethod
    def renderMarkdownTable(data):
        buf = io.StringIO()
        writer = pytablewriter.MarkdownTableWriter()
        writer.stream = buf
        writer.headers = data[0]
        writer.value_matrix = data[1:]
        writer.write_table()
        return buf.getvalue()


class FeishuClient(ABC):
    def __init__(self, ctx: Dict[str, Any]):
        self.app_id = ctx.get("app_id", None)
        if self.app_id is None:
            raise Exception("app_id is required")

        self.app_secret = ctx.get("app_secret")
        if self.app_secret is None:
            raise Exception("app_secret is required")

        self.mutex = Lock()
        self.space_id = ctx.get("space_id")
        self.tenant_access_token = ""
        self.expire_at = datetime.datetime.now()

    def request(self, method, path, **kwargs):
        url = f"https://open.feishu.cn/open-apis/{path}"
        logger.info("request feishu api: %s %s", method, url)
        with self.mutex:
            if self.expire_at - datetime.datetime.now() < datetime.timedelta(minutes=15):
                self.tenant_access_token, self.expire_at = self.get_tenant_access_token()
        headers = {"Authorization": f"Bearer {self.tenant_access_token}"}
        resp = requests.request(method, url, headers=headers, **kwargs)
        if resp.status_code != 200:
            raise Exception(f"request failed: {resp.text}")
        resp = resp.json()
        if resp["code"] != 0:
            raise Exception(f"request failed: {resp['msg']}")
        return resp

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def patch(self, path, **kwargs):
        return self.request("PATCH", path, **kwargs)

    def get_user_access_token(self, code, redirect_uri):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        params = {
            "code": f"{code}",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        resp = requests.post("https://passport.feishu.cn/suite/passport/oauth/token", params=params, headers=headers)
        if resp.status_code != 200:
            raise Exception(f"request failed: {resp.text}")
        resp = resp.json()
        return resp["access_token"]

    def get_tenant_access_token(self):
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }
        resp = requests.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal", json=data)
        if resp.status_code != 200:
            raise Exception(f"request failed: {resp.text}")
        resp = resp.json()
        if resp["code"] != 0:
            raise Exception(f"request failed: {resp['msg']}")
        expired_at = datetime.datetime.now() + datetime.timedelta(seconds=resp["expire"])
        return resp["tenant_access_token"], expired_at

    @staticmethod
    def build_card_data(message):
        content = {
            "config": {
                "wide_screen_mode": True
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": message,
                }
            ]
        }
        return {
            "msg_type": "interactive",
            "content": json.dumps(content),
        }

    def reply_card_message(self, message_id, message):
        data = self.build_card_data(message)
        resp = self.post(f"im/v1/messages/{message_id}/reply", json=data)
        return resp["data"]["message_id"]

    def update_card_message(self, message_id, message):
        data = self.build_card_data(message)
        self.patch(f"im/v1/messages/{message_id}", json=data)

    def send_message(self, chat_id, message):
        params = {"receive_id_type": "chat_id"}
        content = {
            "config": {
                "wide_screen_mode": True
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": message,
                }
            ]
        }
        data = {
            "receive_id": f"{chat_id}",
            "msg_type": "interactive",
            "content": json.dumps(content),
        }
        resp = self.post("im/v1/messages", params=params, json=data)
        return resp["data"]["message_id"]

    def get_spaces(self):
        spaces = []
        resp = self.get("wiki/v2/spaces")
        for item in resp["data"]["items"]:
            spaces.append(Space(
                description=item["description"],
                name=item["name"],
                id=item["space_id"],
                visibility=item["visibility"],
            ))
        return spaces

    def get_space_nodes(self, space_id, parent_node_token=""):
        nodes = []
        page_token = None
        while True:
            params = {
                "parent_node_token": parent_node_token,
                "page_size": 1,
            }
            if page_token is not None:
                params["page_token"] = page_token
            resp = self.get(f"wiki/v2/spaces/{space_id}/nodes", params=params)
            for node in resp["data"]["items"]:
                nodes.append(node)
            if not resp["data"]["has_more"]:
                break
            page_token = resp["data"]["page_token"]
        return nodes

    def get_node(self, token):
        params = {
            "token": token,
        }
        resp = self.get(f"wiki/v2/spaces/get_node", params=params)
        return resp["data"]["node"]

    def get_doc_plain_content(self, doc_id):
        if doc_id is None:
            raise Exception("doc_id is None")
        resp = self.get(f"docx/v1/documents/{doc_id}/raw_content?lang=0")
        return resp["data"]["content"]

    def get_docx_blocks(self, doc_id):
        if doc_id is None:
            raise Exception("doc_id is None")
        resp = self.get(f"docx/v1/documents/{doc_id}/blocks")
        return resp["data"]["items"]


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

            if node["obj_type"] == "docx":
                metadata = node.copy()
                metadata["titles"] = get_parent_titles(node)
                doc = Document(
                    user=self.collection.user,
                    name=node["title"] + ".md",
                    status=DocumentStatus.PENDING,
                    collection=self.collection,
                    metadata=json.dumps(metadata),
                    size=0,
                )
                documents.append(doc)
            else:
                logger.info("ignore unsupported node: %s", node["title"])
        return documents

    def scan_documents(self):
        return self.get_node_documents(self.space_id, self.node_id)

    def prepare_document(self, doc: Document):
        node = json.loads(doc.metadata)
        node_id = node["obj_token"]
        blocks = self.client.get_docx_blocks(node_id)
        content = Feishu2Markdown(node_id, blocks).gen()
        temp_file = gen_temporary_file(doc.name)
        temp_file.write(content.encode("utf-8"))
        temp_file.close()

        metadata = {}
        if node["titles"]:
            titles = " ".join(node["titles"])
            metadata = {
                "PARENT TITLES":  titles
            }
        self.prepare_metadata_file(temp_file.name, doc, metadata)

        return temp_file.name

    def close(self):
        pass

    def sync_enabled(self):
        return True