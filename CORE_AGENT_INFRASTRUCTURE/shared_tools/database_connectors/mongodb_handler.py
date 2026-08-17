"""
MongoDB handler (pymongo) — used for conversation logs and event streams.

Env vars: MONGO_URI, MONGO_DATABASE
"""
import os
from typing import Any, Optional

try:
    from pymongo import MongoClient
except ImportError:  # pragma: no cover
    MongoClient = None


class MongoDBHandler:
    def __init__(self, uri: Optional[str] = None, database: Optional[str] = None):
        if MongoClient is None:
            raise RuntimeError("pymongo not installed")
        self.client = MongoClient(uri or os.getenv("MONGO_URI", "mongodb://localhost:27017"))
        self.db = self.client[database or os.getenv("MONGO_DATABASE", "agency")]

    def collection(self, name: str):
        return self.db[name]

    def insert(self, collection: str, document: dict) -> str:
        result = self.db[collection].insert_one(document)
        return str(result.inserted_id)

    def find(self, collection: str, query: dict, limit: int = 50) -> list[dict]:
        return list(self.db[collection].find(query).limit(limit))

    def upsert(self, collection: str, filter_doc: dict, update: dict) -> None:
        self.db[collection].update_one(filter_doc, {"$set": update}, upsert=True)

    def healthcheck(self) -> dict:
        try:
            self.client.admin.command("ping")
            return {"ok": True}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}
