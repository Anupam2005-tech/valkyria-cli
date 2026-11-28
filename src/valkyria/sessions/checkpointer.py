"""
JSON-backed LangGraph checkpoint saver — durable interrupt/resume state with zero SQLite.
"""

from __future__ import annotations

import base64
import json
import threading
import uuid
from typing import TYPE_CHECKING, Any

from langgraph.checkpoint.memory import InMemorySaver

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from pathlib import Path

    from langchain_core.runnables import RunnableConfig
    from langgraph.checkpoint.base import (
        ChannelVersions,
        Checkpoint,
        CheckpointMetadata,
        CheckpointTuple,
    )
    from langgraph.checkpoint.serde.base import SerializerProtocol


def _encode_typed(pair: tuple[str, bytes]) -> list[str]:
    return [pair[0], base64.b64encode(pair[1]).decode("ascii")]


def _decode_typed(raw: list[str]) -> tuple[str, bytes]:
    return (str(raw[0]), base64.b64decode(raw[1].encode("ascii")))


class JsonFileSaver(InMemorySaver):
    """LangGraph checkpointer persisting per-thread state as JSON files (no SQLite)."""

    def __init__(
        self,
        checkpoints_dir: Path | None = None,
        *,
        serde: SerializerProtocol | None = None,
    ) -> None:
        super().__init__(serde=serde)
        self.checkpoints_dir = checkpoints_dir
        if self.checkpoints_dir is not None:
            self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self._loaded_threads: set[str] = set()
        self._lock = threading.RLock()

    def _thread_path(self, thread_id: str) -> Path | None:
        if self.checkpoints_dir is None:
            return None
        safe_id = thread_id.replace("/", "_")
        return self.checkpoints_dir / f"{safe_id}.json"

    def _ensure_loaded(self, thread_id: str) -> None:
        if thread_id in self._loaded_threads or self.checkpoints_dir is None:
            return
        self._loaded_threads.add(thread_id)
        path = self._thread_path(thread_id)
        if path is None or not path.exists():
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(payload, dict):
            return

        for ns, cp_map in payload.get("storage", {}).items():
            for cp_id, entry in cp_map.items():
                self.storage[thread_id][ns][cp_id] = (
                    _decode_typed(entry["checkpoint"]),
                    _decode_typed(entry["metadata"]),
                    entry.get("parent_checkpoint_id"),
                )

        for key_str, task_map in payload.get("writes", {}).items():
            parts = key_str.split("\x00", 2)
            if len(parts) != 3:
                continue
            tid_key = (parts[0], parts[1], parts[2])
            bucket = self.writes[tid_key]
            for item in task_map:
                bucket[(str(item["task_id"]), int(item["idx"]))] = (
                    str(item["task_id"]),
                    str(item["channel"]),
                    _decode_typed(item["value"]),
                    str(item.get("task_path", "")),
                )

        for blob_item in payload.get("blobs", []):
            version_raw = blob_item["version"]
            version: str | int | float = version_raw
            blob_key = (
                thread_id,
                str(blob_item["ns"]),
                str(blob_item["channel"]),
                version,
            )
            self.blobs[blob_key] = _decode_typed(blob_item["value"])

    def _flush_thread(self, thread_id: str) -> None:
        path = self._thread_path(thread_id)
        if path is None:
            return

        storage_out: dict[str, dict[str, Any]] = {}
        for ns, cp_map in self.storage.get(thread_id, {}).items():
            storage_out[ns] = {
                cp_id: {
                    "checkpoint": _encode_typed(cp_pair),
                    "metadata": _encode_typed(meta_pair),
                    "parent_checkpoint_id": parent_id,
                }
                for cp_id, (cp_pair, meta_pair, parent_id) in cp_map.items()
            }

        writes_out: dict[str, list[dict[str, Any]]] = {}
        for (tid, ns, cp_id), task_map in self.writes.items():
            if tid != thread_id:
                continue
            key_str = f"{tid}\x00{ns}\x00{cp_id}"
            writes_out[key_str] = [
                {
                    "task_id": task_id,
                    "idx": idx,
                    "channel": val[1],
                    "value": _encode_typed(val[2]),
                    "task_path": val[3],
                }
                for (task_id, idx), val in task_map.items()
            ]

        blobs_out: list[dict[str, Any]] = []
        for (tid, ns, ch, ver), blob_pair in self.blobs.items():
            if tid != thread_id:
                continue
            blobs_out.append(
                {
                    "ns": ns,
                    "channel": ch,
                    "version": ver,
                    "value": _encode_typed(blob_pair),
                }
            )

        data = {"storage": storage_out, "writes": writes_out, "blobs": blobs_out}
        tmp = path.with_name(f".{path.stem}.{uuid.uuid4().hex}.tmp")
        tmp.write_text(json.dumps(data) + "\n", encoding="utf-8")
        tmp.replace(path)

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        thread_id = str(config["configurable"]["thread_id"])
        with self._lock:
            self._ensure_loaded(thread_id)
            return super().get_tuple(config)

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,  # noqa: A002
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        with self._lock:
            if config is not None:
                tid = config.get("configurable", {}).get("thread_id")
                if tid:
                    self._ensure_loaded(str(tid))
            return iter(list(super().list(config, filter=filter, before=before, limit=limit)))

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        thread_id = str(config["configurable"]["thread_id"])
        with self._lock:
            self._ensure_loaded(thread_id)
            updated = super().put(config, checkpoint, metadata, new_versions)
            self._flush_thread(thread_id)
            return updated

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        thread_id = str(config["configurable"]["thread_id"])
        with self._lock:
            self._ensure_loaded(thread_id)
            super().put_writes(config, writes, task_id, task_path)
            self._flush_thread(thread_id)

    def delete_thread(self, thread_id: str) -> None:
        with self._lock:
            self._ensure_loaded(thread_id)
            super().delete_thread(thread_id)
            path = self._thread_path(thread_id)
            if path is not None and path.exists():
                path.unlink()

