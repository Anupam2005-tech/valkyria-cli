"""
Embedding pipeline and Pinecone API key resolution.

Supports:
1. Hosted provider embeddings (Gemini embedContent or NVIDIA /embeddings)
2. Pinecone Inference API (llama-text-embed-v2) when Pinecone key is available
3. Deterministic local normalized hashing embeddings (zero-dependency offline fallback)
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
from dotenv import dotenv_values

from valkyria.core.config import PineconeConfig
from valkyria.core.paths import get_config_dir
from valkyria.providers.gemini import GEMINI_API_BASE
from valkyria.providers.nvidia import NVIDIA_API_BASE

if TYPE_CHECKING:
    from valkyria.core.config import ValkyriaConfig

_TOKEN_RE = re.compile(r"[a-z0-9_]+")
DEFAULT_LOCAL_DIM = 1024
_APP_ROOT = Path(__file__).resolve().parents[3]


def _read_env_var(name: str, workspace_root: Path | None = None) -> str | None:
    """Read an env setting from os.environ or .env chain without mutating os.environ."""
    direct = os.environ.get(name, "").strip()
    if direct:
        return direct

    candidates: list[Path] = []
    if workspace_root is not None:
        candidates.append(workspace_root / ".env")
    candidates.extend(
        [
            Path.cwd() / ".env",
            _APP_ROOT / ".env",
            get_config_dir() / ".env",
        ]
    )
    seen: set[Path] = set()
    for env_path in candidates:
        resolved = env_path.resolve()
        if resolved in seen or not resolved.exists():
            continue
        seen.add(resolved)
        values = dotenv_values(resolved)
        raw = values.get(name)
        if raw and raw.strip():
            return raw.strip()
    return None


def resolve_pinecone_api_key(
    workspace_root: Path | None = None,
    vault_keys: dict[str, str] | None = None,
) -> str | None:
    """
    Resolve PINECONE_API_KEY from environment or .env chain (app/workspace/cwd/config).

    Users are never required to enter a Pinecone key; it is configured by the app .env.
    """
    env_val = _read_env_var("PINECONE_API_KEY", workspace_root)
    if env_val:
        return env_val

    if vault_keys and vault_keys.get("pinecone"):
        return vault_keys["pinecone"].strip()
    return None


def resolve_pinecone_config(
    config: ValkyriaConfig,
    workspace_root: Path | None = None,
) -> PineconeConfig:
    """Resolve Pinecone index/cloud/region with .env overrides."""
    index_name = _read_env_var("PINECONE_INDEX", workspace_root) or config.pinecone.index_name
    cloud = _read_env_var("PINECONE_CLOUD", workspace_root) or config.pinecone.cloud
    region = _read_env_var("PINECONE_REGION", workspace_root) or config.pinecone.region
    return PineconeConfig(index_name=index_name, cloud=cloud, region=region)


def local_hash_embed(texts: list[str], *, dim: int = DEFAULT_LOCAL_DIM) -> list[list[float]]:
    """
    Deterministic normalized feature-hashing vector embedding (local, offline).
    """
    vectors: list[list[float]] = []
    for text in texts:
        vec = [0.0] * dim
        tokens = _TOKEN_RE.findall(text.lower())
        # Unigrams + character trigrams for robust code/identifier matching
        features = list(tokens)
        for tok in tokens:
            if len(tok) >= 4:
                features.extend(tok[i : i + 3] for i in range(len(tok) - 2))

        for feat in features:
            digest = hashlib.blake2b(feat.encode("utf-8"), digest_size=8).digest()
            val = int.from_bytes(digest, "big")
            idx = val % dim
            sign = 1.0 if ((val >> 63) & 1) == 0 else -1.0
            vec[idx] += sign

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0.0:
            vec = [v / norm for v in vec]
        else:
            vec[0] = 1.0
        vectors.append(vec)
    return vectors


def _embed_gemini(texts: list[str], model_id: str, api_key: str) -> list[list[float]]:
    """Call Gemini batchEmbedContents REST API."""
    url = f"{GEMINI_API_BASE}/models/{model_id}:batchEmbedContents"
    requests_body = [
        {"model": f"models/{model_id}", "content": {"parts": [{"text": t}]}}
        for t in texts
    ]
    resp = httpx.post(
        url,
        params={"key": api_key},
        json={"requests": requests_body},
        timeout=30.0,
    )
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()
    return [list(item["values"]) for item in data.get("embeddings", [])]


def _embed_nvidia(
    texts: list[str], model_id: str, api_key: str, input_type: str
) -> list[list[float]]:
    """Call NVIDIA NIM OpenAI-compatible embeddings endpoint."""
    resp = httpx.post(
        f"{NVIDIA_API_BASE}/embeddings",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model_id,
            "input": texts,
            "input_type": input_type,
            "encoding_format": "float",
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()
    return [list(item["embedding"]) for item in data.get("data", [])]


def _embed_pinecone_inference(
    texts: list[str],
    pinecone_api_key: str,
    input_type: str,
    model: str = "llama-text-embed-v2",
) -> list[list[float]]:
    """Call Pinecone hosted Inference API."""
    from pinecone import Pinecone

    pc = Pinecone(api_key=pinecone_api_key)
    res = pc.inference.embed(
        model=model,
        inputs=texts,
        parameters={"input_type": input_type, "truncate": "END"},
    )
    return [list(item["values"]) for item in res.data]


def embed_texts(
    texts: list[str],
    *,
    config: ValkyriaConfig,
    api_keys: dict[str, str] | None = None,
    pinecone_api_key: str | None = None,
    input_type: str = "passage",
    batch_size: int = 32,
    target_dim: int | None = None,
) -> tuple[list[list[float]], str]:
    """
    Embed texts using the configured mode, returning (vectors, backend_label).
    """
    if not texts:
        return [], "none"

    keys = api_keys or {}
    embed_model = config.models.embeddings

    # 1. Hosted provider embedding (Gemini / NVIDIA) when configured
    if config.embedding_mode in ("hosted", "pinecone") and embed_model and "/" in embed_model:
        pkey, mid = embed_model.split("/", 1)
        pkey_key = keys.get(pkey)
        if pkey_key:
            all_vecs: list[list[float]] = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                if pkey == "gemini":
                    all_vecs.extend(_embed_gemini(batch, mid, pkey_key))
                elif pkey == "nvidia":
                    all_vecs.extend(_embed_nvidia(batch, mid, pkey_key, input_type))
            if len(all_vecs) == len(texts):
                return all_vecs, f"hosted:{embed_model}"

    # 2. Pinecone Inference when Pinecone key is configured
    if pinecone_api_key and pinecone_api_key != "mock-key":
        try:
            all_vecs = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                all_vecs.extend(_embed_pinecone_inference(batch, pinecone_api_key, input_type))
            if len(all_vecs) == len(texts):
                return all_vecs, "pinecone:llama-text-embed-v2"
        except Exception:
            pass

    # 3. Deterministic normalized vectorization in-memory (stored strictly in Pinecone)
    dim = target_dim or DEFAULT_LOCAL_DIM
    return local_hash_embed(texts, dim=dim), f"hash-{dim}->pinecone"
