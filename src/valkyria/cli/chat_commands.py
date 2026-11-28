"""
Chat CLI command — launch or resume a durable multi-model terminal chat session.
"""

from __future__ import annotations

import click

from valkyria.chat.engine import ChatEngine, build_system_prompt, run_chat_repl
from valkyria.chat.messages import ChatMessage, MessageRole
from valkyria.core.config import ValkyriaConfig
from valkyria.core.console import console, print_error, print_info, print_rule
from valkyria.core.workspace import detect_workspace_root
from valkyria.providers.registry import PROVIDERS, ModelRegistry
from valkyria.sessions.store import SessionStore
from valkyria.vault.prompt import verify_and_prompt
from valkyria.vault.store import get_key, vault_exists


@click.command()
@click.option(
    "--model",
    "model_override",
    default=None,
    help="Override chat model (<provider>/<model_id>).",
)
@click.option(
    "--new",
    "force_new",
    is_flag=True,
    default=False,
    help="Start a new session instead of resuming the latest one.",
)
@click.option(
    "--session",
    "session_id",
    default=None,
    help="Resume a specific session by ID (or unique prefix).",
)
def chat(model_override: str | None, force_new: bool, session_id: str | None) -> None:
    """Start or resume an interactive chat session."""
    config = ValkyriaConfig.load()
    registry = ModelRegistry.load_cache()
    store = SessionStore()
    ws_root = detect_workspace_root()
    workspace = str(ws_root)

    # Resolve target session (explicit ID -> latest for workspace -> new)
    existing_session = None
    if session_id is not None:
        existing_session = store.get_session(session_id)
        if existing_session is None:
            print_error(f"Session '{session_id}' not found.")
            raise SystemExit(1)
    elif not force_new:
        existing_session = store.get_latest_session(workspace_root=workspace)

    selected_model = model_override or (
        existing_session.active_model if existing_session else config.models.chat
    )
    if not selected_model:
        console.print()
        print_rule("Chat")
        print_error("No chat model configured.")
        print_info(
            "Run [bold]valkyria setup[/bold] or "
            "[bold]valkyria model set chat <provider>/<model>[/bold]."
        )
        console.print()
        raise SystemExit(1)

    if "/" not in selected_model:
        print_error("Model must be in <provider>/<model_id> format.")
        raise SystemExit(1)

    if not vault_exists():
        print_error("No key vault found. Run [bold]valkyria keys add[/bold] first.")
        raise SystemExit(1)

    console.print()
    print_info("Unlock vault to start chat session.")
    password = verify_and_prompt(action="unlock API keys for chat")
    if password is None:
        raise SystemExit(1)

    api_keys: dict[str, str] = {}
    for pkey in PROVIDERS:
        key = get_key(password, pkey)
        if key:
            api_keys[pkey] = key

    provider_key, _ = selected_model.split("/", 1)
    if provider_key not in api_keys:
        print_error(f"No API key found in vault for provider '{provider_key}'.")
        raise SystemExit(1)

    if existing_session is not None:
        loaded_messages = store.load_messages(existing_session.id)
        if model_override and model_override != existing_session.active_model:
            store.update_active_model(existing_session.id, model_override)
        print_info(
            f"Resuming session [bold]{existing_session.title}[/bold] "
            f"([dim]{existing_session.id}[/dim], {existing_session.message_count} messages)"
        )
        engine = ChatEngine(
            config=config,
            registry=registry,
            api_keys=api_keys,
            initial_model=selected_model,
            session_store=store,
            session_id=existing_session.id,
            initial_messages=loaded_messages,
            total_prompt_tokens=existing_session.total_prompt_tokens,
            total_completion_tokens=existing_session.total_completion_tokens,
            workspace_root=ws_root,
        )
    else:
        sys_msg = ChatMessage(
            role=MessageRole.SYSTEM,
            content=build_system_prompt(config, ws_root),
        )
        created = store.create_session(
            active_model=selected_model,
            workspace_root=workspace,
            initial_messages=[sys_msg],
        )
        print_info(f"Started new session [dim]{created.id}[/dim]")
        engine = ChatEngine(
            config=config,
            registry=registry,
            api_keys=api_keys,
            initial_model=selected_model,
            session_store=store,
            session_id=created.id,
            initial_messages=[sys_msg],
            workspace_root=ws_root,
        )

    run_chat_repl(engine)
