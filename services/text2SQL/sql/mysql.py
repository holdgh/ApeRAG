from typing import Optional

from sqlalchemy import text

from services.text2SQL.sql.sql import SQLBase


class Mysql(SQLBase):
    def _generate_db_url(self, driver: Optional[str] = "pymysql") -> str:
        if self.port is None:
            self.port = 3306
        return f"{self.db_type}+{driver}://{self.user}:{self.pwd}@{self.host}:{self.port}/{self.db}"

    def _get_ssl_args(self, verify, ca_cert, client_key, client_cert):
        ssl_str = "?"
        if ca_cert is not None:
            ssl_str += "ssl_ca={}&".format(ca_cert)
        if client_key is not None:
            ssl_str += "ssl_key={}&".format(client_key)
        if client_cert is not None:
            ssl_str += "ssl_cert={}".format(client_cert)

        if verify and ssl_str == "?":
            raise ValueError("have no ssl file at all")
        return ssl_str

    def get_database_list(self):
        cmd = "show databases;"

        db_list = []
        with self.conn.engine.connect() as connection:
            db_all = connection.execute(text(cmd))
            for db in db_all:
                db_list.append(db[0])
        return db_list
