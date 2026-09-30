"""Generate a static GitHub Pages site from prompt content.

Usage (from repo root):
  PYTHONPATH=. python -m pipeline.prompts.build_static
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from pipeline.prompts.content import (
    BASE_PLAN,
    BASE_PLAN_TEACH,
    BASE_PLAN_TITLE,
    CREATE_SKILL_PROMPT,
    STAGES,
    WRAP_UP_PROMPT,
    WRAP_UP_TEACH,
    WRAP_UP_TITLE,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "index.html"


def build() -> Path:
    data = {
        "base": {
            "title": BASE_PLAN_TITLE,
            "teach": BASE_PLAN_TEACH,
            "plan": BASE_PLAN,
        },
        "wrap_up": {
            "title": WRAP_UP_TITLE,
            "teach": WRAP_UP_TEACH,
            "plan": WRAP_UP_PROMPT,
        },
        "stages": [
            {
                "number": s.number,
                "title": s.title,
                "teach": s.teach,
                "plan": s.plan,
                "execute": s.execute,
                "test": s.test,
            }
            for s in STAGES
        ],
    }
    # Prevent accidental </script> breakout inside the JSON blob
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    skill_prompt_html = html.escape(CREATE_SKILL_PROMPT)
    skill_prompt_id = "create-skill-prompt"

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
  <meta http-equiv="Pragma" content="no-cache" />
  <meta http-equiv="Expires" content="0" />
  <title>DashBite — Agent Prompt Board</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --bg: #0e1117;
      --surface: #1a2421;
      --hero-a: #0f241f;
      --hero-b: #1a3a32;
      --hero-c: #243d28;
      --border: #2d5a4e;
      --accent: #3d8f76;
      --text: #e8f2ee;
      --muted: #b8c9c2;
      --primary: #ff4b4b;
      --code-bg: #0b0f0d;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "DM Sans", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.45;
    }}
    main {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 1.5rem 1.25rem 3rem;
    }}
    .hero {{
      background: linear-gradient(135deg, var(--hero-a) 0%, var(--hero-b) 45%, var(--hero-c) 100%);
      color: var(--text);
      padding: 1.75rem;
      border-radius: 12px;
      margin-bottom: 1.25rem;
      border: 1px solid var(--border);
    }}
    .hero h1 {{
      margin: 0 0 0.35rem;
      font-size: 1.85rem;
      letter-spacing: -0.02em;
    }}
    .hero p {{ margin: 0; opacity: 0.9; }}
    .chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-top: 1rem;
    }}
    .chip {{
      background: rgba(232, 242, 238, 0.12);
      border: 1px solid rgba(232, 242, 238, 0.25);
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      font-family: "IBM Plex Mono", monospace;
      font-size: 0.8rem;
      letter-spacing: 0.04em;
    }}
    .how {{
      background: rgba(61, 143, 118, 0.14);
      border-left: 4px solid var(--accent);
      padding: 0.85rem 1rem;
      margin-bottom: 1.25rem;
      border-radius: 0 8px 8px 0;
      font-size: 0.95rem;
    }}
    .how code {{
      font-family: "IBM Plex Mono", monospace;
      color: #9fdbc5;
    }}
    .toolbar {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 1rem;
    }}
    .toolbar label {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      cursor: pointer;
      color: var(--muted);
    }}
    details.stage {{
      border: 1px solid rgba(61, 143, 118, 0.35);
      border-radius: 10px;
      margin-bottom: 0.75rem;
      background: transparent;
      overflow: hidden;
    }}
    details.stage > summary {{
      cursor: pointer;
      padding: 0.9rem 1rem;
      font-weight: 600;
      list-style: none;
      background: var(--surface);
    }}
    details.stage > summary::-webkit-details-marker {{ display: none; }}
    details.stage > summary::before {{
      content: "▸";
      display: inline-block;
      margin-right: 0.55rem;
      color: var(--accent);
      transition: transform 0.15s ease;
    }}
    details.stage[open] > summary::before {{ transform: rotate(90deg); }}
    .stage-body {{ padding: 0.75rem 1rem 1.1rem; }}
    .teach {{
      color: var(--muted);
      margin: 0 0 0.85rem;
      font-size: 0.95rem;
    }}
    .tabs {{
      display: flex;
      gap: 0.25rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 0.75rem;
    }}
    .tab {{
      background: transparent;
      border: none;
      color: var(--muted);
      padding: 0.55rem 0.9rem;
      cursor: pointer;
      font-family: inherit;
      font-size: 0.95rem;
      border-bottom: 2px solid transparent;
    }}
    .tab.active {{
      color: var(--primary);
      border-bottom-color: var(--primary);
    }}
    .panel {{ display: none; }}
    .panel.active {{ display: block; }}
    .caption {{
      color: var(--muted);
      font-size: 0.85rem;
      margin-bottom: 0.4rem;
    }}
    .prompt-wrap {{
      position: relative;
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.75rem 0.85rem 0.85rem;
    }}
    .prompt-wrap pre {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: "IBM Plex Mono", monospace;
      font-size: 0.82rem;
      line-height: 1.5;
      color: var(--text);
    }}
    .copy-btn {{
      position: absolute;
      top: 0.5rem;
      right: 0.5rem;
      background: var(--hero-b);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.3rem 0.65rem;
      font-size: 0.8rem;
      cursor: pointer;
      font-family: inherit;
    }}
    .copy-btn:hover {{ background: var(--border); }}
    .copy-btn.copied {{ background: var(--accent); border-color: var(--accent); }}
    .roles {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.75rem;
      margin-bottom: 1.25rem;
    }}
    @media (max-width: 800px) {{
      .roles {{ grid-template-columns: 1fr; }}
    }}
    .role {{
      background: rgba(61, 143, 118, 0.08);
      border: 1px solid rgba(61, 143, 118, 0.35);
      border-radius: 10px;
      padding: 0.85rem 1rem;
      font-size: 0.9rem;
      color: var(--text);
    }}
    .role strong {{
      display: block;
      font-family: "IBM Plex Mono", monospace;
      font-size: 0.78rem;
      letter-spacing: 0.04em;
      margin-bottom: 0.35rem;
      color: var(--accent);
    }}
    footer {{
      margin-top: 1.5rem;
      color: var(--muted);
      font-size: 0.85rem;
    }}
    .outro {{
      margin-top: 2rem;
      padding: 1.5rem 1.35rem 1.35rem;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: linear-gradient(160deg, #132820 0%, #0f1a17 55%, #161b19 100%);
    }}
    .outro h2 {{
      margin: 0 0 0.75rem;
      font-size: 1.45rem;
      letter-spacing: -0.02em;
    }}
    .outro-flow {{
      font-family: "IBM Plex Mono", monospace;
      font-size: 0.85rem;
      letter-spacing: 0.06em;
      color: var(--accent);
      margin: 0 0 1rem;
    }}
    .outro p {{
      color: var(--muted);
      margin: 0 0 0.85rem;
      font-size: 0.95rem;
    }}
    .outro .examples {{
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.85rem 1rem;
      margin: 0 0 1rem;
      font-family: "IBM Plex Mono", monospace;
      font-size: 0.85rem;
      line-height: 1.7;
      color: var(--text);
      white-space: pre-wrap;
    }}
    .outro .callout {{
      border-left: 4px solid var(--accent);
      background: rgba(61, 143, 118, 0.12);
      padding: 0.7rem 0.9rem;
      border-radius: 0 8px 8px 0;
      margin: 0 0 1.25rem;
      color: var(--text);
      font-size: 0.92rem;
    }}
    .outro h3 {{
      margin: 0 0 0.65rem;
      font-size: 1.05rem;
    }}
    .outro .takeaway {{
      margin: 1rem 0 0;
      font-size: 0.95rem;
      color: var(--text);
      font-style: italic;
    }}
    .outro .portable {{
      margin-top: 0.75rem;
      font-size: 0.85rem;
      color: var(--muted);
    }}
    .outro .portable a {{
      color: #9fdbc5;
    }}
    .smoke-reminder {{
      margin-top: 0.85rem;
      padding: 0.55rem 0.75rem;
      border-radius: 8px;
      border: 1px dashed rgba(61, 143, 118, 0.55);
      background: rgba(61, 143, 118, 0.1);
      font-family: "IBM Plex Mono", monospace;
      font-size: 0.8rem;
      letter-spacing: 0.02em;
      color: var(--text);
    }}
    .smoke-reminder strong {{
      color: var(--accent);
      font-weight: 500;
    }}
    .nav-burger {{
      position: fixed;
      top: 1rem;
      right: 1rem;
      z-index: 1002;
      width: 2.75rem;
      height: 2.75rem;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 5px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    }}
    .nav-burger span {{
      display: block;
      width: 1.15rem;
      height: 2px;
      background: var(--text);
      border-radius: 1px;
      transition: transform 0.2s ease, opacity 0.2s ease;
    }}
    body.nav-open .nav-burger span:nth-child(1) {{
      transform: translateY(7px) rotate(45deg);
    }}
    body.nav-open .nav-burger span:nth-child(2) {{
      opacity: 0;
    }}
    body.nav-open .nav-burger span:nth-child(3) {{
      transform: translateY(-7px) rotate(-45deg);
    }}
    .nav-backdrop {{
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.45);
      z-index: 1000;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.2s ease;
    }}
    body.nav-open .nav-backdrop {{
      opacity: 1;
      pointer-events: auto;
    }}
    .nav-drawer {{
      position: fixed;
      top: 0;
      right: 0;
      width: min(20rem, 88vw);
      height: 100%;
      z-index: 1001;
      background: #121a17;
      border-left: 1px solid var(--border);
      padding: 4.5rem 1.1rem 1.5rem;
      transform: translateX(105%);
      transition: transform 0.22s ease;
      overflow-y: auto;
    }}
    body.nav-open .nav-drawer {{
      transform: translateX(0);
    }}
    .nav-drawer h2 {{
      margin: 0 0 0.85rem;
      font-family: "IBM Plex Mono", monospace;
      font-size: 0.78rem;
      letter-spacing: 0.08em;
      color: var(--accent);
      font-weight: 500;
    }}
    .nav-drawer a {{
      display: block;
      padding: 0.65rem 0.75rem;
      margin-bottom: 0.35rem;
      border-radius: 8px;
      color: var(--text);
      text-decoration: none;
      border: 1px solid transparent;
      font-size: 0.92rem;
    }}
    .nav-drawer a:hover,
    .nav-drawer a:focus-visible {{
      background: rgba(61, 143, 118, 0.14);
      border-color: rgba(61, 143, 118, 0.35);
      outline: none;
    }}
    .nav-drawer a .nav-meta {{
      display: block;
      margin-top: 0.15rem;
      font-size: 0.75rem;
      color: var(--muted);
    }}
  </style>
</head>
<body>
  <button class="nav-burger" type="button" id="nav-burger" aria-label="Open stages menu" aria-expanded="false" aria-controls="nav-drawer">
    <span></span><span></span><span></span>
  </button>
  <div class="nav-backdrop" id="nav-backdrop" hidden></div>
  <nav class="nav-drawer" id="nav-drawer" aria-label="Stages">
    <h2>JUMP TO STAGE</h2>
    <div id="nav-links"></div>
  </nav>
  <main>
    <div class="hero">
      <h1>DashBite</h1>
      <p>Agent Prompt Board — Think it through → Build it → Check it as three
        independent Cursor chats. The repo, a single living <code>docs/plan.md</code>, and tests are the shared source of truth.</p>
      <div class="chips">
        <span class="chip">THINK · ARCHITECT</span>
        <span class="chip">BUILD · IMPLEMENTER</span>
        <span class="chip">CHECK · REVIEWER</span>
      </div>
    </div>

    <div class="how">
      <strong>How to use in the demo:</strong>
      Each step is intentionally run in a <em>fresh</em> Cursor chat.
      Think it through acts like an architect (appends to <code>docs/plan.md</code>,
      including a <em>Manual Smoke Test</em> — never overwrites earlier stages),
      Build it like an implementer (reads <code>docs/plan.md</code> first), and
      Check it like a reviewer. After Build, run the smoke test from the terminal
      with the class before opening the reviewer chat. Wait for full
      <code>pytest</code> green before the next stage's architect chat.
    </div>

    <div class="roles">
      <div class="role">
        <strong>ARCHITECT</strong>
        Fresh chat. Inspect the repo, append this stage to docs/plan.md (design + automated tests + Manual Smoke Test) — don't implement.
      </div>
      <div class="role">
        <strong>IMPLEMENTER</strong>
        Fresh chat. Read docs/plan.md first, then build. Keep this stage's smoke-test section runnable.
      </div>
      <div class="role">
        <strong>REVIEWER</strong>
        Fresh chat. Read docs/plan.md, verify code/tests, and confirm this stage's Manual Smoke Test still matches reality.
      </div>
    </div>

    <div class="toolbar">
      <label><input type="checkbox" id="expand-all" checked /> Expand all stages</label>
    </div>

    <div id="board"></div>

    <section class="outro" id="outro" aria-label="Take the workflow with you">
      <h2>Take the workflow with you</h2>
      <p class="outro-flow">ARCHITECT → IMPLEMENTER → REVIEWER</p>
      <p>
        The prompts above are intentionally explicit so we can see the workflow during the demo.
        In a real project, we don't want to rewrite this scaffolding every time.
      </p>
      <p>
        Cursor Skills let us package the workflow once and reuse it across projects.
      </p>
      <p>
        Install the <code>dev-cycle</code> skill, then start three fresh chats for a feature
        (and run the Manual Smoke Test from <code>docs/plan.md</code> between Implement and Review):
      </p>
      <div class="examples">/dev-cycle architect Add caching to the API

/dev-cycle implement Add caching to the API

# then: run the Manual Smoke Test from docs/plan.md with the class

/dev-cycle review Add caching to the API</div>
      <div class="callout">
        Each chat starts fresh. The repository, a single <code>docs/plan.md</code> (append-only stages, including Manual Smoke Test),
        interfaces, and tests provide the shared context between agents.
      </div>
      <h3>Create it once</h3>
      <div class="caption">Paste into Cursor — click Copy</div>
      <div class="prompt-wrap">
        <button class="copy-btn" type="button" data-copy="{skill_prompt_id}">Copy</button>
        <pre id="{skill_prompt_id}">{skill_prompt_html}</pre>
      </div>
      <p class="portable">
        Prefer a plain markdown file for Codex, Claude Code, or any agent?
        Use <a href="./dev-cycle.md">dev-cycle.md</a> in this docs folder.
      </p>
      <p class="takeaway">
        Prompt engineering gets you through one task. A skill turns the workflow into reusable engineering infrastructure.
      </p>
    </section>

    <footer>
      Teaching point: docs/plan.md (append-only living plan with Manual Smoke Tests), the repo, filesystem contracts,
      and automated tests let independent agents collaborate without shared chat history.
      Full <code>pytest</code> green before the next stage.
      Local Streamlit board: <code>make prompts</code> → :8502.
    </footer>
  </main>

  <script type="application/json" id="prompt-data">{payload}</script>
  <script>
    const data = JSON.parse(document.getElementById("prompt-data").textContent);
    const board = document.getElementById("board");

    function escapeHtml(s) {{
      return s
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
    }}

    function promptBlock(label, text) {{
      const id = "p-" + Math.random().toString(36).slice(2);
      return `
        <div class="caption">${{label}} — click Copy</div>
        <div class="prompt-wrap">
          <button class="copy-btn" type="button" data-copy="${{id}}">Copy</button>
          <pre id="${{id}}">${{escapeHtml(text)}}</pre>
        </div>`;
    }}

    function stageDetails(title, teach, innerHtml, open, id) {{
      return `
        <details class="stage" id="${{id}}" ${{open ? "open" : ""}}>
          <summary>${{escapeHtml(title)}}</summary>
          <div class="stage-body">
            <p class="teach"><strong>Teach:</strong> ${{escapeHtml(teach)}}</p>
            ${{innerHtml}}
          </div>
        </details>`;
    }}

    function tabsFor(stage) {{
      const phases = [
        ["plan", "Think it through", "Fresh architect chat — append stage to docs/plan.md (+ Manual Smoke Test)"],
        ["execute", "Build it", "Fresh implementer chat — read docs/plan.md, then build"],
        ["test", "Check it", "Fresh reviewer chat — verify code, tests & smoke-test docs"],
      ];
      const tabBtns = phases.map(([key, label], i) =>
        `<button class="tab ${{i === 0 ? "active" : ""}}" type="button" data-tab="${{key}}">${{label}}</button>`
      ).join("");
      const panels = phases.map(([key, , caption], i) =>
        `<div class="panel ${{i === 0 ? "active" : ""}}" data-panel="${{key}}">
          ${{promptBlock(caption, stage[key])}}
          ${{key === "execute" ? '<div class="smoke-reminder"><strong>Live with the class:</strong> Build → run docs/plan.md smoke test manually → Check</div>' : ""}}
        </div>`
      ).join("");
      return `<div class="tabs">${{tabBtns}}</div>${{panels}}`;
    }}

    function navEntries() {{
      const entries = [
        {{ id: "stage-base", label: "0′ — " + data.base.title, meta: data.base.teach }},
      ];
      for (const s of data.stages) {{
        entries.push({{
          id: "stage-" + s.number,
          label: `Stage ${{s.number}} — ${{s.title}}`,
          meta: s.teach,
        }});
      }}
      if (data.wrap_up) {{
        entries.push({{
          id: "stage-wrap",
          label: "6′ — " + data.wrap_up.title,
          meta: data.wrap_up.teach,
        }});
      }}
      entries.push({{
        id: "outro",
        label: "Take the workflow with you",
        meta: "dev-cycle skill",
      }});
      return entries;
    }}

    function renderNav() {{
      const root = document.getElementById("nav-links");
      root.innerHTML = navEntries().map((e) =>
        `<a href="#${{e.id}}" data-nav-target="${{e.id}}">${{escapeHtml(e.label)}}<span class="nav-meta">${{escapeHtml(e.meta)}}</span></a>`
      ).join("");
    }}

    function setNavOpen(open) {{
      document.body.classList.toggle("nav-open", open);
      const burger = document.getElementById("nav-burger");
      const backdrop = document.getElementById("nav-backdrop");
      burger.setAttribute("aria-expanded", open ? "true" : "false");
      burger.setAttribute("aria-label", open ? "Close stages menu" : "Open stages menu");
      backdrop.hidden = !open;
    }}

    function jumpToStage(id) {{
      const el = document.getElementById(id);
      if (!el) return;
      if (el.tagName === "DETAILS") el.open = true;
      el.scrollIntoView({{ behavior: "smooth", block: "start" }});
      setNavOpen(false);
    }}

    function render(openAll) {{
      const baseInner = promptBlock(
        "Room warm-up — diagram & mental model",
        data.base.plan
      );
      let html = stageDetails(
        "0′ — " + data.base.title,
        data.base.teach,
        baseInner,
        openAll,
        "stage-base"
      );
      for (const s of data.stages) {{
        html += stageDetails(
          `Stage ${{s.number}} — ${{s.title}}`,
          s.teach,
          tabsFor(s),
          openAll,
          "stage-" + s.number
        );
      }}
      if (data.wrap_up) {{
        html += stageDetails(
          "6′ — " + data.wrap_up.title,
          data.wrap_up.teach,
          promptBlock("End of demo — paste into a fresh chat", data.wrap_up.plan),
          openAll,
          "stage-wrap"
        );
      }}
      board.innerHTML = html;
      bindInteractions();
    }}

    function bindInteractions() {{
      board.querySelectorAll(".tabs").forEach((tabBar) => {{
        const parent = tabBar.parentElement;
        tabBar.querySelectorAll(".tab").forEach((btn) => {{
          btn.addEventListener("click", () => {{
            tabBar.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
            parent.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
            btn.classList.add("active");
            parent.querySelector(`[data-panel="${{btn.dataset.tab}}"]`).classList.add("active");
          }});
        }});
      }});
    }}

    document.getElementById("nav-burger").addEventListener("click", () => {{
      setNavOpen(!document.body.classList.contains("nav-open"));
    }});
    document.getElementById("nav-backdrop").addEventListener("click", () => setNavOpen(false));
    document.getElementById("nav-links").addEventListener("click", (e) => {{
      const link = e.target.closest("[data-nav-target]");
      if (!link) return;
      e.preventDefault();
      jumpToStage(link.dataset.navTarget);
    }});
    document.addEventListener("keydown", (e) => {{
      if (e.key === "Escape") setNavOpen(false);
    }});

    document.addEventListener("click", async (e) => {{
      const btn = e.target.closest(".copy-btn");
      if (!btn) return;
      const pre = document.getElementById(btn.dataset.copy);
      if (!pre) return;
      try {{
        await navigator.clipboard.writeText(pre.textContent);
        btn.textContent = "Copied";
        btn.classList.add("copied");
        setTimeout(() => {{
          btn.textContent = "Copy";
          btn.classList.remove("copied");
        }}, 1200);
      }} catch (err) {{
        btn.textContent = "Select text";
      }}
    }});

    const expandAll = document.getElementById("expand-all");
    expandAll.addEventListener("change", () => render(expandAll.checked));
    renderNav();
    render(true);
    setNavOpen(false);
  </script>
</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"Wrote {path}")
