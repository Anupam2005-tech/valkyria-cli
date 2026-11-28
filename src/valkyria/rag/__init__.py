"""RAG module — read-only workspace file access, chunking, embeddings, and Pinecone DB."""

from valkyrie.rag.chunker import DocumentChunk, chunk_text
from valkyrie.rag.embeddings import embed_texts, local_hash_embed, resolve_pinecone_api_key
from valkyrie.rag.files import FileReadResult, collect_indexable_files, read_workspace_file
from valkyrie.rag.pinecone_store import PineconeRagStore, SearchHit, workspace_namespace
from valkyrie.rag.pipeline import (
    IndexSummary,
    format_rag_context,
    get_pinecone_store,
    index_workspace_path,
    search_workspace_rag,
)

__all__ = [
    "DocumentChunk",
    "FileReadResult",
    "IndexSummary",
    "PineconeRagStore",
    "SearchHit",
    "chunk_text",
    "collect_indexable_files",
    "embed_texts",
    "format_rag_context",
    "get_pinecone_store",
    "index_workspace_path",
    "local_hash_embed",
    "read_workspace_file",
    "resolve_pinecone_api_key",
    "search_workspace_rag",
    "workspace_namespace",
]
