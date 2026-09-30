"""DashBite Agent Prompt Board — independent Architect / Implementer / Reviewer chats."""

from __future__ import annotations

import streamlit as st

from pipeline.prompts.content import (
    BASE_PLAN,
    BASE_PLAN_TEACH,
    BASE_PLAN_TITLE,
    CREATE_SKILL_PROMPT,
    STAGES,
    StagePrompts,
    WRAP_UP_PROMPT,
    WRAP_UP_TEACH,
    WRAP_UP_TITLE,
)

PHASES = (
    ("plan", "Think it through", "Fresh architect chat — append stage to docs/plan.md (+ Manual Smoke Test)"),
    ("execute", "Build it", "Fresh implementer chat — read docs/plan.md, then build"),
    ("test", "Check it", "Fresh reviewer chat — verify code, tests & smoke-test docs"),
)


def _prompt_text(stage: StagePrompts, key: str) -> str:
    return getattr(stage, key)


def _inject_style() -> None:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

          html, body, [class*="css"] {
            font-family: 'DM Sans', sans-serif;
          }

          .block-container {
            padding-top: 1.5rem;
            max-width: 1100px;
          }

          .dpb-hero {
            background: linear-gradient(135deg, #0f241f 0%, #1a3a32 45%, #243d28 100%);
            color: #e8f2ee;
            padding: 1.75rem 1.75rem 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.25rem;
            border: 1px solid #2d5a4e;
          }
          .dpb-hero h1 {
            font-size: 1.85rem;
            font-weight: 700;
            margin: 0 0 0.35rem 0;
            letter-spacing: -0.02em;
          }
          .dpb-hero p {
            margin: 0;
            opacity: 0.9;
            font-size: 1rem;
            line-height: 1.45;
          }
          .dpb-loop {
            display: inline-flex;
            gap: 0.5rem;
            margin-top: 1rem;
            flex-wrap: wrap;
          }
          .dpb-chip {
            background: rgba(232, 242, 238, 0.12);
            border: 1px solid rgba(232, 242, 238, 0.25);
            padding: 0.35rem 0.75rem;
            border-radius: 6px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.8rem;
            letter-spacing: 0.04em;
          }
          .dpb-how {
            background: rgba(61, 143, 118, 0.14);
            border-left: 4px solid #3d8f76;
            padding: 0.85rem 1rem;
            margin-bottom: 1.25rem;
            border-radius: 0 8px 8px 0;
            color: inherit;
            font-size: 0.95rem;
          }
          .dpb-roles {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.75rem;
            margin-bottom: 1.25rem;
          }
          @media (max-width: 800px) {
            .dpb-roles { grid-template-columns: 1fr; }
          }
          .dpb-role {
            background: rgba(61, 143, 118, 0.08);
            border: 1px solid rgba(61, 143, 118, 0.35);
            border-radius: 10px;
            padding: 0.85rem 1rem;
            color: inherit;
            font-size: 0.9rem;
          }
          .dpb-role strong {
            display: block;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.78rem;
            letter-spacing: 0.04em;
            margin-bottom: 0.35rem;
            color: #3d8f76;
          }
          .dpb-stage-meta {
            color: inherit;
            opacity: 0.9;
            margin-bottom: 0.75rem;
            font-size: 0.95rem;
          }
          div[data-testid="stExpander"] details {
            border: 1px solid rgba(61, 143, 118, 0.35) !important;
            border-radius: 10px !important;
            background: transparent !important;
          }
          div[data-testid="stExpander"] details > div,
          div[data-testid="stExpander"] [data-testid="stExpanderDetails"],
          div[data-testid="stExpander"] .streamlit-expanderContent,
          div[data-testid="stExpander"] summary {
            background: transparent !important;
            color: inherit !important;
          }
          code, pre, .stCode {
            font-family: 'IBM Plex Mono', monospace !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="DashBite Agent Prompts",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_style()

    nav_options = [
        ("all", "All stages"),
        ("base", f"0′ — {BASE_PLAN_TITLE}"),
        *[ (f"stage-{s.number}", f"Stage {s.number} — {s.title}") for s in STAGES ],
        ("wrap", f"6′ — {WRAP_UP_TITLE}"),
        ("skill", "Take the workflow with you"),
    ]
    with st.sidebar:
        st.markdown("### Stages")
        st.caption("Open this panel from the ☰ control to jump around the board.")
        focus = st.radio(
            "Jump to",
            options=[key for key, _ in nav_options],
            format_func=lambda key: dict(nav_options)[key],
            index=0,
            label_visibility="collapsed",
        )

    st.markdown(
        """
        <div class="dpb-hero">
          <h1>DashBite</h1>
          <p>Agent Prompt Board — Think it through → Build it → Check it as three
          independent Cursor chats. The repo, a single living <code>docs/plan.md</code>, and tests are the shared source of truth.</p>
          <div class="dpb-loop">
            <span class="dpb-chip">THINK · ARCHITECT</span>
            <span class="dpb-chip">BUILD · IMPLEMENTER</span>
            <span class="dpb-chip">CHECK · REVIEWER</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="dpb-how">
          <strong>How to use in the demo:</strong>
          Each step is intentionally run in a <em>fresh</em> Cursor chat.
          Think it through acts like an architect (appends to <code>docs/plan.md</code>,
          including a <em>Manual Smoke Test</em> — never overwrites earlier stages),
          Build it like an implementer (reads <code>docs/plan.md</code> first), and
          Check it like a reviewer. After Build, run the smoke test from the terminal
          with the class before opening the reviewer chat. Wait for full
          <code>pytest</code> green before the next stage's architect chat.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="dpb-roles">
          <div class="dpb-role">
            <strong>ARCHITECT</strong>
            Fresh chat. Inspect the repo, append this stage to docs/plan.md (design + automated tests + Manual Smoke Test) — don't implement.
          </div>
          <div class="dpb-role">
            <strong>IMPLEMENTER</strong>
            Fresh chat. Read docs/plan.md first, then build. Keep this stage's smoke-test section runnable.
          </div>
          <div class="dpb-role">
            <strong>REVIEWER</strong>
            Fresh chat. Read docs/plan.md, verify code/tests, and confirm this stage's Manual Smoke Test still matches reality.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    show_all = focus == "all"
    expand_all = st.toggle("Expand all stages", value=True) if show_all else True

    def _show(key: str) -> bool:
        return show_all or focus == key

    if _show("base"):
        with st.expander(f"0′ — {BASE_PLAN_TITLE}", expanded=expand_all or focus == "base"):
            st.markdown(
                f'<p class="dpb-stage-meta"><strong>Teach:</strong> {BASE_PLAN_TEACH}</p>',
                unsafe_allow_html=True,
            )
            st.caption("Room warm-up — diagram & mental model; click the copy icon")
            st.code(BASE_PLAN, language="markdown")

    for stage in STAGES:
        key = f"stage-{stage.number}"
        if not _show(key):
            continue
        header = f"Stage {stage.number} — {stage.title}"
        with st.expander(header, expanded=expand_all or focus == key):
            st.markdown(
                f'<p class="dpb-stage-meta"><strong>Teach:</strong> {stage.teach}</p>',
                unsafe_allow_html=True,
            )

            tabs = st.tabs([label for _, label, _ in PHASES])
            for tab, (pkey, label, caption) in zip(tabs, PHASES):
                with tab:
                    st.caption(f"{caption} — click the copy icon on the code block")
                    st.code(_prompt_text(stage, pkey), language="markdown")
                    if pkey == "execute":
                        st.markdown(
                            '<p class="dpb-stage-meta" style="margin-top:0.75rem;">'
                            "<strong>Live with the class:</strong> "
                            "<code>Build → run docs/plan.md smoke test manually → Check</code>"
                            "</p>",
                            unsafe_allow_html=True,
                        )

    if _show("wrap"):
        with st.expander(
            f"6′ — {WRAP_UP_TITLE}",
            expanded=expand_all or focus == "wrap",
        ):
            st.markdown(
                f'<p class="dpb-stage-meta"><strong>Teach:</strong> {WRAP_UP_TEACH}</p>',
                unsafe_allow_html=True,
            )
            st.caption("End of demo — paste into a fresh chat; click the copy icon")
            st.code(WRAP_UP_PROMPT, language="markdown")

    if _show("skill"):
        st.divider()
        st.markdown("## Take the workflow with you")
        st.caption("ARCHITECT → IMPLEMENTER → REVIEWER")
        st.markdown(
            """
The prompts above are intentionally explicit so we can see the workflow during the demo.
In a real project, we don't want to rewrite this scaffolding every time.

Cursor Skills let us package the workflow once and reuse it across projects.

Install the `dev-cycle` skill, then start three fresh chats for a feature
(and run the Manual Smoke Test from `docs/plan.md` between Implement and Review):
"""
        )
        st.code(
            "/dev-cycle architect Add caching to the API\n\n"
            "/dev-cycle implement Add caching to the API\n\n"
            "# then: run the Manual Smoke Test from docs/plan.md with the class\n\n"
            "/dev-cycle review Add caching to the API",
            language="text",
        )
        st.info(
            "Each chat starts fresh. The repository, a single docs/plan.md (append-only stages, including Manual Smoke Test), "
            "interfaces, and tests provide the shared context between agents."
        )
        st.markdown("### Create it once")
        st.caption("Paste into Cursor — click the copy icon")
        st.code(CREATE_SKILL_PROMPT, language="markdown")
        st.markdown(
            "Prefer a plain markdown file for Codex, Claude Code, or any agent? "
            "See [`docs/dev-cycle.md`](../docs/dev-cycle.md)."
        )
        st.markdown(
            "*Prompt engineering gets you through one task. "
            "A skill turns the workflow into reusable engineering infrastructure.*"
        )

    st.divider()
    st.caption(
        "Teaching point: docs/plan.md (append-only living plan with Manual Smoke Tests), the repo, filesystem contracts, "
        "and automated tests let independent agents collaborate without shared chat history. "
        "Full pytest green before the next stage. Local board: make prompts → :8502."
    )


if __name__ == "__main__":
    main()
