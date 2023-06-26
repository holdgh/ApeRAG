from langchain.sql_database import SQLDatabase as LangchainSQLDatabase
from sqlalchemy import MetaData, create_engine, insert, text
from sqlalchemy.engine import Engine
from typing import Any, Dict, List, Tuple, Optional
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError

# more information about Dialect https://docs.sqlalchemy.org/en/20/dialects/#included-dialects
Dialect = ["mysql","postgresql","sqlite","oracle","mssql"]

#
class SQLDataBase(LangchainSQLDatabase):
    """SQL Database.

       Wrapper around SQLDatabase object from langchain.
       See `langchain documentation <https://tinyurl.com/4we5ku8j>`_ for more details:
       Do not

       Args:
           *args: Arguments to pass to langchain SQLDatabase.
           **kwargs: Keyword arguments to pass to langchain SQLDatabase.

       """

    @property
    def engine(self) -> Engine:
        """Return SQL Alchemy engine."""
        return self._engine

    @property
    def metadata_obj(self) -> MetaData:
        """Return SQL Alchemy metadata."""
        return self._metadata

    @classmethod
    def from_uri(
            cls, database_uri: str, engine_args: Optional[dict] = None, **kwargs: Any
    ) -> "SQLDataBase":
        """Construct a SQLAlchemy engine from URI."""
        _engine_args = engine_args or {}
        return cls(create_engine(database_uri, **_engine_args), **kwargs)

    def set_sample_rows(self, nums: int):
        self._sample_rows_in_table_info = nums

    def get_table_columns(self, table_name: str) -> List[Any]:
        """Get table columns."""
        return self._inspector.get_columns(table_name)

    def get_single_table_info(self, table_name: str) -> str:
        """Get table info for a single table."""
        # same logic as table_info, but with specific table names
        template = (
            "Table '{table_name}' has columns: {columns} "
            "and foreign keys: {foreign_keys}."
        )
        columns = []
        for column in self._inspector.get_columns(table_name):
            columns.append(f"{column['name']} ({str(column['type'])})")
        column_str = ", ".join(columns)
        foreign_keys = []
        for foreign_key in self._inspector.get_foreign_keys(table_name):
            foreign_keys.append(
                f"{foreign_key['constrained_columns']} -> "
                f"{foreign_key['referred_table']}.{foreign_key['referred_columns']}"
            )
        foreign_key_str = ", ".join(foreign_keys)
        table_str = template.format(
            table_name=table_name, columns=column_str, foreign_keys=foreign_key_str
        )
        return table_str

    def insert_into_table(self, table_name: str, data: dict) -> None:
        """Insert data into a table."""
        table = self._metadata.tables[table_name]
        stmt = insert(table).values(**data)
        with self._engine.connect() as connection:
            connection.execute(stmt)
            connection.commit()

    def run_sql(self, command: str) -> Tuple[str, Dict]:
        """Execute a SQL statement and return a string representing the results.

        If the statement returns rows, a string of the results is returned.
        If the statement returns no rows, an empty string is returned.
        """
        return self._run_with_no_throw(command)

    def _run_with_no_throw(self, command: str) -> Tuple[str, Dict]:
        try:
            with self._engine.connect() as connection:
                cursor = connection.execute(text(command))
                if cursor.returns_rows:
                    result = cursor.fetchall()
                    return str(result), {"result": result}
        except SQLAlchemyError as e:
            return "", {}

    def generate_sql_context(self, sample_rows: int) -> str:
        scheme = self.get_table_info_no_throw()
        tables = self.get_usable_table_names()
        meta_tables = [
            tbl
            for tbl in self._metadata.sorted_tables
            if tbl.name in set(tables)
               and not (self.dialect == "sqlite" and tbl.name.startswith("sqlite_"))
        ]
        self.set_sample_rows(sample_rows)
        for table in meta_tables:
            scheme += f"\nhere are some example rows data in {table} to help you understand the table struct:" + f"\n{self._get_sample_rows(table)}\n"

        # more database info could add here

        return scheme

#
# class NoSQLTemplate():
