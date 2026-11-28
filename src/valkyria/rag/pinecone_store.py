"""
Pinecone DB vector store — index lifecycle, workspace namespaces, upsert, and search.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pinecone import Pinecone, ServerlessSpec

if TYPE_CHECKING:
    from pathlib import Path

    from valkyria.core.config import PineconeConfig
    from valkyria.rag.chunker import DocumentChunk


@dataclass
class SearchHit:
    """Single semantic search match returned from Pinecone."""

    rel_path: str
    start_line: int
    end_line: int
    score: float
    text: str

    @property
    def citation(self) -> str:
        return f"{self.rel_path}:L{self.start_line}-L{self.end_line}"


def workspace_namespace(workspace_root: Path) -> str:
    """Deterministic Pinecone namespace per workspace root."""
    digest = hashlib.sha256(str(workspace_root.resolve()).encode("utf-8")).hexdigest()[:12]
    return f"ws_{digest}"


class PineconeRagStore:
    """Manages vector indexing and semantic search in Pinecone DB."""

    def __init__(
        self,
        *,
        api_key: str,
        pinecone_config: PineconeConfig,
        workspace_root: Path,
        client: Any | None = None,
    ) -> None:
        self.api_key = api_key
        self.config = pinecone_config
        self.workspace_root = workspace_root
        self.namespace = workspace_namespace(workspace_root)
        self._pc: Any = client or Pinecone(api_key=api_key)

    def ensure_index(self, dimension: int) -> int:
        """
        Ensure the configured Pinecone index exists, creating a serverless index if needed.

        Returns the active index vector dimension.
        """
        if not self._pc.has_index(self.config.index_name):
            self._pc.create_index(
                name=self.config.index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=self.config.cloud,
                    region=self.config.region,
                ),
            )
            return dimension

        desc = self._pc.describe_index(self.config.index_name)
        existing_dim = getattr(desc, "dimension", None)
        return int(existing_dim) if existing_dim else dimension

    def index_dimension(self) -> int | None:
        """Return existing index dimension if the index exists, else None."""
        if not self._pc.has_index(self.config.index_name):
            return None
        desc = self._pc.describe_index(self.config.index_name)
        dim = getattr(desc, "dimension", None)
        return int(dim) if dim else None

    def upsert_chunks(
        self,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
        *,
        batch_size: int = 50,
    ) -> int:
        """Upsert document chunks and embeddings into the workspace Pinecone namespace."""
        if not chunks or len(chunks) != len(vectors):
            return 0

        self.ensure_index(len(vectors[0]))
        index = self._pc.Index(self.config.index_name)
        upserted = 0

        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            batch_vecs = vectors[i : i + batch_size]
            payload = [
                {
                    "id": ch.id,
                    "values": vec,
                    "metadata": {
                        "path": ch.rel_path,
                        "start_line": ch.start_line,
                        "end_line": ch.end_line,
                        "text": ch.text[:2000],
                    },
                }
                for ch, vec in zip(batch_chunks, batch_vecs, strict=True)
            ]
            index.upsert(vectors=payload, namespace=self.namespace)
            upserted += len(payload)

        return upserted

    def query(
        self,
        query_vector: list[float],
        *,
        top_k: int = 5,
    ) -> list[SearchHit]:
        """Query the workspace Pinecone namespace and return ranked citations."""
        if not self._pc.has_index(self.config.index_name):
            return []

        index = self._pc.Index(self.config.index_name)
        res = index.query(
            vector=query_vector,
            top_k=top_k,
            namespace=self.namespace,
            include_metadata=True,
        )

        hits: list[SearchHit] = []
        matches = getattr(res, "matches", None) or (
            res.get("matches", []) if isinstance(res, dict) else []
        )
        for m in matches:
            meta = getattr(m, "metadata", None) or (
                m.get("metadata", {}) if isinstance(m, dict) else {}
            )
            score = float(
                getattr(m, "score", None)
                or (m.get("score", 0.0) if isinstance(m, dict) else 0.0)
            )
            hits.append(
                SearchHit(
                    rel_path=str(meta.get("path", "unknown")),
                    start_line=int(meta.get("start_line", 1)),
                    end_line=int(meta.get("end_line", 1)),
                    score=score,
                    text=str(meta.get("text", "")),
                )
            )
        return hits

    def stats(self) -> dict[str, Any]:
        """Return vector count for the current workspace namespace."""
        if not self._pc.has_index(self.config.index_name):
            return {"index_exists": False, "vectors": 0}

        index = self._pc.Index(self.config.index_name)
        raw = index.describe_index_stats()
        namespaces = getattr(raw, "namespaces", None) or (
            raw.get("namespaces", {}) if isinstance(raw, dict) else {}
        )
        ns_info = namespaces.get(self.namespace)
        if ns_info is None:
            count = 0
        elif isinstance(ns_info, dict):
            count = int(ns_info.get("vector_count", 0))
        else:
            count = int(getattr(ns_info, "vector_count", 0))
        return {"index_exists": True, "vectors": count}

    def clear_workspace(self) -> bool:
        """Delete all vectors in the current workspace namespace."""
        if not self._pc.has_index(self.config.index_name):
            return False
        index = self._pc.Index(self.config.index_name)
        index.delete(delete_all=True, namespace=self.namespace)
        return True

