"""
RAG pipeline helpers — coordinate file collection, chunking, embedding, and Pinecone DB.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from valkyria.rag.chunker import DocumentChunk, chunk_text
from valkyria.rag.embeddings import (
    embed_texts,
    resolve_pinecone_api_key,
    resolve_pinecone_config,
)
from valkyria.rag.files import collect_indexable_files
from valkyria.rag.pinecone_store import PineconeRagStore, SearchHit

if TYPE_CHECKING:
    from pathlib import Path

    from valkyria.core.config import ValkyriaConfig


@dataclass
class IndexSummary:
    """Summary of an indexing run."""

    files_indexed: int
    chunks_upserted: int
    embedding_backend: str
    index_name: str
    namespace: str


def get_pinecone_store(
    *,
    workspace_root: Path,
    config: ValkyriaConfig,
    api_keys: dict[str, str] | None = None,
    pinecone_api_key: str | None = None,
    client: Any | None = None,
) -> PineconeRagStore | None:
    """Build a PineconeRagStore if a Pinecone API key is available."""
    resolved_key = pinecone_api_key or resolve_pinecone_api_key(workspace_root, api_keys)
    if not resolved_key and client is None:
        return None
    pc_cfg = resolve_pinecone_config(config, workspace_root)
    return PineconeRagStore(
        api_key=resolved_key or "mock-key",
        pinecone_config=pc_cfg,
        workspace_root=workspace_root,
        client=client,
    )


def get_workspace_rag_store(
    *,
    workspace_root: Path,
    config: ValkyriaConfig,
    api_keys: dict[str, str] | None = None,
    pinecone_api_key: str | None = None,
) -> PineconeRagStore:
    """Return the Pinecone DB store (RAG vectors are stored exclusively in Pinecone)."""
    store = get_pinecone_store(
        workspace_root=workspace_root,
        config=config,
        api_keys=api_keys,
        pinecone_api_key=pinecone_api_key,
    )
    if store is None:
        raise RuntimeError(
            "Pinecone API key required (RAG data is stored exclusively in Pinecone, "
            "never locally). Configure PINECONE_API_KEY in the application .env file."
        )
    return store


def index_workspace_path(
    workspace_root: Path,
    target: str,
    *,
    config: ValkyriaConfig,
    api_keys: dict[str, str] | None = None,
    pinecone_api_key: str | None = None,
    store: PineconeRagStore | None = None,
) -> IndexSummary:
    """Collect, chunk, embed, and upsert workspace files into Pinecone DB."""
    rag_store = store or get_workspace_rag_store(
        workspace_root=workspace_root,
        config=config,
        api_keys=api_keys,
        pinecone_api_key=pinecone_api_key,
    )

    files = collect_indexable_files(workspace_root, target)
    all_chunks: list[DocumentChunk] = []
    for rel_path, full_path in files:
        content = full_path.read_text(encoding="utf-8", errors="replace")
        all_chunks.extend(chunk_text(rel_path, content))

    if not all_chunks:
        return IndexSummary(
            files_indexed=len(files),
            chunks_upserted=0,
            embedding_backend="none",
            index_name=rag_store.config.index_name,
            namespace=rag_store.namespace,
        )

    existing_dim = rag_store.index_dimension()
    vectors, backend = embed_texts(
        [c.text for c in all_chunks],
        config=config,
        api_keys=api_keys,
        pinecone_api_key=getattr(rag_store, "api_key", pinecone_api_key),
        input_type="passage",
        target_dim=existing_dim,
    )
    upserted = rag_store.upsert_chunks(all_chunks, vectors)
    return IndexSummary(
        files_indexed=len(files),
        chunks_upserted=upserted,
        embedding_backend=backend,
        index_name=rag_store.config.index_name,
        namespace=rag_store.namespace,
    )


def search_workspace_rag(
    query: str,
    workspace_root: Path,
    *,
    config: ValkyriaConfig,
    api_keys: dict[str, str] | None = None,
    pinecone_api_key: str | None = None,
    store: PineconeRagStore | None = None,
    top_k: int = 5,
) -> tuple[list[SearchHit], str]:
    """Embed a query and search the workspace's Pinecone namespace."""
    rag_store = store or get_workspace_rag_store(
        workspace_root=workspace_root,
        config=config,
        api_keys=api_keys,
        pinecone_api_key=pinecone_api_key,
    )
    existing_dim = rag_store.index_dimension()
    vectors, backend = embed_texts(
        [query],
        config=config,
        api_keys=api_keys,
        pinecone_api_key=getattr(rag_store, "api_key", pinecone_api_key),
        input_type="query",
        target_dim=existing_dim,
    )
    if not vectors:
        return [], backend
    hits = rag_store.query(vectors[0], top_k=top_k)
    return hits, backend


def format_rag_context(hits: list[SearchHit]) -> str:
    """Format search hits as cited context for LLM prompt injection."""
    if not hits:
        return ""
    blocks = [
        f"[Source: {h.citation} | score={h.score:.3f}]\n{h.text}"
        for h in hits
    ]
    return "Relevant workspace context:\n\n" + "\n\n---\n\n".join(blocks)
