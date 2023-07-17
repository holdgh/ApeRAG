import json
import re
from datetime import datetime
from typing import Dict

AVAILABLE_MODEL = [""]
AVAILABLE_SOURCE = ["system", "local", "s3", "oss", "ftp", "email"]


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


def generate_vector_db_collection_id(user, collection) -> str:
    return str(user).replace("|", "-") + "-" + str(collection)


def fix_path_name(path) -> str:
    return str(path).replace("|", "-")


def validate_document_config(config: Dict) -> bool:
    if "source" not in config.keys():
        return False
    if config.get("source") not in AVAILABLE_SOURCE:
        return False
    return True
