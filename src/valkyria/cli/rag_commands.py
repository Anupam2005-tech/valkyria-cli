"""
RAG CLI commands — index workspace files, semantic search via Pinecone, and inspect status.
"""

from __future__ import annotations

import click

from valkyrie.core.cards import render_tool_card
from valkyrie.core.config import ValkyrieConfig
from valkyrie.core.console import (
    console,
    print_error,
    print_info,
    print_kv,
    print_rule,
    print_success,
    print_warning,
)
from valkyrie.core.workspace import detect_workspace_root
from valkyrie.rag.embeddings import resolve_pinecone_api_key, resolve_pinecone_config
from valkyrie.rag.pipeline import (
    get_workspace_rag_store,
    index_workspace_path,
    search_workspace_rag,
)


@click.group()
def rag() -> None:
    """Index workspace documents and search with Pinecone DB (.env configured)."""
    pass


@rag.command()
@click.argument("target", default=".")
def index(target: str) -> None:
    """Index a workspace file or directory into Pinecone DB."""
    ws_root = detect_workspace_root()
    config = ValkyrieConfig.load()
    pc_key = resolve_pinecone_api_key(ws_root)
    pc_cfg = resolve_pinecone_config(config, ws_root)

    console.print()
    print_rule("Pinecone Index")
    console.print()
    print_info(
        f"Data transfer: workspace chunks from [bold]{target}[/bold] -> "
        f"Pinecone index [accent]{pc_cfg.index_name}[/accent]"
    )

    try:
        summary = index_workspace_path(
            ws_root,
            target,
            config=config,
            pinecone_api_key=pc_key,
        )
    except Exception as exc:
        print_error(f"Indexing failed: {exc}")
        console.print()
        raise SystemExit(1) from exc

    render_tool_card(
        tool="index",
        status="ok",
        target=target,
        summary=(
            f"Indexed {summary.files_indexed} files ({summary.chunks_upserted} chunks) "
            f"into {summary.index_name} [{summary.namespace}] via {summary.embedding_backend}"
        ),
    )
    console.print()


@rag.command()
@click.argument("query")
@click.option("--top-k", default=5, show_default=True, help="Maximum results to return.")
def search(query: str, top_k: int) -> None:
    """Search indexed workspace documents in Pinecone with source citations."""
    ws_root = detect_workspace_root()
    config = ValkyrieConfig.load()
    pc_key = resolve_pinecone_api_key(ws_root)

    console.print()
    print_rule(f"Pinecone Search · {query}")
    console.print()

    try:
        hits, backend = search_workspace_rag(
            query,
            ws_root,
            config=config,
            pinecone_api_key=pc_key,
            top_k=top_k,
        )
    except Exception as exc:
        print_error(f"Search failed: {exc}")
        console.print()
        raise SystemExit(1) from exc

    if not hits:
        print_warning("No matching chunks found. Run 'valkyrie rag index' first.")
        console.print()
        return

    print_info(f"Query embedded with [dim]{backend}[/dim] -> {len(hits)} citation(s)")
    console.print()
    for hit in hits:
        preview = " ".join(hit.text.splitlines()[:3])
        if len(preview) > 200:
            preview = preview[:197] + "..."
        render_tool_card(
            tool="citation",
            status="ok",
            target=hit.citation,
            summary=f"similarity score: {hit.score:.3f}",
            details=preview,
        )
    console.print()


@rag.command()
def status() -> None:
    """Show Pinecone retrieval configuration and workspace vector count."""
    ws_root = detect_workspace_root()
    config = ValkyrieConfig.load()
    pc_key = resolve_pinecone_api_key(ws_root)
    pc_cfg = resolve_pinecone_config(config, ws_root)

    console.print()
    print_rule("Pinecone RAG Status")
    console.print()
    print_kv("Workspace", str(ws_root))
    print_kv("Storage", "Pinecone DB only (zero local vector storage)")
    print_kv("Embedding mode", config.embedding_mode)
    print_kv("Index name", pc_cfg.index_name)
    print_kv("Cloud / Region", f"{pc_cfg.cloud} / {pc_cfg.region}")
    print_kv(
        "Pinecone backend",
        "[green]connected (.env)[/green]" if pc_key else "[yellow]missing in .env[/yellow]",
    )
    if pc_key:
        store = get_workspace_rag_store(
            workspace_root=ws_root,
            config=config,
            pinecone_api_key=pc_key,
        )
        print_kv("Namespace", store.namespace)
        try:
            info = store.stats()
            vec_str = str(info["vectors"]) if info["index_exists"] else "index not created yet"
            print_kv("Vectors", vec_str)
        except Exception as exc:
            print_warning(f"Could not reach Pinecone: {exc}")
    console.print()


@rag.command()
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def clear(yes: bool) -> None:
    """Clear the current workspace's local or hosted index."""
    ws_root = detect_workspace_root()
    config = ValkyrieConfig.load()
    pc_key = resolve_pinecone_api_key(ws_root)

    console.print()
    try:
        store = get_workspace_rag_store(
            workspace_root=ws_root,
            config=config,
            pinecone_api_key=pc_key,
        )
    except RuntimeError as exc:
        print_error(str(exc))
        console.print()
        raise SystemExit(1) from exc

    if not yes and not click.confirm(
        f"  Delete all indexed chunks in namespace '{store.namespace}'?", default=False
    ):
        print_info("Cancelled.")
        console.print()
        return

    if store.clear_workspace():
        print_success(f"Cleared index namespace [dim]{store.namespace}[/dim].")
    else:
        print_info("The index is empty.")
    console.print()

