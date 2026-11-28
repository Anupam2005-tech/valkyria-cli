export const PROVIDER_STRIP = [
  "Groq",
  "Gemini",
  "NVIDIA",
  "Pinecone",
  "Firebase",
  "FastAPI",
];

export const HOW_IT_WORKS_STEPS = [
  {
    num: "01",
    title: "Connect",
    copy: "Log in from your browser, paste your Groq, Gemini and NVIDIA keys, tell Valkyria your name and what you do. It remembers.",
    command: "valkyria login",
    snippet: [
      "$ valkyria login",
      "Opened browser sign-in via Firebase...",
      "Signed in as sam@studio.dev",
      "Vault unlocked (AES-256-GCM)",
      "Providers ready: Groq · Gemini · NVIDIA",
    ],
  },
  {
    num: "02",
    title: "Plan",
    copy: "Type /plan. Your task becomes steps you can read, edit and approve.",
    command: "/plan migrate auth to JWT",
    snippet: [
      "> /plan migrate auth to JWT",
      "Plan · 4 steps",
      "  1  read app/auth/session.py, app/deps.py",
      "  2  add RS256 token signer and verify middleware",
      "  3  update tests/test_auth.py",
      "  4  run pytest -q",
    ],
  },
  {
    num: "03",
    title: "Approve",
    copy: "Every write, command or install waits for your yes. Diffs shown, undo ready.",
    command: "[a]pprove  [e]dit  [d]eny",
    snippet: [
      "~ edit app/deps.py (+18 / -4)",
      "  + def verify_bearer_jwt(token: str) -> Claims:",
      "  +     return jwt.decode(token, PUBLIC_KEY, algorithms=[\"RS256\"])",
      "  - def verify_cookie(session_id: str) -> User:",
      "Approve?  [a]pprove  [e]dit  [d]eny",
    ],
  },
  {
    num: "04",
    title: "Build",
    copy: "Valkyria executes, checks its own work and saves the session. Use /new for a clean slate or /session to pick up later.",
    command: "/new · /session",
    snippet: [
      "Running pytest -q...",
      "14 passed in 0.84s",
      "Session saved · ctx 18% · #auth-jwt",
      "> /new",
      "Fresh context window ready.",
    ],
  },
];

export const COMPARISON_ROWS = [
  {
    feature: "Models",
    typical: "One provider, one lock-in",
    valkyria: "Groq, Gemini and NVIDIA, routed per task with automatic fallback",
  },
  {
    feature: "Your keys",
    typical: "Held on someone else's server",
    valkyria: "Yours, encrypted on your machine before they ever sync",
  },
  {
    feature: "Your files",
    typical: "Pasted in or uploaded wholesale",
    valkyria: "Indexed and stored in your Pinecone cloud index; only relevant chunks go out",
  },
  {
    feature: "System access",
    typical: "All or nothing",
    valkyria: "Tiered permissions, approval prompts, undo",
  },
  {
    feature: "Memory",
    typical: "One endless scroll",
    valkyria: "Real sessions plus context budgeting: /new, /session",
  },
  {
    feature: "Workflow",
    typical: "Straight to code",
    valkyria: "Plan, approve, then build",
  },
];

export const DIFFERENT_STATS = [
  { value: "3", label: "Providers at launch" },
  { value: "5+", label: "Model roles" },
  { value: "1", label: "Approval gate for every risky action" },
];

export const UNDER_THE_HOOD_PLATES = [
  {
    id: "01",
    label: "Plate 01 · Terminal UI",
    headline: "Fast hands",
    bullets: [
      "Slash commands for every task",
      "Suggestions pop up as you type",
      "@ autocompletes file paths",
    ],
  },
  {
    id: "02",
    label: "Plate 02 · Agent loop",
    headline: "The flight plan",
    bullets: [
      "Planner, Safety gate, Executor, Evaluator in one loop",
      "Pause, inspect and steer every step",
      "Tool calls stay visible with live status cards",
    ],
  },
  {
    id: "03",
    label: "Plate 03 · Safety gate",
    headline: "The shield",
    bullets: [
      "Permission tiers: read, write, exec, network, system",
      "Workspace jail and protected-path denylist",
      "Diff before write with undo snapshots and audit log",
    ],
  },
  {
    id: "04",
    label: "Plate 04 · Model router",
    headline: "Right model, every time",
    bullets: [
      "Picks Groq, Gemini or NVIDIA per task",
      "Falls back cleanly on rate limits or retired models",
      "Context window respected per model",
    ],
  },
  {
    id: "05",
    label: "Plate 05 · Cloud memory",
    headline: "Knows your code",
    bullets: [
      "Pinecone vector store scoped to your workspace",
      "Chunking by file type; re-indexes only changed files",
      "Sessions with rolling summaries and compaction near 75% context",
    ],
    showBudget: true,
  },
  {
    id: "06",
    label: "Plate 06 · Vault and sync",
    headline: "Your keys, your lock",
    bullets: [
      "Keys encrypted client-side with your master password (AES-256-GCM)",
      "Argon2id key derivation",
      "Only ciphertext syncs through Firebase",
    ],
  },
];

export const CONTEXT_BUDGET_SEGMENTS = [
  { label: "system", pct: 12, color: "#4A4E55" },
  { label: "memory", pct: 10, color: "#6F747A" },
  { label: "summary", pct: 14, color: "#A3A7AB" },
  { label: "recent", pct: 28, color: "#F2F4F1" },
  { label: "retrieved", pct: 18, color: "#FFC929" },
  { label: "reserved", pct: 18, color: "#26282C" },
];

export const FAQ_ITEMS = [
  {
    q: "Does Valkyria run offline?",
    a: "Models are hosted by your providers and RAG vectors live in your Pinecone cloud index, so chatting and RAG search need internet. Your local files and JSON sessions stay on your machine.",
  },
  {
    q: "Where do my API keys live?",
    a: "Encrypted on your machine with your master password before anything syncs. Firebase only ever stores ciphertext, so we cannot read your keys.",
  },
  {
    q: "Which models can I use?",
    a: "Groq, Gemini and NVIDIA at launch, with more providers planned. Valkyria routes per task and falls back automatically.",
  },
  {
    q: "Can it change files or run commands on my laptop?",
    a: "Only with your approval. Every write, command, package install or system inspection is tiered, shown to you first, and undoable.",
  },
  {
    q: "Is my code uploaded anywhere?",
    a: "Valkyria chunks your workspace into your own Pinecone index and retrieves only relevant context for the model provider you chose, per request.",
  },
  {
    q: "How much does it cost?",
    a: "Valkyria is free and open-source. You bring your own API keys and pay providers directly.",
  },
  {
    q: "What systems does it run on?",
    a: "Linux, macOS and Windows. Valkyria is a Python 3.11+ CLI installed with pipx or uv.",
  },
  {
    q: "How do sessions work?",
    a: "/new opens a fresh context window. /session lists previous sessions so you can resume, rename or delete them.",
  },
];

export const COMMANDS_REFERENCE = [
  { cmd: "/new", action: "Start a fresh context window; the old session is saved" },
  { cmd: "/session", action: "List previous sessions; resume, search, rename or delete" },
  { cmd: "/fork", action: "Branch the current session" },
  { cmd: "/compact", action: "Summarize older turns now" },
  { cmd: "/context", action: "Show token usage" },
  { cmd: "/clear", action: "Wipe the current session" },
  { cmd: "/ask", action: "Read-only question mode" },
  { cmd: "/plan", action: "Create a step-by-step plan" },
  { cmd: "/build", action: "Execute the plan with approvals" },
  { cmd: "/index", action: "Add files or folders to the RAG index" },
  { cmd: "/search", action: "Web search" },
  { cmd: "/img", action: "Analyze an image" },
  { cmd: "/fs", action: "File operations" },
  { cmd: "/run", action: "Run a command" },
  { cmd: "/pkg", action: "Install or manage packages" },
  { cmd: "/sys", action: "Inspect the machine" },
  { cmd: "/model", action: "Switch model or provider" },
  { cmd: "/mode", action: "Switch ask, plan, build or auto" },
  { cmd: "/profile, /keys", action: "Edit profile and API keys" },
  { cmd: "/undo", action: "Revert the last change" },
  { cmd: "/login, /logout", action: "Authentication" },
];

export const FOOTER_COLUMNS = [
  {
    heading: "Product",
    links: [
      { label: "How it works", href: "/#how-it-works" },
      { label: "Why Valkyria", href: "/#different" },
      { label: "Setup", href: "/#setup" },
      { label: "FAQ", href: "/#faq" },
    ],
  },
  {
    heading: "Resources",
    links: [
      { label: "Docs", href: "/docs" },
      { label: "Command reference", href: "/docs#commands-reference" },
      { label: "Changelog", href: "/docs#getting-started" },
    ],
  },
  {
    heading: "Legal",
    links: [
      { label: "Terms & Conditions", href: "/terms" },
      { label: "Privacy Policy", href: "/privacy" },
    ],
  },
  {
    heading: "Community",
    links: [
      { label: "GitHub", href: "https://github.com/Anupam2005-tech/valkyria-cli", external: true },
      { label: "X", href: "https://x.com", external: true },
      { label: "Discord", href: "https://discord.com", external: true },
    ],
  },
];
