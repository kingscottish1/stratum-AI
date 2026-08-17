"""
MySQL handler (pymysql) for clients that keep legacy MySQL databases.

Env vars: MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
"""
import os
from typing import Any, Optional

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:  # pragma: no cover
    pymysql = None


class MySQLHandler:
    def __init__(self, **overrides: Any):
        if pymysql is None:
            raise RuntimeError("pymysql not installed")
        self.config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "user": os.getenv("MYSQL_USER", "agent"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "agency"),
            "cursorclass": DictCursor,
            "charset": "utf8mb4",
        }
        self.config.update(overrides)

    def query(self, sql: str, params: Optional[tuple] = None) -> list[dict]:
        conn = pymysql.connect(**self.config)
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return list(cur.fetchall())
        finally:
            conn.close()

    def execute(self, sql: str, params: Optional[tuple] = None) -> int:
        conn = pymysql.connect(**self.config)
        try:
            with conn.cursor() as cur:
                affected = cur.execute(sql, params)
            conn.commit()
            return affected
        finally:
            conn.close()
