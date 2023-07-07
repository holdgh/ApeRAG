from typing import Optional

from sqlalchemy import text

from services.text2SQL.sql.sql import SQLBase


class Postgresql(SQLBase):
    def _generate_db_url(self, driver: Optional[str] = "psycopg2") -> str:
        if self.port is None:
            self.port = 5432
        return f"{self.db_type}+{driver}://{self.user}:{self.pwd}@{self.host}:{self.port}/{self.db}"

    def _get_ssl_args(self, verify, ca_cert, client_key, client_cert):
        return {
            "sslmode": "require",
            "sslcert": client_cert,
            "sslkey": client_key,
            "sslrootcert": ca_cert
        } if verify else {}

    def get_database_list(self):
        cmd = "SELECT datname FROM pg_database;"

        db_list = []
        with self.conn.engine.connect() as connection:
            db_all = connection.execute(text(cmd))
            for db in db_all:
                # template0 is not allowed to connect
                if db[0] != "template0":
                    db_list.append(db[0])
        return db_list



