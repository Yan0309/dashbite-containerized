# Dev Cycle — Architect → Implementer → Reviewer

Portable workflow for Cursor, Claude Code, Codex, and similar coding agents.

Each role runs in a **fresh chat**. Never depend on previous conversational context. The **repository** and a single living **`docs/plan.md`** are the shared source of truth.

## How to use

Start three independent sessions for a feature:

```text
Architect:  /dev-cycle architect Add caching to the API
Implement:  /dev-cycle implement Add caching to the API
Review:     /dev-cycle review Add caching to the API
```

Between Implement and Review, run the **Manual Smoke Test** from the relevant section of `docs/plan.md` live from the terminal.

```text
Architect (append to docs/plan.md) → Implementer (build) → Manual smoke test from docs/plan.md → Reviewer
```

If your tool does not support `/dev-cycle`, paste the matching role section below and append the feature request.

---

## Architect

- inspect the current repository
- do not modify implementation files (you may create/update `docs/plan.md` only)
- understand the requested feature / stage
- propose the smallest clean design
- identify relevant files/interfaces
- explain automated test strategy
- document a **Manual Smoke Test** for a live demo after implementation

Maintain **one** plan file at `docs/plan.md`:

- if missing, create it with a short project header, then add this stage/feature section
- if it exists, **append** the new section at the end — never overwrite the whole file or delete earlier stages

```markdown
## <Feature or Stage N — Title>

### Goal
...

### Proposed changes
- ...

### Architecture / boundaries
- ...

### Automated tests
- Unit: ...
- Regression: ...
- Integration: ...

### Manual Smoke Test

#### What we're proving
...

#### Terminal
(pasteable commands; label Terminal 1 / 2 / 3 if needed)

#### Watch for
...

#### Stop
Ctrl+C when a process should be stopped
```

Manual Smoke Test rules: visible logs/files/outputs; short and pasteable; use real project commands; do **not** use `pytest` as the smoke test. Stop after updating `docs/plan.md` — do not implement.

---

## Implement

- assume the planning conversation is unavailable
- inspect the repository and reconstruct context yourself
- **read `docs/plan.md` first** (focus on the latest / relevant section; earlier sections are context); treat it as the agreed architecture, automated tests, and Manual Smoke Test handoff
- implement the requested behavior using existing patterns
- keep the change scoped
- add/update relevant tests
- run relevant tests and the broader suite when practical
- when done, do **not** rewrite `docs/plan.md` — if commands or outputs changed, update **only that section's Manual Smoke Test** so it stays runnable
- summarize what changed and test status

---

## Review

- assume another agent implemented the feature
- **read `docs/plan.md` first** for intended behavior, architecture, automated test strategy, and Manual Smoke Test
- inspect the change like a PR you did not author
- verify the requested behavior and architecture against that contract
- look for bugs, regressions, coupling, edge cases, and weak tests
- add useful missing tests
- fix implementation bugs rather than weakening legitimate tests
- run the relevant tests and broader suite
- confirm the documented Manual Smoke Test is still accurate and runnable
- keep the relevant section in `docs/plan.md` synchronized with reality if commands or outputs changed — never wipe earlier stages
- summarize findings and final test status

---

## Across all roles

- inspect before assuming
- prefer existing project conventions
- avoid unnecessary abstractions
- keep changes small and reviewable
- the single `docs/plan.md` (with Manual Smoke Tests) is part of the handoff contract between independent agents

Two verification layers:
- **Manual smoke test** — can we visibly show the system works?
- **Automated tests / review** — is the behavior correct and does it stay correct?

---

## Cursor install (user-level skill)

Copy to `~/.cursor/skills/dev-cycle/SKILL.md`, or paste the create-skill prompt from the DashBite Prompt Board (“Take the workflow with you”).
