# DashBite — Containerized (IDS706 Final, Repository B)

Teaching demo of a modular data + ML application. **DashBite** predicts whether a food-delivery order will be **late**.

Stages are separate Python modules that share folders under `data/`. Run them locally with the Makefile or together as a Docker Compose stack. Training and inference are **independent processes** coupled only by timestamped checkpoints in `data/models/`. Inference always uses the **newest** checkpoint.

## About this repository (IDS706 Final — Repository B, Option 1)

**Option 1: Extend and Containerize DashBite.** The goal is to run the course's DashBite late-order prediction pipeline as a reproducible Docker Compose stack and make it behave correctly inside containers: a configurable data location, no half-written handoff files, and clean shutdown. The base code is the course demo `Kedar-V/TestingAndContainerisationDemo`, imported unchanged in the first commit; everything after that commit is my work through the AI workflow below. The agreed plan is in [`docs/plan.md`](docs/plan.md) (Stages 6–7), and the three role transcripts are in [`docs/transcripts/`](docs/transcripts/).

### Quick start

```bash
docker compose up --build -d                    # 5 services + shared named volume
open http://localhost:8501                      # Model Pulse dashboard
docker compose --profile test run --rm tests    # full test suite inside the image
docker compose down                             # stop (add -v to delete the data volume)
```

Local tests: `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pytest` (47 tests).

### AI-assisted workflow (GitHub Copilot, three fresh chats)

- **Architect.** Inspected the repository and the course guide before planning. It found gaps I had missed: the guide's Compose file had no `build:` section, `restart` was set only on the simulator, and every whole-file output was written non-atomically, not only checkpoints. I answered its five design questions (Compose only, dashboard only, named volume, host and container tests, and the `DATA_ROOT` meaning and precedence). I then asked it about three topics it had not covered (log buffering, PID 1 and SIGTERM, volume ownership for a non-root user with a healthcheck that doesn't need curl), and finally edited `docs/plan.md` myself.
- **Builder.** Implemented Stage 6, then Stage 7, from the plan. For Stage 7 it wrote tests that failed on the old code first, and it mutation-tested the atomic-write helper. The test count went from 32 to 47, passing both on the host and in the container.
- **Tester.** Compared the implementation with the plan, ran edge cases and the full stack, and reviewed shutdown for all five services. It found the dashboard exiting with 137 and unbounded disk growth, and first gave a verdict of FAIL. The final verdict, after my decisions and fixes, was PASS WITH RISKS.

### Recommendations I accepted

- **Architect:** add a Compose `build:` context and `restart: unless-stopped` on every long-running service. Both were gaps in the course guide.
- **Architect, reviewing my plan edits:** the README update was required but missing from the proposed changes, and the `.tmp` smoke check covered only `models/`. I fixed both.
- **Tester:** the dashboard exited with 137 on stop (fixed with my own approach, below), and the unbounded disk growth (documented as a known limitation).

### Recommendations I changed or rejected

- **Rejected** the course guide's Kubernetes section and `--scale infer=2`. Without a claim or shard mechanism, two infer replicas would score the same orders twice.
- **Removed** the planned pytest tests that parse the Dockerfile and Compose file. They would need PyYAML and only assert on file text; `docker compose config -q`, the image build, the test profile, and the smoke test verify real behavior.
- **Overturned the Builder's conclusion** that `PYTHONPATH` wasn't needed. It relied on the healthcheck and clean startup logs. I opened the page in a browser and got `ModuleNotFoundError`, because the health endpoint only proves the Streamlit server is up. Fixed with `PYTHONPATH=/app`.
- **Rejected the Tester's fix** for the dashboard (a shell `trap` followed by `exec`). `exec` replaces the shell, so the trap is lost. I used `stop_signal: SIGINT` instead, which is Streamlit's normal shutdown path.
- **Rejected** renaming checkpoints to avoid same-second collisions (the Tester's probe passed identical stamps; the real loop retrains at most once per poll, and infer and the dashboard depend on the naming contract), and changing how an empty `DATA_ROOT` is handled. Both are documented instead.
- **Disagreed with the Tester's FAIL verdict.** Its full-stack test stopped the stack immediately after `up`. My controlled experiment showed that stopping after warm-up exits 0 for all five services, while stopping within the first seconds hits a startup race (the signal handlers are installed after the heavy imports), which is harmless because nothing is written yet.
- **Changed** the Builder's fix for a pytest cache warning: I chose `-p no:cacheprovider` rather than making `/app` writable for the non-root user.

### How I verified the result myself

- **Checked the Stage 6 files against the resolved Compose config** with a checklist script (49/50). The one failed check, the missing `PYTHONPATH`, led to the browser test that found the import error.
- **Measured shutdown myself.** The default stop timeout in my environment was about 3 s, not the 10 s I had assumed. A controlled run with `-t 10` took 10.2 s with exit code 137, so I used `-t 10` for a fair before/after comparison: 10.2 s and 137 before the fix, 0.4 s and 0 after.
- **Ran a warm vs. immediate stop experiment** that explained the Tester's contradictory result.
- **Reviewed the diffs of the existing tests** the Builder touched: only an import line was removed, and no assertions were removed.
- **Ran a fresh-clone smoke test** in `/tmp`: 47 tests passed, the full stack ran, data flowed through the volume, no `.tmp` files were left over, and the data persisted across `down` and `up` (see the Manual Smoke Test section below).

I also used Claude (Anthropic) outside the three Copilot roles, as a study guide for drafting my prompts and review checklists. All decisions, experiments, and verification above are my own.


## Stages

| Stage | Module | What it does |
|-------|--------|----------------|
| 0 | `pipeline.config`, `pipeline.paths` | Shared config + data folders |
| 1 | `pipeline.simulator` | Writes timed CSV batches to `data/raw/` (“new orders arrived”) |
| 2 | `pipeline.preprocess` | Drops bad rows, adds `hour` / `is_peak` → `data/features/` |
| 3 | `pipeline.train` | Retrains when ≥ `TRAIN_EVERY_N_EVENTS` new labeled rows; writes checkpoints |
| 4 | `pipeline.infer` | Scores unscored rows with newest checkpoint → `data/predictions/` |
| 5 | `pipeline.dashboard` | Streamlit: **Model Pulse** |

## Setup

```bash
make install
```

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Makefile shortcuts

```bash
make help          # list targets
make test          # full pytest gate
make run           # start all stages in background + dashboard
make stop          # stop background pipeline
make clean-data    # wipe runtime CSVs/checkpoints under data/
```

Foreground single stages: `make simulator`, `make preprocess`, `make train`, `make infer`, `make dashboard`.

Agent demo prompts (independent Architect / Implementer / Reviewer chats): `make prompts` → http://localhost:8502

GitHub Pages (static copy of the board): https://kedar-v.github.io/TestingAndContainerisationDemo/  
Rebuild after editing prompts: `make prompts-static`

## Testing gate (required after every stage)

After each stage you implement or change, run the **full** suite:

```bash
pytest
```

That runs **unit**, **regression**, and **integration** tests together so new work cannot break older stages.

```bash
pytest -m unit
pytest -m regression
pytest -m integration
```

Layout:

```
tests/
  unit/
  regression/
  integration/
  fixtures/
```

## Run the pipeline (background stack)

Classroom default — durable background jobs:

```bash
make run                 # simulator + preprocess + train + infer + Model Pulse
make status              # confirm each stage is UP
open http://localhost:8501
make stop
```

Logs: `.logs/*.log` · PIDs: `.logs/pids/` · Poll default: `POLL_INTERVAL_SECONDS=15`

Foreground single stages (one terminal each): `make simulator`, `make preprocess`, `make train`, `make infer`, `make dashboard`.

## Docker Compose

Start the single-replica pipeline and Model Pulse dashboard:

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f simulator preprocess train infer dashboard
```

Open http://localhost:8501 for Model Pulse. The services share a named volume mounted at `/app/data`; its files survive `docker compose down`. Remove the volume explicitly with `docker compose down -v`.

Run the complete suite in the shared image with the opt-in test profile:

```bash
docker compose --profile test run --rm tests
```

`DATA_ROOT` identifies the data directory itself. Compose sets it to `/app/data`; local runs default to the repository's `data/` directory. An explicit `base` argument to the Python path helpers retains its project-directory meaning and takes precedence over `DATA_ROOT`. An empty `DATA_ROOT` value is treated as unset, which is safer than resolving to an empty path; relative values are interpreted relative to the process working directory.

Whole-file outputs are written to a same-directory `.tmp` file and published with `os.replace`. If a worker is SIGKILLed mid-write, a `<name>.tmp` file may remain; consumers do not glob these files, and a later write to the same destination overwrites it. The append-only `data/quality/batch_quality.csv` log is deliberately unchanged; appending to it is not atomic.

### Known limitations
- The pipeline keeps raw, feature, prediction, checkpoint, and quality files on disk indefinitely. There is no retention policy or cleanup step, so long-running deployments will consume more disk over time.
- The checkpoint naming convention preserves the existing project contract: the filename includes a timestamp in the second field, and infer and the dashboard depend on that naming pattern. Multiple retrains within the same second are intentionally left as a documented limitation rather than a behavior change.
- Startup race: if `docker compose stop` is issued during the first seconds after container start, `train` and `infer` can still be SIGKILLed (exit 137) because their `SIGTERM` handlers are installed only after large imports (`sklearn`, `joblib`). No pipeline files are written during import, so there is no data-corruption risk. The dashboard exits via `SIGINT` and reports `130` if interrupted during startup; once warm, it exits `0` on `SIGINT` shutdown.

### Stop behavior
Warm stop after startup settles: `docker compose stop -t 10` exits in about 1–4 s total (1.4 s and 4.1 s in two runs; the dashboard accounts for most of the variation) with all five containers exiting `0`.

Startup race: if shutdown happens within the first few seconds after `docker compose up`, `train` and `infer` can still be SIGKILLed (exit 137) because their handlers are attached only after the expensive import phase. No writes occur before the handlers are installed, so this is harmless from a data-integrity standpoint. The dashboard exits via `SIGINT`; once warm it exits `0`, and during startup an interrupt can appear as exit `130` (`128 + 2`).

## Manual Smoke Test

Run by me on 2026-09-30 from a fresh clone (`/tmp/smoke`), Docker Compose v5.4.0, macOS.

| Check | Result |
|---|---|
| Fresh clone → `pip install -r requirements.txt` → `pytest` | ✅ 47 passed |
| `docker compose up --build -d` | ✅ 5 services up, dashboard healthy |
| Files flow through the shared volume | ✅ raw → features → models → predictions + quality log |
| No leftover atomic-write temp files after 13 min | ✅ no `.tmp` anywhere under `/app/data` |
| Dashboard in browser | ✅ Model Pulse renders with live data (1,116 samples scored) |
| Stop behavior (see below) | ✅ fixed |
| Data persists across `down` / `up` (no `-v`) | ✅ marker file and 18 checkpoints survived |

**Before vs after graceful shutdown** (`time docker compose stop -t 10 train infer`):

| | Stage 6 (before) | Stage 7 (after) |
|---|---|---|
| Time | 10.2 s | 0.4 s |
| Exit codes | 137 / 137 (SIGKILL) | 0 / 0 |
| Log | none | `... shutting down` |

Note: with Compose's default timeout my environment killed the workers after ~3 s, not the 10 s I had assumed, so I used an explicit `-t 10` for a fair before/after comparison.

<img src="docs/images/b_stop_before.png" width="650" alt="Stop before fix: exit 137">

<img src="docs/images/b_stop_after.png" width="650" alt="Stop after fix: exit 0 and shutdown log lines">

<img src="docs/images/b_persistence.png" width="650" alt="Named volume survives down and up">

<img src="docs/images/b_smoke_dashboard.png" width="550" alt="Model Pulse with live data">

**Problem found during testing: dashboard import error**

The dashboard container reported *healthy*, but opening the page failed with `ModuleNotFoundError: No module named 'pipeline'`. Streamlit's health endpoint only proves the server is up; the app script runs when a browser session connects, so the healthcheck could not catch it. Fixed by setting `PYTHONPATH=/app` in the Dockerfile, then verified in the browser.

<img src="docs/images/b_dashboard_import_error.png" width="500" alt="ModuleNotFoundError before the fix">

<img src="docs/images/b_dashboard_fixed.png" width="500" alt="Dashboard renders after the fix">

## Containerization Sources

**From the course guide** (`docs/docker-k8s-guide.md`): one shared image with a different command per service, one Compose service per stage, a shared named volume, the `DATA_ROOT` concept, explicit demo environment values, and keeping the workers single-replica.

**My additions and corrections:**
- A Compose `build:` context — the guide's Compose file referenced an image it never built.
- `restart: unless-stopped` on every long-running service (the guide had it only on the simulator).
- `PYTHONUNBUFFERED=1`, so `print()` logs appear live in `docker compose logs`.
- `PYTHONPATH=/app` — without it the dashboard crashed with `ModuleNotFoundError` in the browser while still reporting *healthy*.
- A non-root user that owns `/app/data`, so a fresh named volume is writable.
- A Python-stdlib healthcheck for the dashboard (no `curl` in the slim image), documented as checking server availability only.
- An opt-in Compose `test` profile that runs the full suite in the image.
- `DATA_ROOT` actually implemented (the guide described it, but the code ignored it), with precedence: explicit `base` > `DATA_ROOT` > `PROJECT_ROOT/data`.
- Atomic `.tmp` + `os.replace` publication for whole-file outputs; the append-only quality log stays a documented limitation.
- Event-based SIGTERM/SIGINT shutdown for the four workers (exit 137 → 0).

Out of scope by my decision: Kubernetes, the Prompt Board, and `--scale infer=2` (multiple infer replicas would double-score orders without a claim mechanism).

## Config (environment)

| Variable | Default | Meaning |
|----------|---------|---------|
| `TRAIN_EVERY_N_EVENTS` | `2000` | Retrain after this many **new** labeled rows |
| `BATCH_SIZE` | `50` | Orders per simulator tick |
| `POLL_INTERVAL_SECONDS` | `15.0` | Sleep between polls/ticks |
| `RANDOM_SEED` | `42` | Training seed |
| `CORRUPT_BATCH_RATE` | `0.25` | Fraction of batches that include NaNs / bad types |

Preprocess logs per-batch **throughput** and **field-level failures** to `data/quality/batch_quality.csv`. Model Pulse shows these live.

## Design notes for class

- Intake uses **batch CSV files** under the hood; logs say “new orders arrived”.
- Train **only writes** `data/models/checkpoint_*.joblib`.
- Infer **only reads** that folder and never imports train.
- Dashboards read `data/features/` and `data/predictions/` — test the metric helpers with `pytest`, not the browser UI.
