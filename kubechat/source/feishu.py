import datetime
import json
import logging
import os
from threading import Lock
from urllib.parse import urlencode

from pydantic import BaseModel
from abc import ABC
from typing import Dict, Any

import requests

from kubechat.source.base import Source
from kubechat.models import Collection, Document, DocumentStatus
from kubechat.source.utils import gen_temporary_file

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


class FeishuSource(Source):
    def __init__(self, collection: Collection, ctx: Dict[str, Any]):
        super().__init__(ctx)
        self.client = FeishuClient(ctx)
        self.space_id = ctx.get("space_id", "")
        self.node_id = ctx.get("node_id", "")
        self.collection = collection

    def get_node_documents(self, space_id, node_token):
        documents = []
        root_node = self.client.get_node(node_token)
        nodes = [root_node]
        for node in nodes:
            if node["has_child"]:
                nodes.extend(self.client.get_space_nodes(space_id, node["node_token"]))

            if node["obj_type"] == "docx":
                doc = Document(
                    user=self.collection.user,
                    name=node["title"] + ".txt",
                    status=DocumentStatus.PENDING,
                    collection=self.collection,
                    metadata=json.dumps(node),
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
        content = self.client.get_doc_plain_content(node["obj_token"])
        temp_file = gen_temporary_file(doc.name)
        temp_file.write(content.encode("utf-8"))
        temp_file.close()
        return temp_file.name

    def cleanup_document(self, file_path: str, doc: Document):
        os.remove(file_path)

    def close(self):
        pass

    def sync_enabled(self):
        return True