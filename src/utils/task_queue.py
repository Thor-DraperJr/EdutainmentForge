"""Simple Azure Storage Queue wrapper for task creation events.

Hackathon scope: only enqueue on task creation; no dequeue processing here.
"""
from __future__ import annotations

import os
import json
from typing import Optional, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

try:
    from azure.storage.queue import QueueClient  # type: ignore
    AZURE_QUEUE_AVAILABLE = True
except Exception:
    AZURE_QUEUE_AVAILABLE = False


class TaskQueue:
    def __init__(self, queue_client: Optional["QueueClient"], queue_name: str, use_remote: bool):
        self._client = queue_client
        self._queue_name = queue_name
        self._use_remote = use_remote and queue_client is not None

    @classmethod
    def from_env(cls) -> "TaskQueue":
        queue_name = os.getenv("TASK_QUEUE_NAME", "tasks")
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not AZURE_QUEUE_AVAILABLE:
            logger.warning("Azure Queue SDK not available; TaskQueue will be no-op.")
            return cls(None, queue_name, False)
        if not connection_string:
            logger.warning("No AZURE_STORAGE_CONNECTION_STRING set; TaskQueue will be no-op.")
            return cls(None, queue_name, False)
        try:
            client = QueueClient.from_connection_string(connection_string, queue_name)
            try:
                client.create_queue()
            except Exception:
                pass
            logger.info(f"TaskQueue using Azure Queue '{queue_name}'")
            return cls(client, queue_name, True)
        except Exception as e:
            logger.warning(f"Failed to init QueueClient: {e}; TaskQueue will be no-op")
            return cls(None, queue_name, False)

    def enqueue(self, message: Dict[str, Any]) -> None:
        if not self._use_remote:
            return
        try:
            body = json.dumps(message)[:60000]  # queue message size limit safeguard
            self._client.send_message(body)
        except Exception as e:
            logger.debug(f"Failed to enqueue message: {e}")


_task_queue_singleton: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    global _task_queue_singleton
    if _task_queue_singleton is None:
        _task_queue_singleton = TaskQueue.from_env()
    return _task_queue_singleton
