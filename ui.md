# Valkyria Launch Website: Master Build Prompt

> Paste everything below the line into your AI builder (Claude Code, Cursor, v0, etc.).
> Everything in `[brackets]` is a placeholder to confirm before launch.

---

## 0. Brief

Build a **dark-theme, 3D, scroll-driven, immersive marketing website** that launches **Valkyria**, a terminal-first AI agent that plans and builds with Groq, Gemini and NVIDIA models, on the user's own API keys, with cloud RAG (Pinecone), approval-gated system access and real session management.

The site must feel **premium, sassy and flagship-level (award-site quality)**. It has its **own identity**. Take inspiration for *motion quality, terminal-native confidence and playfulness* from motion.dev, opencode.ai and openclaw.ai, but **do not copy any layout, copy, mascot or asset** from them.

**Pages**

| Route | Purpose |
|---|---|
| `/` | The 3D scroll landing experience (sections below) |
| `/docs` | User manual / documentation |
| `/terms` | Terms & Conditions |
| `/privacy` | Privacy Policy |
| `/404` | Branded not-found page |

**Sections on `/` (in this order)**

1. Navbar + Landing (hero)
2. How it works
3. How is it different
4. How it works, part 2 (under the hood)
5. Q&A
6. Setup steps
7. Footer

(That is 6 content sections plus the footer. Build them exactly in this order.)

---

## 1. Brand identity

**Concept:** the Valkyria, the one who *chooses*. Valkyria chooses the right model for each task, shields you from risky actions and carries your work to the finish.

**Visual motifs (use consistently, every section must show at least one)**

| Motif | Meaning | Where it appears |
|---|---|---|
| Hexagon shield | Safety gate, approval | Logo, 3D hero object, bullets, section markers |
| Feather blades / wings | Multi-model reach, speed | Hero 3D wings, section dividers, cursor trail |
| Rings / torus | The agent loop, orbit of providers | Pipeline in "How it works", orbiting provider nodes |
| Shards (tetrahedra) | Chunks of knowledge (RAG) | Particle field, footer convergence |
| Pill | Interface and commands | Buttons, nav, command chips |
| Arrow / spear | Precision, "build" | Setup path, CTA accents |

**Tone of voice:** confident, short, a little cheeky. Never corporate. No emojis in UI. No exclamation-mark spam.

**Logo:** a hexagon outline with two blade-wings extending left and right and a small yellow center notch. Build it as an inline SVG (`<Logo />`) usable at 24px to 240px. Wordmark "Valkyria" in the display font, set beside it.

---

## 2. Design tokens (exact)

### Color

```css
:root {
  /* Brand */
  --graphite:        #1C1D20;  /* Deep Graphite, base background */
  --cloud:           #F2F4F1;  /* Soft Cloud, primary text, light surfaces */
  --sun:             #FFC929;  /* Sunshine Yellow, the single accent */

  /* Derived graphite scale */
  --graphite-950:    #101113;
  --graphite-900:    #151619;
  --graphite-800:    #1C1D20;
  --graphite-700:    #26282C;
  --graphite-600:    #34373C;
  --graphite-500:    #4A4E55;

  /* Text */
  --text:            #F2F4F1;
  --text-muted:      #A3A7AB;   /* meets AA on --graphite */
  --text-dim:        #6F747A;

  /* Lines and glass */
  --line:            rgba(242, 244, 241, 0.10);
  --line-strong:     rgba(242, 244, 241, 0.18);
  --glass:           rgba(28, 29, 32, 0.62);

  /* Accent states */
  --sun-glow:        rgba(255, 201, 41, 0.35);
  --sun-soft:        rgba(255, 201, 41, 0.12);
  --on-sun:          #1C1D20;   /* text on yellow */
}
```

**Color rules**
- Page background: layered radial gradients from `--graphite-950` to `--graphite-800`, with a 3-4% opacity SVG grain overlay, fixed.
- **Yellow is rare:** under about 10% of visible pixels. Use it only for primary CTAs, the active state, one highlighted word per headline, the scroll progress rail, 3D energy lines and focus rings.
- Text on yellow is always graphite.
- No purple, no blue-purple gradients, no rainbow. No gradient text. Headlines are solid cloud with one yellow serif-italic accent word.
- **One inverted section:** "How is it different" is a **Soft Cloud (`#F2F4F1`) panel with graphite text** that wipes in through a clip-path as you scroll, for rhythm. Everything else is dark.

### Typography (Google Fonts via `next/font`)

| Role | Font | Weights | Use |
|---|---|---|---|
| Display | **Bricolage Grotesque** | 600, 700, 800 | Headlines, section titles |
| Accent | **Instrument Serif** (italic) | 400 | One emphasized word per headline |
| UI / body | **Geist** | 400, 500, 600 | Body, nav, buttons |
| Mono | **Geist Mono** | 400, 500 | Terminal, commands, numerals, labels |

```css
--font-display: "Bricolage Grotesque", "Geist", system-ui, sans-serif;
--font-accent:  "Instrument Serif", Georgia, serif;
--font-sans:    "Geist", "Inter", system-ui, sans-serif;
--font-mono:    "Geist Mono", ui-monospace, "SF Mono", monospace;
```

Type scale (fluid):
- `display-xl`: `clamp(44px, 8vw, 120px)`, line-height 0.95, letter-spacing `-0.04em`
- `display-lg`: `clamp(36px, 5.5vw, 76px)`, line-height 1.0, letter-spacing `-0.035em`
- `h3`: `clamp(22px, 2.4vw, 32px)`, letter-spacing `-0.02em`
- `body-lg`: `clamp(16px, 1.3vw, 19px)`, line-height 1.6
- `label` (mono, uppercase): 12px, letter-spacing `0.12em`

### Shape, depth and motion

- Radii: `12px` (inputs), `20px` (cards), `28px` (large panels), `999px` (pills).
- Borders: `1px solid var(--line)`. Hover: `var(--line-strong)` plus a faint yellow inner glow.
- Shadows: soft only, `0 24px 60px rgba(0,0,0,0.45)`. Yellow glow only on primary CTAs: `0 0 0 1px rgba(255,201,41,.35), 0 0 28px var(--sun-glow)`.
- Easing: `cubic-bezier(0.22, 1, 0.36, 1)` for everything. Durations: micro 0.25s, standard 0.6s, hero 0.9-1.2s.
- Springs (Motion): `{ stiffness: 140, damping: 22, mass: 0.9 }`.
- Section boundaries use **angled feather cuts**: `clip-path: polygon(0 0, 100% 0, 100% 92%, 0 100%)` or the mirrored version, never flat horizontal lines.
- Spacing: 8px base. Section padding `clamp(96px, 14vh, 200px)` vertical. Content max-width `1280px`, text blocks `720px`.

---

## 3. Tech stack

- **Next.js (App Router) + TypeScript + Tailwind CSS** (tokens above wired into `tailwind.config`).
- **Motion** (`motion/react`, formerly Framer Motion) for component animation, springs, layout and gestures.
- **GSAP + ScrollTrigger** for pinned and scrubbed scroll sequences.
- **Lenis** for smooth scroll, synced to ScrollTrigger (`lenis.on('scroll', ScrollTrigger.update)`; drive GSAP's ticker from Lenis `raf`).
- **three + @react-three/fiber + @react-three/drei + @react-three/postprocessing** for the 3D scene (bloom only, subtle).
- **zustand** for a global scroll store (`progress`, `section`, `velocity`).
- **lucide-react** for icons (stroke 1.5).
- **MDX** (`@next/mdx` or `next-mdx-remote`) for `/docs` content.
- Use **latest stable** versions of everything.

**Allowed component sources.** You may start from React Bits, Aceternity UI and 21st.dev components, then **fully restyle to the tokens above** so nothing looks stock. If a named component is unavailable or its API differs, rebuild it.

| Need | Suggested base (restyle it) |
|---|---|
| Text reveals | React Bits: Split Text, Blur Text, Shiny Text, Scroll Reveal |
| Magnetic buttons | React Bits: Magnet |
| Spotlight / tilt cards | React Bits: Spotlight Card, Tilt; Aceternity: Wobble Card, 3D Card |
| Dot-grid background reacting to cursor | React Bits: Dot Grid |
| Velocity marquee | React Bits: Scroll Velocity |
| Sticky stacked step reveal | Aceternity: Sticky Scroll Reveal |
| Progress line along content | Aceternity: Tracing Beam |
| Animated number counters | React Bits: Count Up |
| Navbar, accordion, footer patterns | Search the 21st.dev registry, then restyle |

---

## 4. Global experience layer

### 4.1 Persistent 3D canvas
- One **fixed full-viewport `<Canvas>`** at `z-index: 0` behind all content, `pointer-events: none`.
- `dpr={[1, 1.75]}`, `antialias`, alpha background (so the CSS gradient shows through), `powerPreference: "high-performance"`.
- The scene is driven by **scroll progress** (from Lenis into the zustand store). Each section has a "3D beat" (table in section 5). Transitions between beats are **interpolated**, never cut.
- Camera moves along a `CatmullRomCurve3` through section waypoints, eased with damping (`THREE.MathUtils.damp`), so motion feels weighted, not 1:1 jerky.
- Lighting: soft cloud-white key light, yellow rim light from behind, very low ambient. Subtle bloom on yellow emissive edges only. No default HDR environment colors that break the palette.
- Pause rendering when the tab is hidden.

### 4.2 Smooth scroll and real-time scroll effects
- Lenis smooth scrolling site-wide (disabled for reduced motion).
- **Scroll progress rail:** thin vertical line on the right edge, yellow fill grows with scroll, with a mono counter `01 / 06` that updates per section.
- **Scrubbed text:** manifesto lines fill word by word from 25% to 100% cloud opacity as they cross the viewport.
- **Parallax layers:** at least three depth layers per section (background grid, mid shapes, foreground content) moving at different rates.
- **Velocity effects:** marquees speed up and skew slightly with scroll velocity; the 3D shield micro-rotates on velocity spikes.
- **3D card tilt:** cards use `perspective(1000px)` and follow the cursor (max 8 degrees), with a moving spotlight highlight.
- **Magnetic buttons** on primary CTAs (pull radius about 80px).
- **Custom cursor (desktop only):** small yellow dot with a trailing ring; label states "View", "Drag", "Copy"; `mix-blend-mode: difference` on cloud areas. Falls back to the native cursor on touch.
- **Section transitions:** feather-cut clip-path wipes plus the 3D camera flight; content fades and rises (`translateY(24px)`, blur 6px to 0).

### 4.3 Intro loader (first visit only, 1.6s max)
Hexagon outline draws itself (stroke-dashoffset), wings extend, "Valkyria" letters stagger in, then the loader splits open and reveals the hero. Skippable and shown once per session.

### 4.4 Background
- Fixed **dot grid** (React Bits Dot Grid style, restyled: dots `rgba(242,244,241,0.14)`, active dots near cursor turn yellow).
- Fixed grain overlay at 3-4%.
- Large, soft yellow radial glow (opacity 0.06-0.10) that drifts slowly behind the hero.

---

## 5. Section specs

### 5.0 3D beats at a glance

| Section | 3D beat | Camera | Accent behavior |
|---|---|---|---|
| 1 Hero | Hexagon shield assembles from 6 plates; feather-blade wings fan open as you scroll; 3 provider orbs orbit on tilted rings; dust particles drift | Slow push-in, slight parallax to the mouse | Shield edges glow yellow |
| 2 How it works | Four torus rings aligned along Z form a flight tunnel | Camera flies through the rings, one per step | Active ring turns yellow, others graphite |
| 3 How is it different | Scene dims and recedes; a few gray cubes (generic tools) drift away while a single shield stays | Pull-back, then settle | Cloud panel wipes in over the scene |
| 4 Under the hood | Shield "explodes" into six stacked plates on the Y axis, each labeled | Orbit around the stack as steps advance | Highlighted plate glows yellow |
| 5 Q&A | Calm: slow-drifting small hexes and shards, low intensity | Gentle float | Minimal |
| 6 Setup steps | Five ascending hex platforms like stairs; a small yellow spear/arrow climbs them | Camera tracks the arrow upward | Completed steps turn yellow |
| 7 Footer | Shards converge into the shield, which flattens into an outlined wordmark | Pull-back to a flat frontal view | Final yellow pulse on the CTA |

### 5.1 Navbar + Landing

**Navbar**
- Floating glass pill, centered, `top: 16px`, `max-width: 860px`, height 56px, background `var(--glass)`, `backdrop-filter: blur(16px)`, 1px `--line` border.
- Left: `<Logo />` + "Valkyria". Center links: **How it works**, **Why Valkyria**, **FAQ**, **Setup**, **Docs** (route `/docs`). Right: primary pill **Get Valkyria** (yellow, graphite text, magnetic).
- The active link follows the current section (scroll-spy) with a sliding yellow underline pill.
- **Hides on scroll down, reappears on scroll up.** Shrinks to 48px after 80px of scroll.
- Mobile (at or below 820px): logo + circular burger. Opens a full-screen sheet in graphite with large display-font links, staggered entrance, close on link click, Escape and overlay click.
- Sub-pages (`/docs`, `/terms`, `/privacy`) use the same navbar with solid background and links pointing back to `/#section`.

**Hero**
- Layout: 12-column grid. Text block on the left (max 720px), 3D scene fills the back and right, terminal mockup floats lower-right.
- Eyebrow chip (mono, uppercase): `TERMINAL-NATIVE AI AGENT · BRING YOUR OWN KEYS`.
- **H1** (`display-xl`, two lines, solid cloud):
  ```
  Your terminal
  grew *wings.*
  ```
  "wings" in Instrument Serif italic, `--sun`. Lines reveal with mask-up animation, delays 0.15s and 0.35s.
- **Subhead** (`body-lg`, muted): "Valkyria plans, builds and ships using Groq, Gemini and NVIDIA, on your keys, under your approval. Local memory. Real sessions. Zero hand-waving."
- **CTAs:** primary **Get Valkyria** (yellow pill, glow, magnetic) and ghost **Read the manual** (`/docs`).
- **Install chip** under the CTAs: mono, `$ pipx install valkyria` `[confirm package name]`, click to copy, "Copied" feedback.
- **Terminal mockup** (the hero's signature element): glass card with a window header (three hex dots instead of macOS circles), tilted `rotateY(-12deg) rotateX(6deg)`, easing flat toward the cursor. Looping typed script:
  ```
  $ valkyria
  Hey Sam. Ready. model: auto · ctx 4%
  > /plan add rate limiting to the FastAPI service
    Plan · 4 steps
    1  read app/main.py, app/deps.py
    2  add rate-limit middleware
    3  write tests/test_rate_limit.py
    4  run pytest
  Approve?  [a]pprove  [e]dit  [d]eny
  ```
  The command autocomplete popup appears while typing `/pl` (shows `/plan`, `/pkg`) to demo the suggestion feature. Cursor block blinks yellow.
- **Provider strip** at the bottom of the viewport: a slow velocity marquee with hex bullet separators: `Groq · Gemini · NVIDIA · Pinecone · Firebase · FastAPI`. Text-only logos in muted color. **No customer logos, no fake "trusted by" claims.**
- **Scroll cue:** small mono label "SCROLL" with an animated line.

### 5.2 How it works (part 1: the loop)

Pinned section, about 300vh of scroll, the camera flies through the four rings.

- **Title:** "Four moves. One flight path."
- **Manifesto line** (scrubbed word-fill): "No prompt gymnastics. You say what you want, Valkyria shows its plan, you approve, it builds."
- Left: sticky step list (Aceternity Sticky Scroll Reveal style, restyled). Right: a glass panel showing a **mini terminal snippet per step**, crossfading as steps change. The matching 3D ring lights up.

| # | Step | Copy | Terminal snippet |
|---|---|---|---|
| 01 | **Connect** | "Log in from your browser, paste your Groq, Gemini and NVIDIA keys, tell Valkyria your name and what you do. It remembers." | `valkyria login` then onboarding prompts |
| 02 | **Plan** | "Type /plan. Your task becomes steps you can read, edit and approve." | `/plan migrate auth to JWT` with the plan list |
| 03 | **Approve** | "Every write, command or install waits for your yes. Diffs shown. Undo ready." | A diff view with `[a]pprove [d]eny` |
| 04 | **Build** | "Valkyria executes, checks its own work and saves the session. `/new` for a clean slate, `/session` to pick up later." | Test run passing, session saved line |

- Each step number is mono, huge, outlined in cloud, filling yellow when active.

### 5.3 How is it different (cloud-light inverted section)

Clip-path wipe reveals a **Soft Cloud** panel (`#F2F4F1`, graphite text). The 3D scene dims behind it.

- **Title:** "Not another chat box in a terminal costume." (accent word: *costume*, serif italic, graphite with a yellow underline swash.)
- **Comparison table** (rows reveal one by one on scroll, with a 3D tilt hover). Two columns: **Typical AI CLI** (muted graphite 55%) and **Valkyria** (full graphite, yellow check hex).

| | Typical AI CLI | Valkyria |
|---|---|---|
| **Models** | One provider, one lock-in | Groq, Gemini and NVIDIA, routed per task with automatic fallback |
| **Your keys** | Held on someone else's server | Yours, encrypted on your machine before they ever sync |
| **Your files** | Pasted in or uploaded wholesale | Indexed and stored in your Pinecone cloud index, only relevant chunks go out |
| **System access** | All or nothing | Tiered permissions, approval prompts, undo |
| **Memory** | One endless scroll | Real sessions plus context budgeting: `/new`, `/session` |
| **Workflow** | Straight to code | Plan, approve, then build |

- Under the table, three **stat-style cards** (no invented numbers; use capability counts only): "**3** providers at launch", "**5+** model roles", "**1** approval gate for every risky action" `[adjust to final product]`.
- No competitor names anywhere.

### 5.4 How it works, part 2 (under the hood)

Pinned section, about 250vh. The 3D shield **explodes into six stacked plates**. Scrolling advances through them, the camera orbits, and a side panel explains the active plate.

- **Title:** "Anatomy of a flight."
- Six plates, each with a mono label, one-line headline and 2-3 short bullets:

| Plate | Headline | Bullets |
|---|---|---|
| 1 Terminal UI | Fast hands | Slash commands for every task; suggestions pop up as you type; `@` autocompletes file paths |
| 2 Agent graph | The flight plan | Planner, Safety gate, Executor, Evaluator in a LangGraph loop; pause, resume and replay any task |
| 3 Safety gate | The shield | Permission tiers: read / write / exec / network / system; workspace jail; command denylist; diff before write; undo snapshots; full audit log |
| 4 Model router | Right model, every time | Picks Groq, Gemini or NVIDIA per task; falls back on rate limits; context window respected per model |
| 5 Cloud memory | Knows your code | Pinecone vector store; chunking by file type; re-indexes only changed files; sessions with rolling summaries and compaction near 75% context |
| 6 Vault and sync | Your keys, your lock | Keys encrypted client-side with your master password (AES-256-GCM); only ciphertext syncs through Firebase |

- Include a small animated **context budget bar** on plate 5 (segments: system, memory, summary, recent, retrieved, reserved) that fills as you scroll.

### 5.5 Q&A

Calm section (3D beat is minimal). Two columns on desktop: left sticky title "Questions, answered.", right accordion.

- Accordion: keyboard-accessible (`button` + `aria-expanded`, `aria-controls`), animated height, yellow hex marker rotating on open, only one open at a time, first open by default.
- Entries (copy is final unless marked):

1. **Does Valkyria run offline?** "Models are hosted by your providers and RAG vectors live in your Pinecone cloud index, so chatting and RAG search need internet. Your local files and JSON sessions stay on your machine."
2. **Where do my API keys live?** "Encrypted on your machine with your master password before anything syncs. Firebase only ever stores ciphertext, so we can't read your keys."
3. **Which models can I use?** "Groq, Gemini and NVIDIA at launch, with more providers planned. Valkyria routes per task and falls back automatically."
4. **Can it change files or run commands on my laptop?** "Only with your approval. Every write, command, package install or system inspection is tiered, shown to you first, and undoable."
5. **Is my code uploaded anywhere?** "Valkyria retrieves relevant chunks locally and sends only that context to the model provider you chose, per request."
6. **How much does it cost?** "`[Decide pricing.]` You bring your own keys and pay providers directly."
7. **What systems does it run on?** "`[Confirm: Windows, macOS, Linux.]` Valkyria is a Python CLI installed with pipx or uv."
8. **How do sessions work?** "`/new` opens a fresh context window. `/session` lists previous sessions so you can resume, rename or delete them."

### 5.6 Setup steps

Five **ascending hex platforms** in 3D; the yellow arrow climbs as you scroll. On the DOM side, a vertical stepper with a **tracing beam** line that fills yellow.

| # | Step | Command | Note |
|---|---|---|---|
| 1 | **Install** | `pipx install valkyria` `[confirm]` | "Python 3.11+ required `[confirm]`" |
| 2 | **Log in** | `valkyria login` | "Opens your browser. Finish there and you're back in the terminal." |
| 3 | **Onboard** | *(interactive)* | "Add your provider keys, set what Valkyria calls you, tell it your craft." |
| 4 | **Index your project** | `/index .` | "Chunks your files into local memory." |
| 5 | **Plan and build** | `/plan <your task>` then `/build` | "Approve each step. Ship." |

- Each command sits in a **copy chip** (mono, pill, click to copy, cursor label "Copy", toast "Copied").
- Below the stepper: a **CTA band** (rounded 28px, graphite-700, yellow glow edge): "Ready for takeoff?" with the install chip and the primary **Get Valkyria** button.

### 5.7 Footer

- 3D shards converge into the shield, which flattens into the wordmark.
- A **giant outlined "VALKYRIA" wordmark** across the full width (cloud stroke 1px, no fill). On hover, each letter fills yellow progressively (stagger).
- Four link columns:
  - **Product:** How it works, Why Valkyria, Setup, FAQ
  - **Resources:** Docs, Command reference, Changelog `[link]`
  - **Legal:** Terms & Conditions (`/terms`), Privacy Policy (`/privacy`)
  - **Community:** GitHub `[link]`, X `[link]`, Discord `[link]`
- Bottom bar: "© 2026 Valkyria. Built solo, flown everywhere." + "Back to top" magnetic pill.

---

## 6. Sub-pages

All sub-pages share the navbar and footer, use **no heavy 3D** (a static, dimmed dot-grid and grain only), and keep strong readability: body 17px, line-height 1.7, max line width 72ch.

### 6.1 `/docs` (User manual)

Three-column layout: **left sidebar** (sections, collapsible, active item with a yellow marker), **center content** (MDX), **right "On this page"** (scroll-spy anchors). Features:
- **Command palette** (`Ctrl/Cmd + K`) with fuzzy search across headings.
- Code blocks with a language label, copy button and mono syntax theme matching the palette.
- Callouts: Note (cloud), Tip (yellow), Warning (a muted red-orange used only here).
- Prev / Next page links; "Edit this page" `[link]`.

**Sections to author (draft real content for each)**
1. Getting started (what Valkyria is, quick start)
2. Installation
3. Login and onboarding (keys, name, profession, defaults)
4. Commands reference (table below)
5. Sessions and context (`/new`, `/session`, `/fork`, `/compact`, `/context`)
6. RAG and indexing (supported file types, chunking, re-indexing)
7. Plan and build
8. Safety and permissions (tiers, approvals, undo, audit log)
9. Providers and models (Groq, Gemini, NVIDIA, routing, fallback)
10. Vault and key sync
11. Troubleshooting
12. FAQ

**Commands reference table (include verbatim)**

| Command | Action |
|---|---|
| `/new` | Start a fresh context window; the old session is saved |
| `/session` | List previous sessions; resume, search, rename or delete |
| `/fork` | Branch the current session |
| `/compact` | Summarize older turns now |
| `/context` | Show token usage |
| `/clear` | Wipe the current session |
| `/ask` | Read-only question mode |
| `/plan` | Create a step-by-step plan |
| `/build` | Execute the plan with approvals |
| `/index` | Add files or folders to the RAG index |
| `/search` | Web search |
| `/img` | Analyze an image |
| `/fs` | File operations |
| `/run` | Run a command |
| `/pkg` | Install or manage packages |
| `/sys` | Inspect the machine |
| `/model` | Switch model or provider |
| `/mode` | Switch ask, plan, build or auto |
| `/profile`, `/keys` | Edit profile and API keys |
| `/undo` | Revert the last change |
| `/login`, `/logout` | Authentication |

### 6.2 `/terms` and `/privacy`

Two-column layout: sticky table of contents left, content right, "Last updated" date at the top. Write complete **draft** documents with `[placeholders]` and a visible note: "Draft. Have a qualified lawyer review before launch."

**Terms & Conditions: include**
1. Acceptance of terms
2. The service (CLI tool, accounts, hosted sync)
3. Eligibility and accounts
4. Bring-your-own-keys: user is responsible for provider keys, costs and compliance with each provider's terms
5. Acceptable use
6. User content and ownership
7. Agent actions: user approval, user responsibility for approved changes, backups and undo limits
8. Third-party services (Groq, Google, NVIDIA, Firebase)
9. Disclaimers and limitation of liability
10. Termination
11. Changes to terms
12. Governing law `[jurisdiction]` and contact `[email]`

**Privacy Policy: include**
1. What we collect: account identifiers, profile (name, profession), session metadata, encrypted key vault ciphertext, basic diagnostics `[confirm]`
2. What stays local: files, session content cache, decrypted keys (RAG vectors live in your Pinecone cloud index)
3. What is sent to model providers: only the context for the request, under the user's own keys
4. How keys are protected: client-side encryption, we cannot read them, loss of master password means no recovery
5. Firebase and other processors
6. Retention and deletion (how to delete account and synced data)
7. Cookies and analytics `[decide]`
8. Children, security, international transfers
9. User rights and contact `[email]`

### 6.3 `/404`
Shield with a cracked wing, headline "Even Valkyrias get lost." and a **Back to base** button.

---

## 7. Content rules

- Use the **real copy above**. No lorem ipsum.
- **No fabricated stats, testimonials, customer logos, awards or "trusted by" claims.**
- Keep claims aligned with the product: hosted models (Groq, Gemini, NVIDIA), Pinecone cloud vector store, Firebase for auth and encrypted sync, approval-gated system access.
- Placeholders in `[brackets]` must stay visible in code comments so they are easy to find.

---

## 8. Responsive behavior

| Breakpoint | Behavior |
|---|---|
| Desktop (above 1024px) | Full pinned sections, custom cursor, full 3D |
| Tablet (721-1024px) | Pinning kept, simpler 3D, tilt disabled |
| Mobile (720px and below) | No pinning (stacked sections with scroll-triggered reveals), a lighter 3D scene (fewer particles, `dpr` 1), no custom cursor, burger menu, terminal mockup sits below the CTA, tables become stacked cards |

- No horizontal scroll at any width. Tap targets at least 44px.
- Test at 360, 390, 768, 1024, 1440 and 1920 widths.

---

## 9. Performance, accessibility and SEO

**Performance**
- 3D canvas lazy-loaded after the hero text paints. Show a static poster (CSS gradient plus shield SVG) until WebGL is ready.
- Targets: LCP under 2.5s, CLS under 0.1, 60fps on a mid-range laptop. Mobile particles: 300 max (desktop 800).
- Dispose geometries and materials on unmount. Use instancing for particles and shards.
- Use `next/font`, `next/image`, route-level code splitting, and no unused libraries.

**Accessibility**
- `prefers-reduced-motion: reduce`: disable Lenis, pinning, parallax, tilt, marquee motion and the intro loader; render the final static state with a still 3D frame or poster.
- WebGL-unavailable fallback: static poster plus full content, nothing lost.
- WCAG AA contrast everywhere; visible 2px yellow focus rings with offset; full keyboard navigation; semantic landmarks (`header`, `nav`, `main`, `section` with `aria-labelledby`, `footer`); accordion and mobile menu ARIA-correct; decorative canvas is `aria-hidden`.
- The terminal mockup has a text alternative describing the demo.

**SEO and meta**
- Title: `Valkyria | Terminal-native AI agent`. Description: "Plan, build and ship from your terminal with Groq, Gemini and NVIDIA, on your own keys."
- Open Graph and Twitter images (1200x630, graphite with the shield), favicon from the logo, `robots.txt`, `sitemap.xml`, JSON-LD `SoftwareApplication`.

---

## 10. File structure

```
valkyria-site/
  app/
    layout.tsx              # fonts, providers, nav, footer, canvas mount
    page.tsx                # composes the 7 sections
    globals.css             # tokens, grain, base
    docs/[[...slug]]/page.tsx
    terms/page.tsx
    privacy/page.tsx
    not-found.tsx
  components/
    nav/                    # Navbar, MobileMenu, ScrollSpy
    sections/               # Hero, HowItWorks, Different, UnderTheHood, Faq, Setup, Footer
    three/                  # Scene, Shield, Wings, Orbs, Rings, Plates, Stairs, Dust, CameraRig
    ui/                     # Logo, MagneticButton, CopyChip, TerminalMock, Accordion, CursorFollower, ProgressRail, Marquee
    docs/                   # Sidebar, Toc, CommandPalette, Callout, CodeBlock
  lib/
    scroll-store.ts         # zustand: progress, section, velocity
    lenis.ts                # smooth scroll + ScrollTrigger sync
    constants.ts            # copy, commands, links
  content/docs/*.mdx
  public/                   # og.png, favicon
```

---

## 11. Do not

- No purple or neon gradients, no gradient or shimmer text, no glassmorphism overload (glass only on nav, terminal and one panel).
- No stock 3D blobs; every 3D object is a Valkyria motif (shield, wings, rings, shards, arrow).
- No emojis in UI, no lorem ipsum, no placeholder avatars.
- No heavy shadows, no pure `#000` backgrounds (use the graphite scale).
- Do not copy layouts, copy, mascots or assets from the inspiration sites.
- Do not let yellow exceed about 10% of any viewport.

---

## 12. Acceptance checklist

- [ ] All 7 sections render in the specified order with the specified copy.
- [ ] 3D scene responds to scroll in every section and transitions smoothly.
- [ ] Navbar hides/shows on scroll direction and scroll-spy highlights correctly.
- [ ] Cloud-light "different" section wipes in, with readable contrast.
- [ ] `/docs`, `/terms`, `/privacy` and `/404` exist, share nav and footer, and are fully readable.
- [ ] Command palette and TOC work on `/docs`.
- [ ] Copy-to-clipboard chips work.
- [ ] Reduced-motion and no-WebGL fallbacks work.
- [ ] Mobile layout has no horizontal scroll and a lighter 3D scene.
- [ ] Lighthouse: Performance 85+ desktop, Accessibility 95+, SEO 95+.
- [ ] Palette adheres to the tokens; yellow stays rare.