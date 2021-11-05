from contextlib import contextmanager
from decouple import config
from typing import Callable, Tuple, List, Any

import psycopg2


class GenericDbHandler:

    def __init__(self):
        self.__connection = psycopg2.connect(
            database=config("DB_NAME"),
            user=config("DB_USER"),
            password=config("DB_PASSWORD"),
            host=config("DB_HOST"),
            port=config("DB_PORT", cast=int, default=5432)
        )
        self.__connection.autocommit = True

    @contextmanager
    def __cursor(self):
        cursor = self.__connection.cursor()
        yield cursor
        cursor.close()

    def get_one(self, table: str, obj_id: int, cast: Callable = None):
        with self.__cursor() as cur:
            cur.execute(f"SELECT *, {table}_id as id FROM {table} WHERE {table}_id={obj_id}")
            columns = cur.description
            result = {columns[i].name: value for i, value in enumerate(cur.fetchone())}
            if cast is not None:
                return cast(**result)
            else:
                return result

    def get_list(self, table: str, sort_col: str = None, sort_order: str = None, record_range: Tuple[int, int] = None, cast: Callable = None):
        with self.__cursor() as cur:
            sql = f"SELECT *, {table}_id as id FROM {table} "
            if sort_col is not None:
                sql += f"ORDER BY {sort_col} {sort_order or ''} "
            if record_range is not None and not any([el is None for el in record_range]):
                sql += f"LIMIT {record_range[1] - record_range[0]} OFFSET {record_range[0]}"
            cur.execute(sql)
            columns = cur.description
            result = [{columns[i].name: value for i, value in enumerate(row)} for row in cur.fetchall()]
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            total_size = int(cur.fetchone()[0])
            if cast is not None:
                return [cast(**props) for props in result], total_size
            else:
                return result, total_size

    def create(self, table: str, columns: List[str], values: List[Any]):
        with self.__cursor() as cur:
            cur.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join(['%s'] * len(columns))}) RETURNING {table}_id", values)
            print(cur.query)
            return cur.fetchone()[0]

    def delete_one(self, table: str, id: int):
        with self.__cursor() as cur:
            cur.execute(f"DELETE FROM {table} WHERE {table}_id={id}")
            print(cur.query)

    def update_one(self, table: str, id: int, columns: List[str], values: List[Any]):
        with self.__cursor() as cur:
            assignments = [f"{column}=%s" for column in columns]
            cur.execute(f"UPDATE {table} SET {','.join(assignments)} WHERE {table}_id={id}", values)