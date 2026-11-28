"""Tests for Phase 9 read-only file access, chunking, embeddings, Pinecone RAG, and CLI."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

from click.testing import CliRunner
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import Field

from valkyria.chat.engine import ChatEngine, _handle_slash_command
from valkyria.cli.main import cli
from valkyria.core.config import PineconeConfig, ValkyriaConfig
from valkyria.providers.registry import ModelRegistry
from valkyria.rag.chunker import chunk_text
from valkyria.rag.embeddings import local_hash_embed, resolve_pinecone_api_key
from valkyria.rag.files import collect_indexable_files, read_workspace_file
from valkyria.rag.pinecone_store import PineconeRagStore, workspace_namespace
from valkyria.rag.pipeline import index_workspace_path, search_workspace_rag

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path


class _FakePineconeIndex:
    """In-memory mock of a Pinecone Index for unit tests."""

    def __init__(self) -> None:
        self.namespaces: dict[str, list[dict[str, Any]]] = {}

    def upsert(self, *, vectors: list[dict[str, Any]], namespace: str) -> None:
        bucket = self.namespaces.setdefault(namespace, [])
        by_id = {v["id"]: v for v in bucket}
        for vec in vectors:
            by_id[vec["id"]] = vec
        self.namespaces[namespace] = list(by_id.values())

    def query(
        self,
        *,
        vector: list[float],
        top_k: int,
        namespace: str,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        bucket = self.namespaces.get(namespace, [])
        scored: list[dict[str, Any]] = []
        for item in bucket:
            v2 = item["values"]
            score = sum(a * b for a, b in zip(vector, v2, strict=True))
            scored.append(
                {
                    "id": item["id"],
                    "score": score,
                    "metadata": item["metadata"] if include_metadata else {},
                }
            )
        scored.sort(key=lambda x: x["score"], reverse=True)
        return {"matches": scored[:top_k]}

    def describe_index_stats(self) -> dict[str, Any]:
        return {
            "namespaces": {
                ns: {"vector_count": len(items)} for ns, items in self.namespaces.items()
            }
        }

    def delete(self, *, delete_all: bool, namespace: str) -> None:
        if delete_all:
            self.namespaces.pop(namespace, None)


class _FakePineconeClient:
    """In-memory mock of pinecone.Pinecone."""

    def __init__(self) -> None:
        self.indexes: dict[str, tuple[int, _FakePineconeIndex]] = {}

    def has_index(self, name: str) -> bool:
        return name in self.indexes

    def create_index(self, *, name: str, dimension: int, metric: str, spec: object) -> None:
        self.indexes[name] = (dimension, _FakePineconeIndex())

    def describe_index(self, name: str) -> MagicMock:
        dim, _ = self.indexes[name]
        desc = MagicMock()
        desc.dimension = dim
        return desc

    def Index(self, name: str) -> _FakePineconeIndex:  # noqa: N802
        return self.indexes[name][1]


class _FakeRagChatModel(BaseChatModel):
    captured_messages: list[list[BaseMessage]] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "fake-rag"

    def bind_tools(self, tools: Any, **kwargs: Any) -> _FakeRagChatModel:
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        self.captured_messages.append(list(messages))
        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(
                        content="Using Pinecone.",
                        usage_metadata={"input_tokens": 30, "output_tokens": 5, "total_tokens": 35},
                    )
                )
            ]
        )

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        self.captured_messages.append(list(messages))
        chunk = AIMessageChunk(
            content="Using Pinecone.",
            usage_metadata={"input_tokens": 30, "output_tokens": 5, "total_tokens": 35},
        )
        if run_manager:
            await run_manager.on_llm_new_token("Using Pinecone.", chunk=chunk)
        yield ChatGenerationChunk(message=chunk)


class TestReadOnlyFileTool:
    """Tests for workspace-scoped file reading and collection."""

    def test_read_file_line_slice_and_escape_block(self, tmp_path: Path) -> None:
        target = tmp_path / "notes.md"
        target.write_text("line 1\nline 2\nline 3\nline 4\n")

        res = read_workspace_file(tmp_path, "notes.md", start_line=2, end_line=3)
        assert res.rel_path == "notes.md"
        assert res.content == "line 2\nline 3"
        assert res.total_lines == 4

        try:
            read_workspace_file(tmp_path, "../outside.txt")
            raise AssertionError("Expected PermissionError")
        except PermissionError:
            pass

    def test_binary_rejection_and_collect_indexable(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("def hello():\n    return 'world'\n")
        (tmp_path / "src" / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00")

        files = collect_indexable_files(tmp_path, "src")
        assert [rel for rel, _ in files] == ["src/main.py"]


class TestChunkerAndEnvResolution:
    """Tests for chunking, .env Pinecone key resolution, and local embeddings."""

    def test_chunk_text_line_ranges(self) -> None:
        text = "\n".join(f"line {i}: some content here" for i in range(1, 30))
        chunks = chunk_text("doc.py", text, max_chars=200, overlap_lines=2)
        assert len(chunks) >= 2
        assert chunks[0].start_line == 1
        assert chunks[0].id.startswith("chk_")
        assert chunks[1].start_line <= chunks[0].end_line

    def test_resolve_pinecone_key_from_dotenv(self, tmp_path: Path, monkeypatch: Any) -> None:
        monkeypatch.delenv("PINECONE_API_KEY", raising=False)
        (tmp_path / ".env").write_text("PINECONE_API_KEY=pcsk_from_dotenv_123\n")
        with patch("valkyria.rag.embeddings.get_config_dir", return_value=tmp_path / "cfg"):
            assert resolve_pinecone_api_key(tmp_path) == "pcsk_from_dotenv_123"

    def test_local_hash_embed_similarity(self) -> None:
        vecs = local_hash_embed(
            [
                "pinecone vector database indexing",
                "pinecone vector search query",
                "chocolate cake baking recipe",
            ],
            dim=256,
        )
        sim_related = sum(a * b for a, b in zip(vecs[0], vecs[1], strict=True))
        sim_unrelated = sum(a * b for a, b in zip(vecs[0], vecs[2], strict=True))
        assert sim_related > sim_unrelated


class TestPineconeRagPipeline:
    """Tests for Pinecone indexing, semantic search, and ChatEngine integration."""

    def test_index_and_search_with_mock_pinecone(self, tmp_path: Path) -> None:
        (tmp_path / "auth.py").write_text(
            "def verify_firebase_token(token):\n    return decode_jwt(token)\n"
        )
        (tmp_path / "cooking.md").write_text("Boil pasta in salted water for 8 minutes.\n")

        fake_pc = _FakePineconeClient()
        cfg = ValkyriaConfig(pinecone=PineconeConfig(index_name="test-idx"))
        store = PineconeRagStore(
            api_key="pcsk_test",
            pinecone_config=cfg.pinecone,
            workspace_root=tmp_path,
            client=fake_pc,
        )

        summary = index_workspace_path(tmp_path, ".", config=cfg, store=store)
        assert summary.files_indexed == 2
        assert summary.chunks_upserted == 2
        assert summary.namespace == workspace_namespace(tmp_path)
        assert store.stats()["vectors"] == 2

        hits, _ = search_workspace_rag(
            "firebase token decode", tmp_path, config=cfg, store=store, top_k=2
        )
        assert len(hits) == 2
        assert hits[0].rel_path == "auth.py"
        assert hits[0].citation == "auth.py:L1-L2"

    def test_chat_engine_slash_rag_and_auto_injection(self, tmp_path: Path) -> None:
        (tmp_path / "pinecone_notes.md").write_text(
            "Pinecone uses serverless namespaces per workspace.\n"
        )
        fake_pc = _FakePineconeClient()
        cfg = ValkyriaConfig(pinecone=PineconeConfig(index_name="test-idx"))
        store = PineconeRagStore(
            api_key="pcsk_test",
            pinecone_config=cfg.pinecone,
            workspace_root=tmp_path,
            client=fake_pc,
        )

        engine = ChatEngine(
            config=cfg,
            registry=ModelRegistry(),
            api_keys={"groq": "gsk_test"},
            initial_model="groq/llama-3.3-70b-versatile",
            workspace_root=tmp_path,
            auto_rag=True,
            rag_store=store,
        )

        assert _handle_slash_command("/read pinecone_notes.md", engine) is True
        assert _handle_slash_command("/index .", engine) is True
        assert _handle_slash_command("/search serverless namespaces", engine) is True

        fake_model = _FakeRagChatModel()

        with patch("valkyria.chat.clients.build_chat_model", return_value=fake_model):
            reply = asyncio.run(
                engine.send_turn("How does @pinecone_notes.md work with serverless namespaces?")
            )

        assert reply == "Using Pinecone."
        sent_messages = fake_model.captured_messages[0]
        combined_system = "\n".join(str(m.content) for m in sent_messages if m.type == "system")
        assert "pinecone_notes.md" in combined_system


class TestRagCli:
    """Tests for valkyria rag CLI subcommands."""

    def test_rag_status_and_help(self, tmp_path: Path, monkeypatch: Any) -> None:
        monkeypatch.delenv("PINECONE_API_KEY", raising=False)
        with (
            patch("valkyria.cli.rag_commands.detect_workspace_root", return_value=tmp_path),
            patch("valkyria.rag.embeddings.get_config_dir", return_value=tmp_path),
            patch("valkyria.core.config.get_config_path", return_value=tmp_path / "cfg.json"),
        ):
            runner = CliRunner()
            res_help = runner.invoke(cli, ["rag", "--help"])
            assert res_help.exit_code == 0
            assert "index" in res_help.output
            assert "search" in res_help.output

            res_status = runner.invoke(cli, ["rag", "status"])
            assert res_status.exit_code == 0
            assert "valkyria-rag" in res_status.output
            assert "missing" in res_status.output
            assert "Pinecone DB only" in res_status.output

            # Indexing without Pinecone key must refuse local fallback
            res_idx = runner.invoke(cli, ["rag", "index", "."])
            assert res_idx.exit_code == 1
            assert "Pinecone API key required" in res_idx.output
            assert not (tmp_path / "index").exists()
