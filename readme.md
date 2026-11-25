# Valkyrie CLI — Product and Engineering Specification

**Status:** Design specification  
**Version:** 1.0 draft  
**Date:** 25 November 2026  
**Product:** Terminal-first, multi-model AI agent with local retrieval, controlled system access, and durable sessions

---

## 1. Product intent

Valkyrie CLI is an AI workspace that runs in a terminal. It answers questions, helps write and edit code, searches local material, creates plans, and carries out approved tasks. Users bring API keys for Groq, Gemini, and NVIDIA. They choose the exact model used for each kind of work. The product keeps its retrieval index and execution history on the user's machine, while making every transfer to a hosted provider visible.

The defining experience is **a precise, fast terminal tool with an editorial voice**: concise, confident, occasionally sassy, and always useful. Its interface should feel designed by people who build developer tools, not like a generic AI chat screen. The personality belongs in microcopy and rhythm, never in permission prompts, errors that need diagnosis, or safety decisions.

### 1.1 Product promises

1. A user can enter one or more provider keys, see the models available to those keys, and assign models to tasks.
2. A user can understand what the agent is doing, what data leaves the machine, and what action requires approval.
3. A session survives process restarts and can be resumed, forked, searched, renamed, compacted, or deleted.
4. Local documents can be indexed and searched without a cloud vector database.
5. Files and commands are controlled by scoped permissions, previews, snapshots, limits, and an audit trail.
6. The CLI remains useful in narrow terminals, over SSH, and without full TUI support.

### 1.2 Primary users

| User | Main job | Need |
|---|---|---|
| Developer | Understand and change a codebase | Fast context, diffs, command transparency, undo |
| Technical researcher | Search documents and compare evidence | Source citations, local indexing, clear provenance |
| Power user | Inspect and automate a workstation | Explicit scopes, dry runs, reliable approvals |
| Multi-model user | Assign the right model to each task | Live catalog, capabilities, cost visibility where available |

### 1.3 Non-goals for initial release

- A desktop GUI or web chat product.
- Autonomous operation without a user-visible approval boundary.
- Cloud hosting of document indexes or raw local files.
- Team administration, shared workspaces, or billing aggregation.
- Running hosted provider models offline.
- Guaranteeing an undo of arbitrary shell commands or external side effects.

## 2. Scope and release definitions

**MVP:** Login, local key vault, provider model discovery, model assignments, chat, sessions, context accounting, read-only local file access, basic local RAG, and a polished terminal interface.

**Beta:** Plan/build, previewed file edits, scoped approvals, snapshots and undo, safe command execution, package management in isolated environments, hybrid search, session sync, and audit export.

**V1:** Vision, web search, robust offline behavior, advanced ingestion, security hardening, accessibility and cross-platform certification.

Feature flags must prevent unfinished tools from appearing as executable commands. Help may show a clearly marked upcoming feature only in development builds.

## 3. Experience principles

1. **The prompt stays the center.** One active input line; information appears only when relevant.
2. **Show the receipt.** Before a consequential action, show target, scope, exact operation, expected effect, and recovery option.
3. **Disclose model and data path.** The active model is always visible; any hosted request involving local content is clear.
4. **Never make confidence decorative.** Unknown capability, token limit, or cost is shown as unknown.
5. **Speed is visual.** Immediate input response, streamed output, stable layout, and no theatrical loading animation.
6. **Voice is earned.** Personality can sharpen a success message; critical prompts remain neutral and exact.

## 4. User journeys

### 4.1 First run

1. `valkyrie` starts and checks local configuration.
2. If signed out, show `valkyrie login` with a short explanation of the browser handoff.
3. After login, ask which providers to connect. At least one hosted model provider is required for chat; the user may return later to add more.
4. Read each API key with masked, no-echo input. Never put a key in a command-line argument or shell history.
5. Validate credentials and fetch the provider catalog. Show accessible models, grouped by capability. A list result alone does not guarantee invocation rights; a low-cost probe validates the selected model when feasible.
6. Ask for the user's preferred name, profession, and expertise level. All are optional; **do not ask for known languages or tone**.
7. Assign models to chat, code, planner, vision, and summarization. Embeddings are configured separately because they have a different data-transfer implication. Only show models that support the role; allow `unassigned` for optional roles.
8. Display a review screen: providers, role assignments, local/hosted embedding mode, sync setting, and a plain-language privacy summary. Save only after confirmation.
9. Open a new session and show one sample action, not a long tutorial.

### 4.2 Daily use

1. Launch in the current directory; that directory is the suggested workspace root.
2. Resume the last session unless the user requests `--new` or a specific session.
3. Type a question or use a slash command. `/` lists commands; a partial command filters them. `@` suggests accessible workspace paths.
4. The assistant streams output. Tool actions appear as compact cards with status and expandable details.
5. Approvals pause the agent and accept an explicit choice. The agent resumes from a durable checkpoint.

### 4.3 Model change

1. `/model` shows current session model and role assignments.
2. `/model list` shows the models available under configured keys, with provider, capability, status, and known limits.
3. `/model refresh` refetches catalogs. `/model set code <provider>/<model>` changes an assignment. `/model use <provider>/<model>` overrides the current session's chat model.
4. Before switching, recalculate context budget. If the existing context will not fit, offer compaction or a new session.
5. If a selected model is retired, inaccessible, or incompatible, explain the exact failure and offer compatible choices. Never silently substitute a model for a paid or privacy-sensitive request.

## 5. Interface design specification

### 5.1 Visual direction

The visual language is **editorial terminal**: a restrained grid, strong type hierarchy, sharp rules, meaningful whitespace, and one vivid functional accent. It should feel like an excellent developer instrument rather than a dashboard rendered in monospace. No gradients, glass effects, decorative stars, robot imagery, fake code rain, or generic glowing chat bubbles. Do not add emojis or decorative icons. Use text, rules, spacing, and color to convey structure. ASCII or Unicode box characters are allowed when they improve clarity, with a plain-text fallback.