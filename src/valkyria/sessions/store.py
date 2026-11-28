"""
JSON session storage — durable sessions, auto-saved turns, fork, search, compact, checkpoints.

Sessions are persisted as JSON files under ~/.valkyria/data/sessions/ (via get_sessions_dir()).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from valkyria.chat.messages import ChatMessage, MessageRole, TokenUsage
from valkyria.core.paths import get_sessions_dir


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _new_id(prefix: str = "sess") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


@dataclass
class SessionRecord:
    """Metadata for a persisted conversation session."""

    id: str
    title: str
    workspace_root: str
    active_model: str
    total_prompt_tokens: int
    total_completion_tokens: int
    created_at: str
    updated_at: str
    message_count: int = 0
    last_checkpoint_id: str | None = None


@dataclass
class CheckpointRecord:
    """Durable checkpoint saved before consequential actions or approvals."""

    id: str
    session_id: str
    message_seq: int
    active_model: str
    reason: str
    state: dict[str, Any]
    created_at: str


def _serialize_message(msg: ChatMessage) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "role": msg.role.value,
        "content": msg.content,
        "model": msg.model,
        "name": msg.name,
        "tool_call_id": msg.tool_call_id,
        "tool_calls": msg.tool_calls,
        "created_at": msg.created_at,
        "usage": (
            {
                "prompt_tokens": msg.usage.prompt_tokens,
                "completion_tokens": msg.usage.completion_tokens,
                "estimated": msg.usage.estimated,
            }
            if msg.usage is not None
            else None
        ),
    }
    return payload


def _deserialize_message(raw: dict[str, Any]) -> ChatMessage:
    usage_raw = raw.get("usage")
    usage: TokenUsage | None = None
    if isinstance(usage_raw, dict):
        usage = TokenUsage(
            prompt_tokens=int(usage_raw.get("prompt_tokens", 0)),
            completion_tokens=int(usage_raw.get("completion_tokens", 0)),
            estimated=bool(usage_raw.get("estimated", False)),
        )
    return ChatMessage(
        role=MessageRole(str(raw["role"])),
        content=str(raw.get("content", "")),
        model=raw.get("model"),
        name=raw.get("name"),
        tool_call_id=raw.get("tool_call_id"),
        tool_calls=raw.get("tool_calls"),
        usage=usage,
        created_at=str(raw.get("created_at") or _now_iso()),
    )


class SessionStore:
    """JSON-file-backed storage for chat sessions, messages, and checkpoints."""

    def __init__(self, sessions_dir: Path | None = None) -> None:
        self.sessions_dir = sessions_dir or get_sessions_dir()
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"

    def _read_raw(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except (OSError, json.JSONDecodeError):
            return None

    def _write_raw(self, session_id: str, data: dict[str, Any]) -> None:
        target = self._session_path(session_id)
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        tmp.replace(target)

    @staticmethod
    def _to_record(data: dict[str, Any]) -> SessionRecord:
        messages = data.get("messages", [])
        msg_count = sum(
            1 for m in messages if isinstance(m, dict) and m.get("role") != MessageRole.SYSTEM.value
        )
        return SessionRecord(
            id=str(data["id"]),
            title=str(data["title"]),
            workspace_root=str(data["workspace_root"]),
            active_model=str(data["active_model"]),
            total_prompt_tokens=int(data.get("total_prompt_tokens", 0)),
            total_completion_tokens=int(data.get("total_completion_tokens", 0)),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            message_count=msg_count,
            last_checkpoint_id=data.get("last_checkpoint_id"),
        )

    def _iter_all_raw(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for file_path in self.sessions_dir.glob("*.json"):
            raw = self._read_raw(file_path)
            if raw is not None and "id" in raw:
                records.append(raw)
        records.sort(key=lambda r: str(r.get("updated_at", "")), reverse=True)
        return records

    def create_session(
        self,
        *,
        active_model: str,
        workspace_root: str | None = None,
        title: str | None = None,
        initial_messages: list[ChatMessage] | None = None,
    ) -> SessionRecord:
        """Create and persist a new session."""
        session_id = _new_id("sess")
        now = _now_iso()
        ws = workspace_root or str(Path.cwd())
        resolved_title = title or f"Session {now[:10]} {now[11:16]}"
        msgs = initial_messages or []

        payload: dict[str, Any] = {
            "id": session_id,
            "title": resolved_title,
            "workspace_root": ws,
            "active_model": active_model,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "created_at": now,
            "updated_at": now,
            "last_checkpoint_id": None,
            "messages": [_serialize_message(m) for m in msgs],
            "checkpoints": [],
        }
        self._write_raw(session_id, payload)
        return self._to_record(payload)

    def resolve_session_id(self, id_or_prefix: str) -> str | None:
        """Resolve an exact session ID or unique prefix."""
        exact = self._session_path(id_or_prefix)
        if exact.exists():
            return id_or_prefix

        matches = [
            str(r["id"]) for r in self._iter_all_raw() if str(r["id"]).startswith(id_or_prefix)
        ]
        if len(matches) == 1:
            return matches[0]
        return None

    def get_session(self, session_id: str) -> SessionRecord | None:
        """Load a session by exact ID or unique prefix."""
        resolved = self.resolve_session_id(session_id)
        if resolved is None:
            return None
        raw = self._read_raw(self._session_path(resolved))
        if raw is None:
            return None
        return self._to_record(raw)

    def get_latest_session(self, workspace_root: str | None = None) -> SessionRecord | None:
        """Return the most recently updated session (scoped to workspace if provided)."""
        for raw in self._iter_all_raw():
            if workspace_root is None or raw.get("workspace_root") == workspace_root:
                return self._to_record(raw)
        return None

    def list_sessions(
        self,
        *,
        workspace_root: str | None = None,
        limit: int = 50,
    ) -> list[SessionRecord]:
        """List sessions ordered by most recently updated."""
        results: list[SessionRecord] = []
        for raw in self._iter_all_raw():
            if workspace_root is not None and raw.get("workspace_root") != workspace_root:
                continue
            results.append(self._to_record(raw))
            if len(results) >= limit:
                break
        return results

    def load_messages(self, session_id: str) -> list[ChatMessage]:
        """Load ordered messages for a session."""
        resolved = self.resolve_session_id(session_id) or session_id
        raw = self._read_raw(self._session_path(resolved))
        if raw is None:
            return []
        return [
            _deserialize_message(item) for item in raw.get("messages", []) if isinstance(item, dict)
        ]

    def append_message(self, session_id: str, msg: ChatMessage) -> None:
        """Append a message to a session and update token totals + timestamp."""
        resolved = self.resolve_session_id(session_id) or session_id
        raw = self._read_raw(self._session_path(resolved))
        if raw is None:
            return
        raw.setdefault("messages", []).append(_serialize_message(msg))
        if msg.usage is not None:
            raw["total_prompt_tokens"] = int(raw.get("total_prompt_tokens", 0)) + (
                msg.usage.prompt_tokens
            )
            raw["total_completion_tokens"] = int(raw.get("total_completion_tokens", 0)) + (
                msg.usage.completion_tokens
            )
        raw["updated_at"] = _now_iso()
        self._write_raw(resolved, raw)

    def replace_messages(self, session_id: str, messages: list[ChatMessage]) -> None:
        """Replace all stored messages for a session (used by clear/compact)."""
        resolved = self.resolve_session_id(session_id) or session_id
        raw = self._read_raw(self._session_path(resolved))
        if raw is None:
            return
        raw["messages"] = [_serialize_message(m) for m in messages]
        raw["updated_at"] = _now_iso()
        self._write_raw(resolved, raw)

    def update_active_model(self, session_id: str, active_model: str) -> None:
        """Persist active model change for a session."""
        resolved = self.resolve_session_id(session_id) or session_id
        raw = self._read_raw(self._session_path(resolved))
        if raw is None:
            return
        raw["active_model"] = active_model
        raw["updated_at"] = _now_iso()
        self._write_raw(resolved, raw)

    def rename_session(self, session_id: str, title: str) -> bool:
        """Rename a session. Returns True if found and updated."""
        resolved = self.resolve_session_id(session_id)
        if resolved is None:
            return False
        raw = self._read_raw(self._session_path(resolved))
        if raw is None:
            return False
        raw["title"] = title
        raw["updated_at"] = _now_iso()
        self._write_raw(resolved, raw)
        return True

    def auto_title_if_default(self, session_id: str, first_user_prompt: str) -> None:
        """Set a concise title from the first user prompt if still using default timestamp title."""
        sess = self.get_session(session_id)
        if sess is None or not sess.title.startswith("Session "):
            return
        snippet = " ".join(first_user_prompt.strip().split())
        if len(snippet) > 48:
            snippet = snippet[:45] + "..."
        if snippet:
            self.rename_session(session_id, snippet)

    def fork_session(self, session_id: str, title: str | None = None) -> SessionRecord | None:
        """Clone an existing session and its message history into a new session."""
        src = self.get_session(session_id)
        if src is None:
            return None
        messages = self.load_messages(src.id)
        fork_title = title or f"Fork of {src.title}"
        return self.create_session(
            active_model=src.active_model,
            workspace_root=src.workspace_root,
            title=fork_title,
            initial_messages=messages,
        )

    def search_sessions(self, query: str) -> list[SessionRecord]:
        """Search sessions by title or message content."""
        needle = query.lower()
        matches: list[SessionRecord] = []
        for raw in self._iter_all_raw():
            title_match = needle in str(raw.get("title", "")).lower()
            msg_match = any(
                needle in str(m.get("content", "")).lower()
                for m in raw.get("messages", [])
                if isinstance(m, dict)
            )
            if title_match or msg_match:
                matches.append(self._to_record(raw))
        return matches

    def compact_session(
        self,
        session_id: str,
        summary_text: str,
        *,
        keep_last: int = 4,
    ) -> tuple[bool, int, int]:
        """
        Compact older turns of a session into a single summary message.

        Preserves the system message (if any) and the most recent `keep_last` turns.
        Returns (success, count_before, count_after).
        """
        resolved = self.resolve_session_id(session_id)
        if resolved is None:
            return False, 0, 0

        messages = self.load_messages(resolved)
        before_count = len(messages)

        system_msgs = [m for m in messages if m.role == MessageRole.SYSTEM]
        non_system = [m for m in messages if m.role != MessageRole.SYSTEM]

        if len(non_system) <= keep_last:
            return False, before_count, before_count

        tail = non_system[-keep_last:] if keep_last > 0 else []
        compacted_msg = ChatMessage(
            role=MessageRole.SYSTEM,
            content=f"[Compacted conversation summary]\n{summary_text.strip()}",
        )
        new_messages = [*system_msgs[:1], compacted_msg, *tail]
        self.replace_messages(resolved, new_messages)
        return True, before_count, len(new_messages)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its messages/checkpoints."""
        resolved = self.resolve_session_id(session_id)
        if resolved is None:
            return False
        path = self._session_path(resolved)
        if path.exists():
            path.unlink()
            return True
        return False

    def create_checkpoint(
        self,
        session_id: str,
        *,
        reason: str,
        state: dict[str, Any] | None = None,
    ) -> CheckpointRecord | None:
        """Save a durable checkpoint for a session (e.g. before an approval boundary)."""
        resolved = self.resolve_session_id(session_id)
        if resolved is None:
            return None
        raw = self._read_raw(self._session_path(resolved))
        if raw is None:
            return None

        cp_id = _new_id("cp")
        now = _now_iso()
        state_payload = state or {}
        max_seq = len(raw.get("messages", [])) - 1
        cp_dict = {
            "id": cp_id,
            "session_id": resolved,
            "message_seq": max_seq,
            "active_model": str(raw["active_model"]),
            "reason": reason,
            "state": state_payload,
            "created_at": now,
        }
        raw.setdefault("checkpoints", []).append(cp_dict)
        raw["last_checkpoint_id"] = cp_id
        raw["updated_at"] = now
        self._write_raw(resolved, raw)

        return CheckpointRecord(
            id=cp_id,
            session_id=resolved,
            message_seq=max_seq,
            active_model=str(raw["active_model"]),
            reason=reason,
            state=state_payload,
            created_at=now,
        )

    def get_latest_checkpoint(self, session_id: str) -> CheckpointRecord | None:
        """Retrieve the latest checkpoint for a session."""
        resolved = self.resolve_session_id(session_id)
        if resolved is None:
            return None
        raw = self._read_raw(self._session_path(resolved))
        if raw is None:
            return None
        checkpoints = raw.get("checkpoints", [])
        if not checkpoints:
            return None
        latest = max(checkpoints, key=lambda c: str(c.get("created_at", "")))
        return CheckpointRecord(
            id=str(latest["id"]),
            session_id=str(latest["session_id"]),
            message_seq=int(latest["message_seq"]),
            active_model=str(latest["active_model"]),
            reason=str(latest["reason"]),
            state=dict(latest.get("state", {})),
            created_at=str(latest["created_at"]),
        )
