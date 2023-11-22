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


def new_db_client(config):
    # only import class when it is needed
    match config["db_type"]:
        case "sqlite" | "oracle":
            from services.text2SQL.sql.sql import SQLBase

            new_client = SQLBase
        case "postgresql":
            from services.text2SQL.sql.postgresql import Postgresql

            new_client = Postgresql
        case "mysql":
            from services.text2SQL.sql.mysql import Mysql

            new_client = Mysql
        case "redis":
            from services.text2SQL.nosql.redis_query import Redis

            new_client = Redis
        case "mongo":
            from services.text2SQL.nosql.mongo_query import Mongo

            new_client = Mongo
        case "clickhouse":
            from services.text2SQL.nosql.clickhouse_query import Clickhouse

            new_client = Clickhouse
        case "elasticsearch":
            from services.text2SQL.nosql.elasticsearch_query import ElasticsearchClient

            new_client = ElasticsearchClient
        case _:
            new_client = None
    if new_client is None:
        return None

    client = new_client(
        host=config["host"],
        user=config["username"] if "username" in config.keys() else None,
        pwd=config["password"] if "password" in config.keys() else None,
        port=int(config["port"])
        if "port" in config.keys() and config["port"] is not None
        else None,
        db_type=config["db_type"],
        db=config["db_name"] if "db_name" in config.keys() else "",
    )
    return client
