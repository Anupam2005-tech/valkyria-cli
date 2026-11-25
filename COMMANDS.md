# Valkyrie CLI — Command Reference

Complete reference for all terminal CLI commands (`valkyrie` / `vk`) and in-chat slash commands (`/...`) available in Valkyrie.

> **Short CLI binary:** You can use `vk` anywhere instead of `valkyrie` (e.g. `vk c` for `valkyrie chat`), plus short group aliases: `c` (`chat`), `m` (`model`), `k` (`keys`), `a` (`auth`), `r` (`rag`), `s` (`status`), `ss` (`session`), `in` (`login`), `out` (`logout`). Unambiguous prefixes also work automatically.

---

## 1. General & Onboarding Commands

| Command | Description |
| :--- | :--- |
| `valkyrie` | Shows the Valkyrie banner and auth/setup summary. Launches the first-run setup wizard automatically in an interactive terminal if setup is incomplete. |
| `valkyrie --version` | Prints the installed Valkyrie CLI version. |
| `valkyrie --help` | Lists all top-level CLI commands. |
| `valkyrie status` | Displays config directory, Firebase auth status, configured providers, assigned model roles, first-run status, workspace root, Pinecone RAG index, and latest workspace session. |
| `valkyrie setup` | Runs the interactive onboarding wizard (optional Google sign-in, encrypted vault + API keys, live model discovery, optional profile, and role assignments). |
| `valkyrie login` | Top-level alias for `valkyrie auth login`. |
| `valkyrie logout` | Top-level alias for `valkyrie auth logout`. |

---

## 2. Authentication & Account Lifecycle (`valkyrie auth`)

| Command | Options | Description |
| :--- | :--- | :--- |
| `valkyrie auth login` | — | Opens your browser for Firebase Google sign-in and stores tokens in `~/.valkyrie/auth.json`. |
| `valkyrie auth switch` | — | Opens Google's account chooser (`select_account`) in the browser to switch to another Google account. Preserves your existing session if cancelled, and offers to pull a synced vault if the new account has one. |
| `valkyrie auth delete` | `--yes`, `--purge-local` | Permanently deletes your Firebase Auth user and remote Firestore vault (`users/{uid}/vault/keys`), clears local `auth.json`, and disables cloud sync. Use `--yes` to skip confirmation and `--purge-local` to also delete local `vault.enc`. |
| `valkyrie auth logout` | — | Signs out locally by clearing `~/.valkyrie/auth.json` (does not delete your Firebase account or remote vault). |
| `valkyrie auth status` | — | Shows current sign-in status, email, display name, UID, cloud sync state, and token expiry. |

---

## 3. Encrypted Key Vault (`valkyrie keys`)

Keys are encrypted locally with Argon2id + AES-256-GCM in `~/.valkyrie/vault.enc`. Supported providers: `groq`, `gemini`, `nvidia`.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| `valkyrie keys add [PROVIDER]` | `PROVIDER` (optional) | Prompts for master password and adds/updates an API key (`groq`, `gemini`, or `nvidia`), then offers to sync to Firebase if signed in. |
| `valkyrie keys list` | — | Unlocks the vault and displays masked API keys and timestamps. |
| `valkyrie keys remove PROVIDER` | `PROVIDER` | Prompts for confirmation and master password, removes the provider key from the vault, and offers to sync. |
| `valkyrie keys sync` | — | Pushes your encrypted vault to Firebase Firestore (`users/{uid}/vault/keys`), or pulls it from Firestore if no local vault exists. |

---

## 4. Model Catalog & Role Assignments (`valkyrie model`)

| Command | Options / Arguments | Description |
| :--- | :--- | :--- |
| `valkyrie model` | — | Shows current model assignments for all roles (`chat`, `code`, `planner`, `vision`, `summarization`, `embeddings`) and cached catalog counts. |
| `valkyrie model list` | `-p/--provider`, `-r/--role`, `-c/--capability`, `-s/--search` | Lists cached models grouped by provider, with provider filter pills and capability/context-window/state columns. |
| `valkyrie model refresh` | `-p/--provider` | Unlocks your vault, validates keys, and fetches live model catalogs from configured providers (or a single provider with `-p`). |
| `valkyrie model set ROLE MODEL_ID` | `ROLE`, `MODEL_ID` | Assigns a `<provider>/<model_id>` (or unique bare model ID) to a role, or pass `unassigned` to clear a role. |

---

## 5. Interactive Chat (`valkyrie chat`)

| Command | Options | Description |
| :--- | :--- | :--- |
| `valkyrie chat` | — | Unlocks your vault and resumes the latest session in the current workspace (or creates one if none exists). |
| `valkyrie chat --new` | `--new` | Starts a brand new session instead of resuming the latest one. |
| `valkyrie chat --model <id>` | `--model` | Overrides the active chat model (`<provider>/<model_id>`) for the session. |
| `valkyrie chat --session <id>` | `--session` | Resumes a specific saved session by exact ID or unique prefix. |

---

## 6. Durable Session Management (`valkyrie session`)

Sessions are stored in SQLite at `~/.valkyrie/data/sessions.db`.

| Command | Options / Arguments | Description |
| :--- | :--- | :--- |
| `valkyrie session list` | `--all` | Lists saved sessions for the current workspace (or across all workspaces with `--all`). |
| `valkyrie session new` | `--title`, `--model` | Creates a new persistent session and prints its ID for resuming later. |
| `valkyrie session show SESSION_ID` | `SESSION_ID` | Displays session metadata, token usage, checkpoint ID, and the last 10 messages. |
| `valkyrie session rename SESSION_ID TITLE` | `SESSION_ID`, `TITLE` | Renames a saved session. |
| `valkyrie session fork SESSION_ID` | `--title` | Clones an existing session and its message history into a new branched session. |
| `valkyrie session search QUERY` | `QUERY` | Searches sessions by title or message content. |
| `valkyrie session compact SESSION_ID` | `--keep` (default: `4`) | Summarizes older turns in a session while keeping the system prompt and the most recent `--keep` messages. |
| `valkyrie session delete SESSION_ID` | `--yes` | Deletes a saved session and its messages/checkpoints (`--yes` skips confirmation). |

---

## 7. Pinecone RAG (`valkyrie rag`)

Vector retrieval uses Pinecone DB exclusively (configured via `PINECONE_API_KEY` and `PINECONE_INDEX` in `.env`, with zero local vector storage).

| Command | Options / Arguments | Description |
| :--- | :--- | :--- |
| `valkyrie rag index [TARGET]` | `TARGET` (default: `.`) | Chunks and embeds workspace files and upserts them into the workspace's Pinecone namespace. |
| `valkyrie rag search QUERY` | `--top-k` (default: `5`) | Searches the workspace's Pinecone namespace and prints matching chunks with line citations and similarity scores. |
| `valkyrie rag status` | — | Displays workspace root, embedding mode, Pinecone index/region/namespace, connection status, and vector count. |
| `valkyrie rag clear` | `--yes` | Deletes all indexed vectors in the current workspace's Pinecone namespace (`--yes` skips confirmation). |

---

## 8. In-Chat Slash Commands (`/...`) & `@` Attachments

Inside `valkyrie chat`, type `/` for live command autocomplete or `@` to attach workspace files.

| Command | Short Alias | Description |
| :--- | :--- | :--- |
| `/help` | `/h`, `/?` | Lists all active in-chat slash commands and their usage. |
| `/new [title]` | `/n` | Starts a brand new chat session with a fresh context window and zeroed token counters (preserves previous sessions in SQLite). |
| `/clear` | `/c`, `/cls` | Clears the screen and resets conversation turns while keeping the current session ID. |
| `/compact [keep]` | `/cmp` | Summarizes older turns into a concise summary message, keeping the last `keep` turns (default: `4`). |
| `/model` | `/m` | Shows the active model, context budget, role assignments, and provider filter pills. |
| `/model <provider> [search]` | `/m <provider>` | Filters the model catalog by provider (`groq`, `gemini`, `nvidia`) and optional search text. |
| `/model list [provider] [query]` | `/m ls` | Lists models in the catalog, optionally filtered by provider and search query. |
| `/model pick [provider]` | `/m p` | Opens an interactive numbered model selector with live provider filtering. |
| `/model refresh [provider]` | `/m rf` | Fetches live model catalogs from unlocked providers. |
| `/model [use] <id>` | `/m <id>`, `/m u <id>` | Switches the active session model immediately (accepts `<provider>/<model_id>` or a unique bare model ID). |
| `/budget` | `/b` | Displays current context window usage and total prompt/completion tokens for the session. |
| `/session` | `/ss` | Shows the active session ID, title, message count, checkpoint ID, and model. |
| `/account` | `/acc`, `/auth`, `/acc st` | Shows current signed-in account, UID, token expiry, and cloud sync status. |
| `/account switch` | `/acc sw` | Opens Google's account picker in your browser to switch accounts (offers to pull synced vault if available). |
| `/account delete [--yes] [--purge-local]` | `/acc del` | Permanently deletes your signed-in Firebase account and remote Firestore vault, clears local auth, and optionally removes local `vault.enc`. |
| `/account login` | `/acc in` | Signs in with Google via browser handoff if not already signed in. |
| `/account logout` | `/acc out` | Signs out locally without deleting your cloud account. |
| `/workspace` | `/ws` | Displays the detected workspace root and count of `@`-attachable files. |
| `/read <path> [start] [end]` | `/r` | Reads a workspace file (or line slice) and displays a preview card. |
| `/index [path]` | `/i` | Indexes workspace files into Pinecone DB. |
| `/search <query>` | `/s` | Searches Pinecone DB for matching workspace chunks with citations. |
| `/rag [on\|off\|status]` | — | Toggles automatic Pinecone RAG context injection per turn or displays Pinecone status. |
| `/web <query>` | `/w` | Runs a live DuckDuckGo web search via LangChain and displays top results. |
| `/auto [on\|off]` | `/a` | Toggles automatic approval for local file write/edit/delete tool calls (or flips state when called with no argument). |
| `/exit` | `/q`, `/quit` | Exits the interactive chat REPL. |
| `@<path>` | — | Inline token in any prompt (with autocomplete) that attaches a workspace file's contents to that turn. |

---

## 9. Autonomous Agent Tools (During Chat)

When chatting in `valkyrie chat`, the model can invoke these LangChain-backed tools automatically (prompting `[Y/n/a]` for mutating file operations unless `/auto on` is active):

| Tool | Purpose |
| :--- | :--- |
| `read_file` | Reads files (with optional line ranges) from the workspace or local user directories (e.g. `~/Downloads`). |
| `write_file` | Creates or overwrites files on your local machine (blocked on protected paths like `/etc`, `.git`, `.env`, `vault.enc`, `auth.json`). |
| `edit_file` | Performs targeted text replacements inside existing local files. |
| `delete_file` | Deletes a local file after confirmation. |
| `list_directory` | Lists files and subdirectories at a given path. |
| `search_files` | Searches for files by glob pattern or text content across a directory. |
| `web_search` | Performs live DuckDuckGo web searches via LangChain. |

