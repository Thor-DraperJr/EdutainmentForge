"""Task status persistence layer.

Provides a Table Storage backed implementation with in-memory fallback.
Designed for hackathon use: minimal dependencies, defensive error handling, optional caching.
"""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, Dict, Optional, List

from utils.logger import get_logger

logger = get_logger(__name__)

try:
    from azure.data.tables import TableServiceClient, UpdateMode  # type: ignore
    AZURE_TABLES_AVAILABLE = True
except Exception:  # pragma: no cover - import path issues
    AZURE_TABLES_AVAILABLE = False


class TaskStoreError(Exception):
    """Raised when the task store encounters an unrecoverable error."""
    pass


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


class TaskStore:
    """Abstraction over task status storage.

    Usage Pattern:
        store = TaskStore.from_env()
        store.create(task_id, {...})
        store.update(task_id, status="processing", progress=50)
        task = store.get(task_id)
    """

    def __init__(self, table_client=None, table_name: str = "taskstatus", use_remote: bool = False):
        self._table = table_client
        self._table_name = table_name
        self._use_remote = use_remote and table_client is not None
        # Small in-memory cache for active tasks to reduce round trips
        self._cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def from_env(cls) -> "TaskStore":
        """Factory loading configuration from environment.

        Prefers connection string if provided; will also attempt DefaultAzureCredential
        implicitly if running in Azure *only if* connection string absent (future enhancement).
        """
        table_name = os.getenv("TASK_STATUS_TABLE", "taskstatus")
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

        if not AZURE_TABLES_AVAILABLE:
            logger.warning("Azure Tables SDK not available; TaskStore will run in-memory only.")
            return cls(None, table_name, use_remote=False)

        if not connection_string:
            logger.warning("No AZURE_STORAGE_CONNECTION_STRING set; using in-memory TaskStore.")
            return cls(None, table_name, use_remote=False)
        try:
            service = TableServiceClient.from_connection_string(conn_str=connection_string)
            # Create table if missing
            try:
                service.create_table_if_not_exists(table_name)
            except Exception:  # Best effort
                pass
            table_client = service.get_table_client(table_name)
            logger.info(f"TaskStore using Azure Table '{table_name}'")
            return cls(table_client, table_name, use_remote=True)
        except Exception as e:
            logger.warning(f"Failed to initialize TableServiceClient: {e}; falling back to in-memory store")
            return cls(None, table_name, use_remote=False)

    # ----------------------- Public API ----------------------- #

    def create(self, task_id: str, data: Dict[str, Any]) -> None:
        entity = self._prepare_entity(task_id, data, is_new=True)
        self._cache[task_id] = entity.copy()
        if self._use_remote:
            try:
                self._table.upsert_entity(entity=entity, mode=UpdateMode.MERGE)
            except Exception as e:
                logger.debug(f"TaskStore create remote failed: {e}")

    def update(self, task_id: str, **fields: Any) -> None:
        current = self._cache.get(task_id) or {}
        current.update(fields)
        current["updated_at"] = _utc_now_iso()
        self._cache[task_id] = current
        if self._use_remote:
            try:
                entity = self._prepare_entity(task_id, current, is_new=False)
                self._table.upsert_entity(entity=entity, mode=UpdateMode.MERGE)
            except Exception as e:
                logger.debug(f"TaskStore update remote failed: {e}")

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        cached = self._cache.get(task_id)
        if cached:
            return cached.copy()
        if self._use_remote:
            try:
                entity = self._table.get_entity(partition_key="task", row_key=task_id)
                data = self._entity_to_dict(entity)
                self._cache[task_id] = data.copy()
                return data
            except Exception:
                return None
        return None

    def list_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        # For hackathon simplicity return cached items; remote scan optional (costly for large tables)
        items = list(self._cache.values())
        items.sort(key=lambda x: x.get("updated_at", x.get("created_at", "")), reverse=True)
        return items[:limit]

    # ----------------------- Internal Helpers ----------------------- #

    def _prepare_entity(self, task_id: str, data: Dict[str, Any], is_new: bool) -> Dict[str, Any]:
        now = _utc_now_iso()
        base = {
            "PartitionKey": "task",
            "RowKey": task_id,
            "task_id": task_id,
            "updated_at": now,
        }
        if is_new:
            base["created_at"] = now
        # Flatten + ensure allowed scalar types (Tables supports str/int/bool/float/datetime/binary)
        for k, v in data.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                base[k] = v
            else:
                # Fallback serialize to string (small JSON-ish repr)
                base[k] = str(v)[:4000]
        return base

    def _entity_to_dict(self, entity: Any) -> Dict[str, Any]:  # type: ignore
        result = dict(entity)
        # Remove Table system keys except RowKey/PartitionKey
        return result


# Convenience singleton pattern (optional usage in app.py)
_task_store_singleton: Optional[TaskStore] = None


def get_task_store() -> TaskStore:
    global _task_store_singleton
    if _task_store_singleton is None:
        _task_store_singleton = TaskStore.from_env()
    return _task_store_singleton
