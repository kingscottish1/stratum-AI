"""
PostgreSQL handler (psycopg2). Each vertical gets its own schema namespace.

Env vars: PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE
"""
import os
from typing import Any, Optional

try:
    import psycopg2
    import psycopg2.extras
except ImportError:  # pragma: no cover
    psycopg2 = None


class PostgresHandler:
    def __init__(self, dsn: Optional[str] = None):
        if psycopg2 is None:
            raise RuntimeError("psycopg2 not installed")
        self.dsn = dsn or os.getenv(
            "PG_DSN",
            f"host={os.getenv('PG_HOST', 'localhost')} port={os.getenv('PG_PORT', 5432)} "
            f"user={os.getenv('PG_USER', 'agent')} password={os.getenv('PG_PASSWORD', '')} "
            f"dbname={os.getenv('PG_DATABASE', 'agency')}",
        )

    def _connect(self):
        return psycopg2.connect(self.dsn)

    def query(self, sql: str, params: Optional[tuple] = None) -> list[dict]:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                return cur.fetchall()

    def execute(self, sql: str, params: Optional[tuple] = None) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                conn.commit()
                return cur.rowcount

    def healthcheck(self) -> dict:
        try:
            self.query("SELECT 1")
            return {"ok": True}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}
