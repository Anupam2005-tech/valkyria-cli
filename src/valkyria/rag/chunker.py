"""
Line-aware document chunker with deterministic IDs for Pinecone upsert.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass
class DocumentChunk:
    """A contiguous slice of a workspace file with line-range metadata."""

    id: str
    rel_path: str
    start_line: int
    end_line: int
    text: str


def _chunk_id(rel_path: str, chunk_index: int) -> str:
    digest = hashlib.sha256(f"{rel_path}:{chunk_index}".encode()).hexdigest()[:24]
    return f"chk_{digest}"


def chunk_text(
    rel_path: str,
    content: str,
    *,
    max_chars: int = 1200,
    overlap_lines: int = 3,
) -> list[DocumentChunk]:
    """
    Split text into overlapping line-bounded chunks suitable for vector indexing.
    """
    lines = content.splitlines()
    if not lines:
        return []

    chunks: list[DocumentChunk] = []
    idx = 0
    chunk_num = 0
    n = len(lines)

    while idx < n:
        start = idx
        char_count = 0
        end = idx
        while end < n:
            line_len = len(lines[end]) + 1
            if end > start and char_count + line_len > max_chars:
                break
            char_count += line_len
            end += 1

        chunk_body = "\n".join(lines[start:end]).strip()
        if chunk_body:
            chunks.append(
                DocumentChunk(
                    id=_chunk_id(rel_path, chunk_num),
                    rel_path=rel_path,
                    start_line=start + 1,
                    end_line=end,
                    text=chunk_body,
                )
            )
            chunk_num += 1

        if end >= n:
            break
        idx = max(start + 1, end - overlap_lines)

    return chunks

