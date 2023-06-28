import re
from datetime import datetime


def extract_collection_and_chat_id(path: str):
    match = re.match(r"/api/v1/collections/(?P<collection_id>\w+)/chats/(?P<chat_id>\w+)/connect$", path)
    if match:
        return match.group("collection_id"), match.group("chat_id")
    else:
        raise ValueError(f"Invalid path format: {path}")


def now_unix_milliseconds():
    return int(datetime.utcnow().timestamp() * 1e3)