import logging

from func_timeout import func_set_timeout
from llama_index.prompts.base import Prompt
from pymongo import MongoClient

from services.text2SQL.nosql.nosql import NoSQLBase

logger = logging.getLogger(__name__)

_MONGODB_PROMPT_TPL = (
    "You are now an expert on mongodb，Given an input question, first create a syntactically correct MONGODB "
    "query to run, then look at the results of the query and return the answer."
    "You can order the results by a relevant column to return the most "
    "interesting examples in the database.\n"
    "Pay attention to use only the keys that you can see in the schema "
    "description. "
    "Be careful to not query for keys that do not exist. "
    "Use the following format:\n"
    "Question: Question here\n"
    "Query: Query to run\n"
    "Result: Result of the Query\n"
    "Answer: Final answer here\n"
    "Only use the collections listed below.\n"
    "{schema}\n"
    "Question: {query_str}\n"
    "Query: "
)


class Mongo(NoSQLBase):
    @func_set_timeout(2)
    def ping(self, verify, ca_cert, client_key, client_cert):
        if self.user is not None:
            self.conn = MongoClient(
                "mongodb://"
                + self.user
                + ":"
                + self.pwd
                + "@"
                + self.host
                + ":"
                + str(self.port),
                **self._get_ssl_args(verify, ca_cert, client_key, client_cert),
            )
        else:
            self.conn = MongoClient(
                "mongodb://" + self.host + ":" + str(self.port),
                **self._get_ssl_args(verify, ca_cert, client_key, client_cert),
            )
        return self.conn.admin.command("ping")

    def _generate_schema(self):
        db = self.conn[self.db]
        collections = db.list_collection_names()
        schema = ""
        for collection in collections:
            schema += "Collection " + collection + ":"
            document = collection.find_one()
            for key in document.keys():
                schema += "Key: {}, Data Type: {}; ".format(key, type[document[key]])
            schema += "\n"

    # pymongo does not support a way to directly execute js query statements
    def execute_query(self, query):
        return

    def _get_ssl_args(self, verify, ca_cert, client_key, client_cert):
        return {
            "directConnection": True,
            "ssl": verify,
            "tlsCAFile": ca_cert,
            "tlsCertificateKeyFile": client_key,
        }

    def _get_default_prompt(self):
        return Prompt(
            _MONGODB_PROMPT_TPL,
            stop_token="\nResult:",
            prompt_type="text_to_sql",
        )
