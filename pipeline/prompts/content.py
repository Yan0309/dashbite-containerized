"""Stage metadata and Think / Build / Check prompts (independent agent chats)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StagePrompts:
    number: int
    title: str
    teach: str
    plan: str  # Think it through — Architect
    execute: str  # Build it — Implementer
    test: str  # Check it — Reviewer


BASE_PLAN_TITLE = "Base plan — Pipeline diagram"
BASE_PLAN_TEACH = (
    "Warm up: one shared mental model before anyone opens an agent chat on code."
)
BASE_PLAN = """\
We're about to build a small ML pipeline together. Before anyone touches application code, help me sketch the system so everyone in the room has the same mental model.

The product story is DashBite: food-delivery orders come in, and we want to predict whether an order will be late. Keep the raw fields short — order_id, timestamp, distance_km, prep_minutes, order_value, was_late.

Architecturally I want something modular and demo-friendly:
- separate stages that feel like separate processes
- they hand off through folders under data/, not by importing each other
- training publishes versioned checkpoints; inference is a separate consumer of the newest checkpoint on disk
- if training is down, inference should still work off whatever model is already there
- a lightweight Model Pulse dashboard that reads existing outputs rather than owning pipeline logic
- dashboards follow claim-first viz: active titles, human-readable labels, one story per chart — not a metrics dump
- Model Pulse must include a time-series of sample volume over time (not just a single volume number)
- no containers, Kafka, Spark, etc. — plain Python and files are enough

Orchestration non-negotiable for this project:
- everything we run in class or in smoke tests must be wired through a Makefile
- prefer targets like `make install`, `make test`, `make simulator`, `make preprocess`, `make train`, `make infer`, `make dashboard`, `make run` / `make stop`, `make clean-data`
- stages can still be implemented as `python -m pipeline.<stage>`, but the Makefile is the public interface the room uses
- a single living plan lives at `docs/plan.md` — Architect owns it; stages are appended, never wholesale-overwritten
- `docs/plan.md` Manual Smoke Tests should use `make …` commands, not ad-hoc python invocations, unless something truly has no make target yet (in which case add the target)

Sketch a Mermaid flowchart (left-to-right is fine) that captures that story, including the train write path and the infer read path. Then give me a few short bullets on the teaching beats we should keep repeating as we build — including that the Makefile is how we orchestrate the demo.

Create `docs/plan.md` (the one plan file for the whole demo) with that diagram and the short bullets under a clear header (e.g. `# DashBite — living plan` plus a `## Base — Pipeline diagram` section). Don't implement the pipeline yet — `docs/plan.md` only.
"""

CREATE_SKILL_PROMPT = """\
Use Cursor's /create-skill workflow to create a user-level skill named `dev-cycle` so I can use it across repositories.

The skill should support three roles: architect, implement, and review.

Each role may run in a completely fresh chat, so the skill must never depend on previous conversational context. The repository and a single living `docs/plan.md` should be treated as the shared source of truth.

Workflow reminder the skill should encode:
Architect (append to docs/plan.md) → Implementer (build) → Manual smoke test from docs/plan.md → Reviewer

Architect:
- inspect the current repository
- do not modify implementation files (may create/update `docs/plan.md` only)
- understand the requested feature / stage
- propose the smallest clean design
- identify relevant files/interfaces
- explain automated test strategy
- maintain ONE plan file at `docs/plan.md`: create it if missing; otherwise APPEND a new stage/feature section — never overwrite the whole file or delete earlier sections
- each appended section includes: Goal, Proposed changes, Architecture / boundaries, Automated tests, and a Manual Smoke Test (What we're proving / Terminal / Watch for / Stop)
- Manual Smoke Test must be a live demo from the terminal (visible logs, files on disk, readable outputs) — not pytest
- stop after updating docs/plan.md — do not implement

Implement:
- assume the planning conversation is unavailable
- inspect the repository and reconstruct context yourself
- read docs/plan.md first (focus on the latest / relevant stage section; earlier sections are context); treat it as the architecture, automated test, and Manual Smoke Test handoff
- implement the requested behavior using existing patterns
- keep the change scoped
- add/update relevant tests
- run relevant tests and the broader suite when practical
- never rewrite docs/plan.md from scratch; if the Manual Smoke Test drifted, update only that stage's Manual Smoke Test section so it stays runnable
- summarize what changed and test status

Review:
- assume another agent implemented the feature
- read docs/plan.md first for intended behavior, architecture, automated tests, and Manual Smoke Test
- inspect it like a PR you did not author
- verify the requested behavior and architecture against that contract
- look for bugs, regressions, coupling, edge cases, and weak tests
- add useful missing tests
- fix implementation bugs rather than weakening legitimate tests
- run the relevant tests and broader suite
- confirm the documented Manual Smoke Test is still accurate and runnable
- keep the relevant stage section in docs/plan.md synchronized with reality if commands or outputs changed (do not wipe earlier stages)
- summarize findings and final test status

Across all roles:
- inspect before assuming
- prefer existing project conventions
- avoid unnecessary abstractions
- keep changes small and reviewable
- the single `docs/plan.md` (with Manual Smoke Tests) is part of the handoff contract between independent agents

Make the skill available globally/user-level rather than only inside this repository.
"""

_PLAN_MD_SHAPE = """\
Maintain a single living plan at docs/plan.md (Architect-owned). Stages are appended; the file is never wholesale-overwritten.

Rules:
- if docs/plan.md does not exist, create it with a short project header, then add this stage's section
- if it already exists, APPEND this stage's section at the end — do not delete or rewrite earlier stages
- only the Architect owns structural additions; Implementer/Reviewer may fix this stage's Manual Smoke Test wording if commands drifted

Append a concise section shaped like:

## Stage N — <Title>

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

The Manual Smoke Test is for a live classroom demo — visible logs, files on disk, readable CSV/model output. Prefer `make …` targets from the project Makefile as the commands the room runs. Do NOT use `pytest` as the smoke test; that's automated verification (`make test` is fine for the automated gate, not for the live smoke demo).
"""

_DASHBOARD_VIZ = """\
Visualization quality bar (non-negotiable for dashboard UI):
- story first: each chart/section has one claim; titles state a finding (active voice), not variable names
- reduce decoding: human-readable axis labels (e.g. `% flagged late`, plain field names); prefer horizontal text
- do not make the audience do math: encode the decision quantity directly (drop rate, at-risk $, ranked failures)
- data-ink: few KPIs (about 2–3); no duplicate chart+table for the same fact; no competing multi-series that retell a KPI
- one Model Pulse page for ML health — keep business/ops KPIs out of this view
"""


STAGES: tuple[StagePrompts, ...] = (
    StagePrompts(
        number=0,
        title="Skeleton",
        teach="Smallest foundation: shared config, data folders, and a pytest gate.",
        plan=f"""\
We're starting DashBite from an empty-ish repo and need the smallest foundation before anything interesting.

Inspect the repository and append this stage's implementation plan to docs/plan.md (create the file if missing; never overwrite earlier stages).

Include:
- what we're changing
- relevant files/interfaces
- architectural constraints
- automated test strategy
- a manual smoke test I can run live from the terminal after implementation

Non-negotiables for this demo:
- config defaults include TRAIN_EVERY_N_EVENTS=2000 and BATCH_SIZE=50, overridable from the environment
- path helpers that resolve data/raw, features, models, predictions, quality and can create them
- pytest layout with unit / regression / integration markers

For the Manual Smoke Test, design something short and visible: load config (and maybe an env override), then show data dirs resolving/being created — e.g. a tiny `python -c` that prints load_config() and ensure_data_dirs().

{_PLAN_MD_SHAPE}

Do not implement the feature yet. Only update docs/plan.md (append this stage), then stop.
""",
        execute="""\
We're implementing Stage 0 of the DashBite pipeline.

Inspect the repository and read docs/plan.md first (focus on this stage's section; earlier stages are context). Treat it as the architecture and behavior handoff from the planning agent — including the Manual Smoke Test section.

Implement the planned skeleton using the existing project patterns: pipeline package with shared config and path helpers, data/ folders, pytest markers. Config defaults should include TRAIN_EVERY_N_EVENTS=2000 and BATCH_SIZE=50, overridable from the environment.

Keep the change scoped — no simulator or model yet. Add/update the relevant tests, and run them as you work.

When implementation is complete, do not overwrite docs/plan.md or earlier stage sections. Make sure this stage's Manual Smoke Test still matches the actual commands and behavior. If details changed, update only that stage's Manual Smoke Test section so it is runnable.
""",
        test="""\
Review the current Stage 0 skeleton as if this were a PR you did not author.

Read docs/plan.md first (this stage's section) to understand the intended behavior, architecture, automated test strategy, and manual smoke test.

Verify the implementation against that contract: shared config (TRAIN_EVERY_N_EVENTS / BATCH_SIZE), path helpers, data dirs, pytest layout.

Add or improve unit, regression, and integration tests where they provide meaningful coverage. Run the full pytest suite. If something fails, fix the underlying implementation problem rather than weakening a legitimate test.

Inspect whether the documented Manual Smoke Test is still accurate and runnable (you don't need to perform the live classroom demo). Keep this stage's section in docs/plan.md synchronized with reality if commands or outputs changed — never wipe earlier stages.

Finish with a short summary of what you checked, anything you changed, and whether the full suite passes.
""",
    ),
    StagePrompts(
        number=1,
        title="Simulator",
        teach="Make the system feel alive: synthetic orders land under data/raw/.",
        plan=f"""\
The project foundation should already be in place. Next I want the system to feel alive with synthetic DashBite orders.

Inspect the repository and append this stage's implementation plan to docs/plan.md (create the file if missing; never overwrite earlier stages).

Include:
- what we're changing
- relevant files/interfaces
- architectural constraints
- automated test strategy
- a manual smoke test I can run live from the terminal after implementation

Non-negotiables:
- columns: order_id, timestamp, distance_km, prep_minutes, order_value, was_late
- module runnable as `python -m pipeline.simulator`, exposed to the room via `make simulator`
- live-feeling logs (“new orders arrived”); messy rows OK for later cleaning

For the Manual Smoke Test, make it visual: Terminal 1 runs `make simulator`; Terminal 2 does `ls -lh data/raw` and `head` on a generated CSV. Students should see “new orders arrived” and new files appearing. Include Ctrl+C to stop the loop.

{_PLAN_MD_SHAPE}

Do not implement the feature yet. Only update docs/plan.md (append this stage), then stop.
""",
        execute="""\
We're implementing Stage 1 of the DashBite pipeline (simulator / intake).

Inspect the repository and read docs/plan.md first (focus on this stage's section; earlier stages are context). Treat it as the architecture and behavior handoff from the planning agent — including the Manual Smoke Test.

Implement the planned intake process: periodically write synthetic orders under data/raw/ with order_id, timestamp, distance_km, prep_minutes, order_value, was_late; live-feeling logs; shared config for batch size / poll interval; `python -m pipeline.simulator` under the hood with a `make simulator` target for the room.

Keep this scoped to intake. Add/update relevant tests and run them as you work.

When implementation is complete, do not overwrite docs/plan.md or earlier stage sections. Make sure this stage's Manual Smoke Test still matches the actual commands and behavior. If details changed, update only that stage's Manual Smoke Test section so it is runnable.
""",
        test="""\
Review the current Stage 1 simulator as if this were a PR you did not author.

Read docs/plan.md first (this stage's section) for intended behavior, architecture, automated tests, and the Manual Smoke Test.

Verify intake writes the expected columns under data/raw/, uses shared config, and doesn't reach into features/models/predictions. Strengthen unit/regression/integration coverage (seeded golden fixture + one-tick write). Run the full suite.

Inspect whether the documented Manual Smoke Test is still accurate and runnable. Keep this stage's section in docs/plan.md synchronized if commands or outputs changed — never wipe earlier stages. Fix real bugs rather than softening asserts.

Summarize findings, changes, and suite status.
""",
    ),
    StagePrompts(
        number=2,
        title="Preprocess",
        teach="Turn raw orders into a simple feature table under data/features/.",
        plan=f"""\
Raw orders are already landing under data/raw/. Next we need a preprocessing stage that turns them into model-ready features.

Inspect the repository and append this stage's implementation plan to docs/plan.md (create the file if missing; never overwrite earlier stages).

Include:
- what we're changing
- relevant files/interfaces
- architectural constraints
- automated test strategy
- a manual smoke test I can run live from the terminal after implementation

Non-negotiables:
- clean invalid rows; derive hour and is_peak; write under data/features/; keep was_late
- stages stay independent and talk through data/

For the Manual Smoke Test, prefer separate terminals so the room sees Simulator → data/raw → Preprocess → data/features via `make simulator` and `make preprocess`. Then `ls` / `head` a feature CSV and call out hour / is_peak / was_late. Include Ctrl+C for loops.

{_PLAN_MD_SHAPE}

Do not implement the feature yet. Only update docs/plan.md (append this stage), then stop.
""",
        execute="""\
We're implementing Stage 2 of the DashBite pipeline.

Inspect the repository and read docs/plan.md first (focus on this stage's section; earlier stages are context). Treat it as the architecture and behavior handoff from the planning agent.

Implement the planned preprocessing stage using the existing project patterns: clean obviously invalid rows, derive hour from timestamp and is_peak for lunch/dinner, write model-ready CSVs under data/features/, keep was_late. Communicate through data/ rather than importing another stage's runtime logic.

Keep the change scoped, add/update the relevant tests, and run them as you work.

When implementation is complete, do not overwrite docs/plan.md or earlier stage sections. Make sure this stage's Manual Smoke Test still matches the actual commands and behavior. If details changed, update only that stage's Manual Smoke Test section so it is runnable.
""",
        test="""\
Review the current Stage 2 implementation as if this were a PR you did not author.

Read docs/plan.md first (this stage's section) to understand the intended behavior, architecture, automated test strategy, and manual smoke test.

Verify the implementation against that contract (invalid rows dropped; hour / is_peak / was_late; outputs under data/features/).

Run the automated tests and inspect whether the documented Manual Smoke Test is still accurate and runnable.

If implementation bugs exist, fix them rather than weakening legitimate tests. Keep this stage's section in docs/plan.md synchronized with reality if commands or outputs changed — never wipe earlier stages.

Finish with a short summary of findings, changes, and suite status.
""",
    ),
    StagePrompts(
        number=3,
        title="Train",
        teach="Model write path: retrain on enough labels, publish checkpoints only.",
        plan=f"""\
Clean labeled features should already be showing up under data/features/. Next is the model's write path.

Inspect the repository and append this stage's implementation plan to docs/plan.md (create the file if missing; never overwrite earlier stages).

Include:
- what we're changing
- relevant files/interfaces
- architectural constraints
- automated test strategy
- a manual smoke test I can run live from the terminal after implementation

Non-negotiables:
- LogisticRegression on distance_km + prep_minutes
- versioned checkpoint under data/models/ (joblib OK) plus a small metrics sidecar
- threshold from TRAIN_EVERY_N_EVENTS
- train only publishes — never import, call, or wait on inference

For the Manual Smoke Test, make the classroom moment “Training published an artifact to disk.” Drive data with `make` targets, run `make train` (use a small TRAIN_EVERY_N_EVENTS if helpful for the demo), then `ls -lh data/models` and show the metrics sidecar. Do not involve inference yet.

{_PLAN_MD_SHAPE}

Do not implement the feature yet. Only update docs/plan.md (append this stage), then stop.
""",
        execute="""\
We're implementing Stage 3 of the DashBite pipeline (training / write path).

Inspect the repository and read docs/plan.md first (focus on this stage's section; earlier stages are context). Treat it as the architecture and behavior handoff from the planning agent — including the Manual Smoke Test.

Implement training: retrain after TRAIN_EVERY_N_EVENTS new labeled examples; publish a versioned checkpoint under data/models/ with a small metrics sidecar; LogisticRegression on distance_km + prep_minutes. Training is only a publisher — must not import, call, or wait on inference.

Keep the change scoped, add/update relevant tests, and run them as you work.

When implementation is complete, do not overwrite docs/plan.md or earlier stage sections. Make sure this stage's Manual Smoke Test still matches the actual commands and behavior. If details changed, update only that stage's Manual Smoke Test section so it is runnable.
""",
        test="""\
Review the current Stage 3 training implementation as if this were a PR you did not author.

Read docs/plan.md first (this stage's section) for intended behavior, architecture, automated tests, and Manual Smoke Test.

Verify retrain trigger, checkpoint + metrics under data/models/, LogisticRegression features, and hard isolation from inference. Strengthen coverage, run the full suite, fix real bugs.

Confirm the documented Manual Smoke Test is still accurate and runnable (artifact-on-disk demo, not inference). Sync this stage's section in docs/plan.md if commands changed — never wipe earlier stages.

Summarize findings, changes, and suite status.
""",
    ),
    StagePrompts(
        number=4,
        title="Infer",
        teach="Model read path: separate consumer of the newest checkpoint on disk.",
        plan=f"""\
Training should already be publishing versioned checkpoints under data/models/, with features under data/features/. I want inference as a completely separate consumer of those artifacts.

Inspect the repository and append this stage's implementation plan to docs/plan.md (create the file if missing; never overwrite earlier stages).

Include:
- what we're changing
- relevant files/interfaces
- architectural constraints
- automated test strategy
- a manual smoke test I can run live from the terminal after implementation

Non-negotiables:
- newest checkpoint on disk; predictions under data/predictions/ with order_id, late_probability, predicted_late, checkpoint_id
- never import training or trigger retraining
- wait cleanly if no checkpoint exists

For the Manual Smoke Test, this is the strongest classroom beat. Prefer separate terminals with `make` targets (`make train`, `make infer`, etc.). Show inference finding a checkpoint, scoring features, and writing predictions (`ls` / `head` under data/predictions/). Design it so the instructor can prove “Training does not need to be running”: create a checkpoint, stop training, keep/start inference, process another batch, show scoring still works from the artifact on disk.

{_PLAN_MD_SHAPE}

Do not implement the feature yet. Only update docs/plan.md (append this stage), then stop.
""",
        execute="""\
We're implementing Stage 4 of the DashBite pipeline (inference / read path).

Inspect the repository and read docs/plan.md first (focus on this stage's section; earlier stages are context). Treat it as the architecture and behavior handoff from the planning agent — including the Manual Smoke Test that proves train/infer isolation.

Build inference as a completely independent consumer: newest checkpoint on disk; score new feature rows; write order_id, late_probability, predicted_late, checkpoint_id under data/predictions/. If training isn't running, keep using the latest checkpoint; if none exists, wait cleanly. Do not import training or trigger retraining.

Keep the change scoped, add/update relevant tests, and run them as you work.

When implementation is complete, do not overwrite docs/plan.md or earlier stage sections. Make sure this stage's Manual Smoke Test still matches the actual commands and behavior. If details changed, update only that stage's Manual Smoke Test section so it is runnable.
""",
        test="""\
Review the current inference stage as if this were a PR you did not author.

Read docs/plan.md first (this stage's section) to understand the intended behavior, architecture, automated test strategy, and manual smoke test — especially the isolation demo.

Verify:
- newest checkpoint selection
- clean behavior when no checkpoint exists
- predictions under data/predictions/ with the expected fields
- inference does not import or trigger training
- inference can operate from an existing checkpoint when training isn't running

Add or improve unit, regression, and integration tests where meaningful. Run the full suite. Fix underlying bugs rather than weakening legitimate tests.

Inspect whether the documented Manual Smoke Test is still accurate and runnable. Keep this stage's section in docs/plan.md synchronized if commands or outputs changed — never wipe earlier stages.

Finish with a short summary of what you checked, anything you changed, and whether the full suite passes.
""",
    ),
    StagePrompts(
        number=5,
        title="ML Dashboard",
        teach="Model Pulse: claim-first charts — volume over time, late-flag rate over time, ranked field failures.",
        plan=f"""\
Features and predictions should already be flowing under data/features/ and data/predictions/. I'd like a lightweight Model Pulse view for someone watching whether the late-prediction system is healthy.

Inspect the repository and append this stage's implementation plan to docs/plan.md (create the file if missing; never overwrite earlier stages).

Include:
- what we're changing
- relevant files/interfaces
- architectural constraints
- automated test strategy
- a manual smoke test I can run live from the terminal after implementation

Non-negotiables:
- pure helpers: sample volume, volume-over-time (timestamp buckets), score summary, and late-flag rate over time (join predictions to feature timestamps via order_id; % predicted_late per minute)
- Model Pulse UI (sparse Streamlit; reads data/ only):
  - ~3 KPIs max (e.g. samples, drop rate, late flag rate) — not a wall of metrics
  - hero chart: orders over time (recent window, e.g. last 60 minutes) with an active title stating the finding
  - model-output chart: step/line of % predicted_late by minute (recent window) with an active title like “flagging more/fewer late” — not a raw score histogram
  - field failures: one horizontal bar chart sorted by count; no duplicate dataframe under it
  - drop redundant throughput multi-series if it only retells drop rate
- no business/ops KPIs in this dashboard (Model Pulse only)

{_DASHBOARD_VIZ}

For the Manual Smoke Test, launch via `make dashboard`. Students should see active chart titles, a moving volume series, a late-flag % series, and ranked field failures. Keep terminal output showing Streamlit is reading pipeline artifacts.

{_PLAN_MD_SHAPE}

Do not implement the feature yet. Only update docs/plan.md (append this stage), then stop.
""",
        execute="""\
We're implementing Stage 5 of the DashBite pipeline (ML / Model Pulse dashboard).

Inspect the repository and read docs/plan.md first (focus on this stage's section; earlier stages are context). Treat it as the architecture and behavior handoff from the planning agent — including the Manual Smoke Test.

Build tested helpers (sample volume, volume-over-time, score summary, late-flag rate over time via order_id→timestamp join) and a claim-first Model Pulse page:
- few KPIs; hero volume-over-time (recent window); % predicted_late over time (step/line); ranked horizontal field-failure bars; no duplicate tables; no ops KPIs
- titles state findings; axes are human-readable; dashboards only read data/

Keep the change scoped, add/update helper tests, and run them as you work.

When implementation is complete, do not overwrite docs/plan.md or earlier stage sections. Make sure this stage's Manual Smoke Test still matches the actual commands and behavior. If details changed, update only that stage's Manual Smoke Test section so it is runnable.
""",
        test="""\
Review the current Stage 5 ML dashboard as if this were a PR you did not author — final dashboard gate for the demo pipeline.

Read docs/plan.md first (this stage's section) for intended behavior, architecture, automated tests, and Manual Smoke Test.

Verify helpers and that Model Pulse meets the viz bar: active titles, recent volume-over-time, late-flag % over time (not a score histogram), ranked failures without a duplicate table, ~3 KPIs, UI only consumes artifacts. Strengthen helper tests, run the full suite, fix real issues.

Confirm the documented Manual Smoke Test (Streamlit launch + what to watch for) is still accurate. Sync this stage's section in docs/plan.md if commands changed — never wipe earlier stages. A short README note on running stages separately is a nice extra if missing.

Finish with a wrap-up of what you verified, what you changed, and whether the full suite passes.
""",
    )
)
WRAP_UP_TITLE = "Wrap-up — Run the full stack"
WRAP_UP_TEACH = (
    "After the stages are built: start every process as a persistent background job via Make."
)
WRAP_UP_PROMPT = """\
We've finished the stage-by-stage DashBite build. Help me run the full application so each stage stays up as a persistent background job.

Inspect the repository (especially the Makefile and pipeline entrypoints). Prefer Makefile orchestration — do not invent ad-hoc one-off shell recipes as the public interface.

I want:
- `make run` starts simulator, preprocess, train, infer, and the dashboard as durable background processes (survive the shell that launched them)
- logs under `.logs/` and PIDs under `.logs/pids/` (or the project's existing convention)
- `make stop` cleanly stops the whole stack
- optional per-stage background targets are fine if they stay Make-friendly (e.g. document `make simulator` in foreground vs the background stack via `make run`)
- default poll cadence is 15 seconds (`POLL_INTERVAL_SECONDS=15`); keep that as the classroom default
- dashboard on :8501 (Model Pulse)

Also append a short section to docs/plan.md (do not overwrite earlier stages) with a Manual Smoke Test for the full stack:
- Terminal: `make run` (and where to watch logs)
- Watch for: new files under data/raw → data/features → data/predictions, and http://localhost:8501 updating
- Stop: `make stop`

Implement/fix whatever is needed so `make run` / `make stop` are reliable, then give me the exact commands to start and stop the demo.
"""
