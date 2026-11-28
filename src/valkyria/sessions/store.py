"""
SQLite session storage — durable sessions, auto-saved turns, fork, search, compact, checkpoints.

Database location: ~/.valkyrie/data/sessions.db (via get_sessions_db_path()).
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from valkyrie.chat.messages import ChatMessage, MessageRole, TokenUsage
from valkyrie.core.paths import get_sessions_db_path


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


class SessionStore:
    """SQLite-backed storage for chat sessions, messages, and checkpoints."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or get_sessions_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    workspace_root TEXT NOT NULL,
                    active_model TEXT NOT NULL,
                    total_prompt_tokens INTEGER NOT NULL DEFAULT 0,
                    total_completion_tokens INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_checkpoint_id TEXT
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    seq INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    model TEXT,
                    name TEXT,
                    tool_call_id TEXT,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    estimated INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session_seq
                    ON messages(session_id, seq);

                CREATE TABLE IF NOT EXISTS checkpoints (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    message_seq INTEGER NOT NULL,
                    active_model TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                """
            )

    @staticmethod
    def _row_to_session(row: sqlite3.Row, message_count: int = 0) -> SessionRecord:
        return SessionRecord(
            id=str(row["id"]),
            title=str(row["title"]),
            workspace_root=str(row["workspace_root"]),
            active_model=str(row["active_model"]),
            total_prompt_tokens=int(row["total_prompt_tokens"]),
            total_completion_tokens=int(row["total_completion_tokens"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            message_count=message_count,
            last_checkpoint_id=row["last_checkpoint_id"],
        )

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

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (
                    id, title, workspace_root, active_model,
                    total_prompt_tokens, total_completion_tokens,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, 0, 0, ?, ?)
                """,
                (session_id, resolved_title, ws, active_model, now, now),
            )

            msgs = initial_messages or []
            for seq, msg in enumerate(msgs):
                self._insert_message_row(conn, session_id, seq, msg)

        return SessionRecord(
            id=session_id,
            title=resolved_title,
            workspace_root=ws,
            active_model=active_model,
            total_prompt_tokens=0,
            total_completion_tokens=0,
            created_at=now,
            updated_at=now,
            message_count=sum(
                1 for m in (initial_messages or []) if m.role != MessageRole.SYSTEM
            ),
        )

    def _insert_message_row(
        self,
        conn: sqlite3.Connection,
        session_id: str,
        seq: int,
        msg: ChatMessage,
    ) -> None:
        conn.execute(
            """
            INSERT INTO messages (
                session_id, seq, role, content, model, name, tool_call_id,
                prompt_tokens, completion_tokens, estimated, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                seq,
                msg.role.value,
                msg.content,
                msg.model,
                msg.name,
                msg.tool_call_id,
                msg.usage.prompt_tokens if msg.usage else None,
                msg.usage.completion_tokens if msg.usage else None,
                1 if (msg.usage and msg.usage.estimated) else 0,
                msg.created_at,
            ),
        )

    def resolve_session_id(self, id_or_prefix: str) -> str | None:
        """Resolve an exact session ID or unique prefix."""
        with self._connect() as conn:
            exact = conn.execute(
                "SELECT id FROM sessions WHERE id = ?",
                (id_or_prefix,),
            ).fetchone()
            if exact is not None:
                return str(exact["id"])

            matches = conn.execute(
                "SELECT id FROM sessions WHERE id LIKE ? ORDER BY updated_at DESC",
                (f"{id_or_prefix}%",),
            ).fetchall()
            if len(matches) == 1:
                return str(matches[0]["id"])
        return None

    def get_session(self, session_id: str) -> SessionRecord | None:
        """Load a session by exact ID or unique prefix."""
        resolved = self.resolve_session_id(session_id)
        if resolved is None:
            return None

        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (resolved,),
            ).fetchone()
            if row is None:
                return None
            cnt = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id = ? AND role != 'system'",
                (resolved,),
            ).fetchone()[0]
            return self._row_to_session(row, int(cnt))

    def get_latest_session(self, workspace_root: str | None = None) -> SessionRecord | None:
        """Return the most recently updated session (scoped to workspace if provided)."""
        with self._connect() as conn:
            if workspace_root is not None:
                row = conn.execute(
                    "SELECT * FROM sessions WHERE workspace_root = ? "
                    "ORDER BY updated_at DESC LIMIT 1",
                    (workspace_root,),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT 1",
                ).fetchone()
            if row is None:
                return None
            cnt = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id = ? AND role != 'system'",
                (row["id"],),
            ).fetchone()[0]
            return self._row_to_session(row, int(cnt))

    def list_sessions(
        self,
        *,
        workspace_root: str | None = None,
        limit: int = 50,
    ) -> list[SessionRecord]:
        """List sessions ordered by most recently updated."""
        query = """
            SELECT s.*, COALESCE(m.cnt, 0) AS msg_count
            FROM sessions s
            LEFT JOIN (
                SELECT session_id, COUNT(*) AS cnt
                FROM messages
                WHERE role != 'system'
                GROUP BY session_id
            ) m ON m.session_id = s.id
        """
        params: list[Any] = []
        if workspace_root is not None:
            query += " WHERE s.workspace_root = ?"
            params.append(workspace_root)
        query += " ORDER BY s.updated_at DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_session(r, int(r["msg_count"])) for r in rows]

    def load_messages(self, session_id: str) -> list[ChatMessage]:
        """Load ordered messages for a session."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY seq ASC, id ASC",
                (session_id,),
            ).fetchall()

        messages: list[ChatMessage] = []
        for r in rows:
            usage: TokenUsage | None = None
            if r["prompt_tokens"] is not None or r["completion_tokens"] is not None:
                usage = TokenUsage(
                    prompt_tokens=int(r["prompt_tokens"] or 0),
                    completion_tokens=int(r["completion_tokens"] or 0),
                    estimated=bool(r["estimated"]),
                )
            messages.append(
                ChatMessage(
                    role=MessageRole(str(r["role"])),
                    content=str(r["content"]),
                    model=r["model"],
                    name=r["name"],
                    tool_call_id=r["tool_call_id"],
                    usage=usage,
                    created_at=str(r["created_at"]),
                )
            )
        return messages

    def append_message(self, session_id: str, msg: ChatMessage) -> None:
        """Append a message to a session and update token totals + timestamp."""
        now = _now_iso()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(seq), -1) AS max_seq FROM messages WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            next_seq = int(row["max_seq"]) + 1
            self._insert_message_row(conn, session_id, next_seq, msg)

            p_tok = msg.usage.prompt_tokens if msg.usage else 0
            c_tok = msg.usage.completion_tokens if msg.usage else 0
            conn.execute(
                """
                UPDATE sessions
                SET total_prompt_tokens = total_prompt_tokens + ?,
                    total_completion_tokens = total_completion_tokens + ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (p_tok, c_tok, now, session_id),
            )

    def replace_messages(self, session_id: str, messages: list[ChatMessage]) -> None:
        """Replace all stored messages for a session (used by clear/compact)."""
        now = _now_iso()
        with self._connect() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            for seq, msg in enumerate(messages):
                self._insert_message_row(conn, session_id, seq, msg)
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )

    def update_active_model(self, session_id: str, active_model: str) -> None:
        """Persist active model change for a session."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE sessions SET active_model = ?, updated_at = ? WHERE id = ?",
                (active_model, _now_iso(), session_id),
            )

    def rename_session(self, session_id: str, title: str) -> bool:
        """Rename a session. Returns True if found and updated."""
        resolved = self.resolve_session_id(session_id)
        if resolved is None:
            return False
        with self._connect() as conn:
            conn.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
                (title, _now_iso(), resolved),
            )
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
        pattern = f"%{query}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT s.*, COALESCE(cnt_tbl.cnt, 0) AS msg_count
                FROM sessions s
                LEFT JOIN messages m ON m.session_id = s.id
                LEFT JOIN (
                    SELECT session_id, COUNT(*) AS cnt
                    FROM messages
                    WHERE role != 'system'
                    GROUP BY session_id
                ) cnt_tbl ON cnt_tbl.session_id = s.id
                WHERE s.title LIKE ? OR m.content LIKE ?
                ORDER BY s.updated_at DESC
                """,
                (pattern, pattern),
            ).fetchall()
            return [self._row_to_session(r, int(r["msg_count"])) for r in rows]

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
        with self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (resolved,))
        return True

    def create_checkpoint(
        self,
        session_id: str,
        *,
        reason: str,
        state: dict[str, Any] | None = None,
    ) -> CheckpointRecord | None:
        """Save a durable checkpoint for a session (e.g. before an approval boundary)."""
        sess = self.get_session(session_id)
        if sess is None:
            return None

        cp_id = _new_id("cp")
        now = _now_iso()
        state_payload = state or {}

        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(seq), -1) AS max_seq FROM messages WHERE session_id = ?",
                (sess.id,),
            ).fetchone()
            max_seq = int(row["max_seq"])
            conn.execute(
                """
                INSERT INTO checkpoints (
                    id, session_id, message_seq, active_model, reason, state_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cp_id,
                    sess.id,
                    max_seq,
                    sess.active_model,
                    reason,
                    json.dumps(state_payload),
                    now,
                ),
            )
            conn.execute(
                "UPDATE sessions SET last_checkpoint_id = ?, updated_at = ? WHERE id = ?",
                (cp_id, now, sess.id),
            )

        return CheckpointRecord(
            id=cp_id,
            session_id=sess.id,
            message_seq=max_seq,
            active_model=sess.active_model,
            reason=reason,
            state=state_payload,
            created_at=now,
        )

    def get_latest_checkpoint(self, session_id: str) -> CheckpointRecord | None:
        """Retrieve the latest checkpoint for a session."""
        resolved = self.resolve_session_id(session_id)
        if resolved is None:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM checkpoints WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
                (resolved,),
            ).fetchone()
            if row is None:
                return None
            return CheckpointRecord(
                id=str(row["id"]),
                session_id=str(row["session_id"]),
                message_seq=int(row["message_seq"]),
                active_model=str(row["active_model"]),
                reason=str(row["reason"]),
                state=json.loads(str(row["state_json"])),
                created_at=str(row["created_at"]),
            )
