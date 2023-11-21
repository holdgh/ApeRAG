import json

from kubechat.utils.utils import now_unix_milliseconds


def success_response(message_id, data, issql=False):
    return json.dumps(
        {
            "type": "message" if not issql else "sql",
            "id": message_id,
            "data": data,
            "timestamp": now_unix_milliseconds(),
        }
    )


def fail_response(message_id, error):
    return json.dumps(
        {
            "type": "error",
            "id": message_id,
            "data": error,
            "timestamp": now_unix_milliseconds(),
        }
    )


def start_response(message_id):
    return json.dumps(
        {
            "type": "start",
            "id": message_id,
            "timestamp": now_unix_milliseconds(),
        }
    )


def stop_response(message_id, references, memory_count=0):
    if references is None:
        references = []
    return json.dumps(
        {
            "type": "stop",
            "id": message_id,
            "data": references,
            "memoryCount": memory_count,
            "timestamp": now_unix_milliseconds()
        }
    )
