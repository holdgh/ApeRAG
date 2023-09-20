import datetime
import io
import json
import logging
import os
import tempfile
from abc import ABC, abstractmethod
from threading import Lock
from typing import Dict, Any

import pytablewriter
import requests
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def gen_temporary_file(name, default_suffix=""):
    prefix, suffix = os.path.splitext(name)
    prefix = prefix.strip("/").replace("/", "--")
    suffix = suffix.lower()
    if not suffix:
        suffix = default_suffix
    return tempfile.NamedTemporaryFile(delete=False, prefix=prefix, suffix=suffix)


feishu_lang_code_mapping = {
    1: "plaintext",
    2: "abap",
    3: "ada",
    4: "apache",
    5: "apex",
    6: "assembly",
    7: "bash",
    8: "csharp",
    9: "c++",
    10: "c",
    11: "cobol",
    12: "css",
    13: "coffeescript",
    14: "d",
    15: "dart",
    16: "delphi",
    17: "django",
    18: "dockerfile",
    19: "erlang",
    20: "fortran",
    21: "foxpro",
    22: "go",
    23: "groovy",
    24: "html",
    25: "htmlbars",
    26: "http",
    27: "haskell",
    28: "json",
    29: "java",
    30: "javascript",
    31: "julia",
    32: "kotlin",
    33: "latex",
    34: "lisp",
    35: "logo",
    36: "lua",
    37: "matlab",
    38: "makefile",
    39: "markdown",
    40: "nginx",
    41: "objective",
    42: "openedgeabl",
    43: "php",
    44: "perl",
    45: "postscript",
    46: "power",
    47: "prolog",
    48: "protobuf",
    49: "python",
    50: "r",
    51: "rpg",
    52: "ruby",
    53: "rust",
    54: "sas",
    55: "scss",
    56: "sql",
    57: "scala",
    58: "scheme",
    59: "scratch",
    60: "shell",
    61: "swift",
    62: "thrift",
    63: "typescript",
    64: "vbscript",
    65: "visual",
    66: "xml",
    67: "yaml",
    68: "cmake",
    69: "diff",
    70: "gherkin",
    71: "graphql",
    72: "opengl shading language",
    73: "properties",
    74: "solidity",
    75: "toml"
}


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


class OutputFormat(BaseModel):
    PlainText = "plain_text"
    Markdown = "markdown"


class FeishuNoPermission(Exception):
    """
    raised when user has no permission to call the Feishu API
    """


class FeishuPermissionDenied(Exception):
    """
    raised when user has no permission to access the Feishu resource
    """


class FeishuBlockParser(ABC):
    def __init__(self, doc_id, blocks):
        self.block_map = {}
        self.doc_id = doc_id
        for block in blocks:
            self.block_map[block["block_id"]] = block

    def gen(self):
        return self.handle_block(self.block_map[self.doc_id])

    @abstractmethod
    def handle_block(self, block, indent=0):
        pass

    def parse_table(self, table):
        rows = []
        for index, block_id in enumerate(table["cells"]):
            cell_block = self.block_map[block_id]
            cell_content = self.handle_block(cell_block)
            cell_content = cell_content.replace("\n", "<br/>")
            row_index = int(index / table["property"]["column_size"])
            if len(rows) < row_index + 1:
                rows.append([])
            rows[row_index].append(cell_content)
        text = self.renderMarkdownTable(rows)
        text += "\n"
        return text

    def parse_table_cell(self, block):
        text = ""
        for child in block["children"]:
            child_block = self.block_map[child]
            text += self.handle_block(child_block)
        return text

    def parse_block_page(self, block):
        text = ""
        text += self.parse_block_text(block["page"]["elements"], [])

        for child in block.get("children", []):
            child_block = self.block_map[child]
            text += self.handle_block(child_block)
        return text

    def parse_block_text(self, elements, children):
        text = ""
        inline = len(elements) > 1
        for element in elements:
            text += self.parse_block_text_element(element, inline)
        text += "\n"
        for child in children:
            child_block = self.block_map[child]
            text += self.handle_block(child_block)
        return text

    def parse_block_bullet_list(self, block, indent):
        text = "- "
        text += self.parse_block_text(block["bullet"]["elements"], [])

        for child_id in block.get("children", []):
            child_block = self.block_map[child_id]
            text += self.handle_block(child_block, indent + 1)
        return text

    def parse_block_ordered_list(self, block, indent):
        order = 1
        parent = self.block_map[block["parent_id"]]
        for index, child in enumerate(parent["children"]):
            if child != block["block_id"]:
                continue
            i = index - 1
            while i >= 0:
                if self.block_map[parent["children"][i]]["block_type"] == 13:
                    order += 1
                else:
                    break
                i -= 1
            break

        text = f"{order}. "
        text += self.parse_block_text(block["ordered"]["elements"], [])

        for child_id in block.get("children", []):
            child_block = self.block_map[child_id]
            text += self.handle_block(child_block, indent + 1)
        return text

    @staticmethod
    def parse_block_text_element(element, inline):
        text = ""
        text_run = element.get("text_run", "")
        if text_run:
            text += text_run["content"]

        mention_user = element.get("mention_user", "")
        if mention_user:
            text += mention_user["user_id"]

        mention_doc = element.get("mention_doc", "")
        if mention_doc:
            text += "[%s](%s)" % (mention_doc.get("title", ""), mention_doc.get("url", ""))

        equation = element.get("equation", "")
        if equation:
            symbol = "$$"
            if inline:
                symbol = "$"
            text += "%s%s%s" % (symbol, equation, symbol)
        return text

    @staticmethod
    def renderMarkdownTable(data):
        writer = pytablewriter.MarkdownTableWriter()
        writer.stream = io.StringIO()
        writer.headers = data[0]
        writer.value_matrix = data[1:]
        writer.write_table()
        return writer.stream.getvalue()


class Feishu2Markdown(FeishuBlockParser):

    # https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/data-structure/block#e8ce4e8e
    def handle_block(self, block, indent=0):
        text = "\t" * indent
        block_type = block["block_type"]
        match block_type:
            case 1:
                # page
                text += "# "
                text += self.parse_block_page(block)
            case 2:
                # text
                text += self.parse_block_text(block["text"]["elements"], block.get("children", []))
            case 3:
                # heading 1
                text += "# "
                text += self.parse_block_text(block["heading1"]["elements"], block.get("children", []))
            case 4:
                # heading 2
                text += "## "
                text += self.parse_block_text(block["heading2"]["elements"], block.get("children", []))
            case 5:
                # heading 3
                text += "### "
                text += self.parse_block_text(block["heading3"]["elements"], block.get("children", []))
            case 6:
                # heading 4
                text += "#### "
                text += self.parse_block_text(block["heading4"]["elements"], block.get("children", []))
            case 7:
                # heading 5
                text += "##### "
                text += self.parse_block_text(block["heading5"]["elements"], block.get("children", []))
            case 8:
                # heading 6
                text += "###### "
                text += self.parse_block_text(block["heading6"]["elements"], block.get("children", []))
            case 9:
                # heading 7
                text += "####### "
                text += self.parse_block_text(block["heading7"]["elements"], block.get("children", []))
            case 10:
                # heading 8
                text += "######## "
                text += self.parse_block_text(block["heading8"]["elements"], block.get("children", []))
            case 11:
                # heading 9
                text += "######### "
                text += self.parse_block_text(block["heading9"]["elements"], block.get("children", []))
            case 12:
                # bullet
                text += self.parse_block_bullet_list(block, indent)
            case 13:
                # ordered list
                text += self.parse_block_ordered_list(block, indent)
                text += "\n"
            case 14:
                # code
                lang = feishu_lang_code_mapping[block["code"]["style"]["language"]]
                text += f"```{lang}\n"
                text += self.parse_block_text(block["code"]["elements"], block.get("children", []))
                text += "```\n"
            case 15:
                # quote
                text += "> "
                text += self.parse_block_text(block["quote"]["elements"], block.get("children", []))
            case 17:
                # todo
                if block["todo"]["style"]["done"]:
                    text += "- [x] "
                else:
                    text += "- [ ] "
                text += self.parse_block_text(block["todo"]["elements"], block.get("children", []))
            case 19:
                # callout
                text += self.parse_block_text([], block.get("children", []))
            case 22:
                # divider
                text += "---\n"
            case 31:
                # table
                text += self.parse_table(block["table"])
            case 32:
                # table cell
                text += self.parse_table_cell(block)
            case 34:
                # quote container
                for child in block.get("children", []):
                    child_block = self.block_map[child]
                    text += "> "
                    text += self.handle_block(child_block)
            case _:
                print(f"Unhandled block type {block_type}")
                print(block)
        return text


class Feishu2PlainText(FeishuBlockParser):

    # https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/data-structure/block#e8ce4e8e
    def handle_block(self, block, indent=0):
        text = "\t" * indent
        block_type = block["block_type"]
        match block_type:
            case 1:
                # page
                text += self.parse_block_page(block)
            case 2:
                # text
                text += self.parse_block_text(block["text"]["elements"], block.get("children", []))
            case 3:
                # heading 1
                text += self.parse_block_text(block["heading1"]["elements"], block.get("children", []))
            case 4:
                # heading 2
                text += self.parse_block_text(block["heading2"]["elements"], block.get("children", []))
            case 5:
                # heading 3
                text += self.parse_block_text(block["heading3"]["elements"], block.get("children", []))
            case 6:
                # heading 4
                text += self.parse_block_text(block["heading4"]["elements"], block.get("children", []))
            case 7:
                # heading 5
                text += self.parse_block_text(block["heading5"]["elements"], block.get("children", []))
            case 8:
                # heading 6
                text += self.parse_block_text(block["heading6"]["elements"], block.get("children", []))
            case 9:
                # heading 7
                text += self.parse_block_text(block["heading7"]["elements"], block.get("children", []))
            case 10:
                # heading 8
                text += self.parse_block_text(block["heading8"]["elements"], block.get("children", []))
            case 11:
                # heading 9
                text += self.parse_block_text(block["heading9"]["elements"], block.get("children", []))
            case 12:
                # bullet
                text += self.parse_block_bullet_list(block, indent)
            case 13:
                # ordered list
                text += self.parse_block_ordered_list(block, indent)
                text += "\n"
            case 14:
                # code
                text += self.parse_block_text(block["code"]["elements"], block.get("children", []))
            case 15:
                # quote
                text += self.parse_block_text(block["quote"]["elements"], block.get("children", []))
            case 17:
                # todo
                text += self.parse_block_text(block["todo"]["elements"], block.get("children", []))
            case 19:
                # callout
                text += self.parse_block_text([], block.get("children", []))
            case 22:
                # divider
                text += "---\n"
            case 31:
                # table
                text += self.parse_table(block["table"])
            case 32:
                # table cell
                text += self.parse_table_cell(block)
            case 34:
                # quote container
                for child in block.get("children", []):
                    child_block = self.block_map[child]
                    text += self.handle_block(child_block)
            case _:
                print(f"Unhandled block type {block_type}")
                print(block)
        return text


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
        resp = self.raw_request(method, path, **kwargs)
        resp = resp.json()
        if resp["code"] != 0:
            raise Exception(f"request failed: {resp['msg']}")
        return resp

    def raw_request(self, method, path, **kwargs):
        url = f"https://open.feishu.cn/open-apis/{path}"
        logger.info("request feishu api: %s %s", method, url)
        with self.mutex:
            if self.expire_at - datetime.datetime.now() < datetime.timedelta(minutes=15):
                self.tenant_access_token, self.expire_at = self.get_tenant_access_token()
        headers = {"Authorization": f"Bearer {self.tenant_access_token}"}
        resp = requests.request(method, url, headers=headers, **kwargs)
        if resp.status_code != 200:
            if "No permission" in resp.json()["msg"]:
                raise FeishuNoPermission()
            if "permission denied" in resp.json()["msg"]:
                raise FeishuPermissionDenied()
            raise Exception(f"request failed: {resp.text}")
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
        """
        https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal
        """
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

    def reply_card_message(self, message_id, data):
        """
        https://open.feishu.cn/document/server-docs/im-v1/message/reply
        """
        resp = self.post(f"im/v1/messages/{message_id}/reply", json=data)
        return resp["data"]["message_id"]

    def delay_update_card_message(self, data):
        """
        https://open.feishu.cn/document/server-docs/im-v1/message-card/delay-update-message-card
        """
        self.post(f"interactive/v1/card/update", json=data)

    def update_card_message(self, message_id, data):
        """
        https://open.feishu.cn/document/server-docs/im-v1/message-card/patch
        """
        self.patch(f"im/v1/messages/{message_id}", json=data)

    def send_message(self, chat_id, message):
        """
        https://open.feishu.cn/document/server-docs/im-v1/message/create
        """
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
        """
        https://open.feishu.cn/document/server-docs/docs/wiki-v2/space/list
        """
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
        """
        https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/list
        """
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
        """
        https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/get_node
        """
        params = {
            "token": token,
        }
        resp = self.get(f"wiki/v2/spaces/get_node", params=params)
        return resp["data"]["node"]

    def get_new_doc_plain_content(self, doc_id):
        """
        https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/raw_content
        """
        if doc_id is None:
            raise Exception("doc_id is None")
        resp = self.get(f"docx/v1/documents/{doc_id}/raw_content?lang=0")
        return resp["data"]["content"]

    def get_old_doc_plain_content(self, doc_id):
        if doc_id is None:
            raise Exception("doc_id is None")
        resp = self.get(f"doc/v2/{doc_id}/raw_content")
        return resp["data"]["content"]

    def get_docx_blocks(self, doc_id):
        """
        https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/list
        """
        if doc_id is None:
            raise Exception("doc_id is None")
        resp = self.get(f"docx/v1/documents/{doc_id}/blocks")
        return resp["data"]["items"]

    def create_export_task(self, doc_id, doc_type="docx", extension="pdf"):
        """
        https://open.feishu.cn/document/server-docs/docs/drive-v1/export_task/create
        """
        if doc_id is None:
            raise Exception("doc_id is None")
        data = {
            "type": doc_type,
            "token": doc_id,
            "file_extension": extension,
        }
        resp = self.post("drive/v1/export_tasks", json=data)
        return resp["data"]["ticket"]

    def query_export_task(self, ticket, doc_id):
        """
        https://open.feishu.cn/document/server-docs/docs/drive-v1/export_task/get
        """
        if ticket is None:
            raise Exception("ticket is None")
        params = {
            "token": doc_id,
        }
        resp = self.get(f"drive/v1/export_tasks/{ticket}", params=params)
        return resp["data"]["result"]

    def download_doc(self, token):
        """
        https://open.feishu.cn/document/server-docs/docs/drive-v1/export_task/download
        """
        if token is None:
            raise Exception("token is None")
        resp = self.raw_request("GET", f"drive/v1/export_tasks/file/{token}/download")
        return resp.content
