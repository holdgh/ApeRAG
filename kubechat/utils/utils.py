import base64
import hashlib
import re
from datetime import datetime

from Crypto.Cipher import AES

AVAILABLE_MODEL = [""]
AVAILABLE_SOURCE = ["system", "local", "s3", "oss", "ftp", "email", "feishu","url"]


def extract_bot_and_chat_id(path: str):
    match = re.match(
        r"/api/v1/bots/(?P<bot_id>\w+)/chats/(?P<chat_id>\w+)/connect$",
        path,
    )
    if match:
        return match.group("bot_id"), match.group("chat_id")
    else:
        raise ValueError(f"Invalid path format: {path}")


def extract_web_bot_and_chat_id(path: str):
    match = re.match(
        r"/api/v1/bots/(?P<bot_id>\w+)/web-chats/(?P<chat_id>\w+)/connect$",
        path,
    )
    if match:
        return match.group("bot_id"), match.group("chat_id")
    else:
        raise ValueError(f"Invalid path format: {path}")


def extract_collection_and_chat_id(path: str):
    match = re.match(
        r"/api/v1/collections/(?P<collection_id>\w+)/chats/(?P<chat_id>\w+)/connect$",
        path,
    )
    if match:
        return match.group("collection_id"), match.group("chat_id")
    else:
        raise ValueError(f"Invalid path format: {path}")


def extract_chat_id(path: str):
    match = re.match(r"/api/v1/bot/(?P<chat_id>\w+)/connect$", path)
    if match:
        return match.group("chat_id")
    else:
        raise ValueError(f"Invalid path format: {path}")


def extract_database(path: str, db_type):
    if db_type in ["mysql", "postgresql"]:
        match = re.match(r"database=(?P<database>\w+)", path)
        if match:
            return match.group("database")
        else:
            raise ValueError(f"Invalid path format: {path}")
    else:
        return None


def extract_code_chat(path: str):
    match = re.match(r"/api/v1/code/(?P<chat_id>\w+)/connect$", path)
    if match:
        return match.group("chat_id")
    else:
        raise ValueError(f"Invalid path format: {path}")


def now_unix_milliseconds():
    return int(datetime.utcnow().timestamp() * 1e3)


def generate_fulltext_index_name(collection_id) -> str:
    return str(collection_id)


def generate_vector_db_collection_name(collection_id) -> str:
    return str(collection_id)

def generate_qa_vector_db_collection_name(collection) -> str:
    return str(collection) + "-qa"

def fix_path_name(path) -> str:
    return str(path).replace("|", "-")


class AESCipher(object):
    def __init__(self, key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(AESCipher.str_to_bytes(key)).digest()

    @staticmethod
    def str_to_bytes(data):
        u_type = type(b"".decode('utf8'))
        if isinstance(data, u_type):
            return data.encode('utf8')
        return data

    @staticmethod
    def _unpadding(s):
        return s[:-ord(s[len(s) - 1:])]

    def decrypt(self, enc):
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpadding(cipher.decrypt(enc[AES.block_size:]))

    def decrypt_string(self, enc):
        enc = base64.b64decode(enc)
        return self.decrypt(enc).decode('utf8')


