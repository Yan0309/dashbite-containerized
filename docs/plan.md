# DashBite — living plan

Classroom handoff for Architect → Implementer → Reviewer. Stages are appended below; do not wholesale-overwrite earlier sections.

## Wrap-up — Run the full stack

### Goal
Run simulator, preprocess, train, infer, and Model Pulse as durable background jobs via the Makefile.

### Architecture / boundaries
- Public interface: `make run`, `make status`, `make stop`
- Implementation helper: `scripts/pipeline_bg.sh` (nohup + PID files + log redirection)
- Foreground single stages remain: `make simulator|preprocess|train|infer|dashboard`
- Default poll cadence: `POLL_INTERVAL_SECONDS=15`
- Dashboard: http://localhost:8501 (Model Pulse only)

### Manual Smoke Test

#### What we're proving
The full pipeline stays up in the background, writes through `data/raw` → `data/features` → `data/predictions`, and Model Pulse updates on :8501.

#### Terminal
```bash
make run
make status
# optional live logs:
tail -f .logs/simulator.log .logs/preprocess.log .logs/train.log .logs/infer.log
# or open http://localhost:8501
```

#### Watch for
- `make status` shows UP for simulator, preprocess, train, infer, dashboard
- New files under `data/raw/`, then `data/features/`, then `data/predictions/`
- Model Pulse at http://localhost:8501 (volume / scores / failures)
- Logs under `.logs/`; PIDs under `.logs/pids/`

#### Stop
```bash
make stop
make status   # expect DOWN
```

## Stage 6 — Containerization

### Goal
Package the existing pipeline and Model Pulse as a local Docker Compose stack, without changing pipeline behavior or the host-side pytest workflow.

### Requirements
- Build one shared image from a Compose `build:` context and run five services: simulator, preprocess, train, infer, and dashboard.
- Run exactly one replica of each long-running service. Do not scale infer or any other worker.
- Mount one named volume at `/app/data` for all pipeline services.
- Set runtime environment explicitly: `TRAIN_EVERY_N_EVENTS=50`, `BATCH_SIZE=20`, `POLL_INTERVAL_SECONDS=15.0`, `CORRUPT_BATCH_RATE=0.25`, and `RANDOM_SEED=42`.
- Set `PYTHONUNBUFFERED=1` so `print()` output is visible promptly in Compose logs.
- Set `restart: unless-stopped` on simulator, preprocess, train, infer, and dashboard. Do not apply a restart policy to the test-profile service.
- Run Model Pulse headlessly on `0.0.0.0:8501`, publish host port 8501, and configure a healthcheck using Python's standard library against Streamlit's health endpoint.
- Run services as a non-root user. Ensure that user owns `/app/data` in the image so an initially empty named volume is writable after Docker volume initialization.
- Add a `.dockerignore` for local runtime data, `.venv`, logs, caches, and VCS files. Include the test suite and pytest configuration in the image for the test profile.
- Add a Compose `test` profile with a one-shot service that runs pytest in the image. Keep the host pytest gate; accepting pytest in the image is a deliberate simplicity trade-off.
- Keep the Prompt Board and Kubernetes out of this stack.
- Keep the stack single-replica. Do not include `--scale infer=2` or other multi-replica instructions.

### Proposed changes
- Add a Dockerfile based on the guide's Python slim image, installing `requirements.txt`, copying application and test files, setting the working directory and unbuffered output, and creating a non-root runtime user with ownership of `/app/data`.
- Add a `.dockerignore` that excludes host-generated data and development artifacts without excluding test fixtures.
- Add a Compose file with a shared image/build context, one service per process, the common environment, the named data volume, dashboard port and healthcheck, and restart policies for all long-running services.
- Add the pytest service behind the `test` profile, runnable with `docker compose --profile test run --rm tests`.
- Leave application path resolution and file-publication behavior for Stage 7. This stage deliberately captures the current shutdown behavior before adding signal handling.

### Architecture / boundaries
- Each pipeline service runs its existing module as the container's foreground process; Compose owns process lifecycle and logs. Do not invoke `make run` or `scripts/pipeline_bg.sh` inside containers.
- Simulator, preprocess, train, infer, and dashboard all see the same named volume mounted at `/app/data`; Compose runs one instance of each.
- Compose builds the same image for every service. The test profile reuses that image but runs only when explicitly selected.
- Python runs as a non-root user. The image's `/app/data` ownership is prepared before the named volume is first mounted; an existing volume retains its own ownership.
- No `init: true` is used for the Stage 6 stop baseline: the Python worker is PID 1 so its current SIGTERM behavior can be measured before Stage 7.
- Host `pytest` and the containerized test profile both run the complete suite. Pytest in the runtime image is an accepted trade-off for this teaching project.

### Important files
- `Dockerfile`
- `.dockerignore`
- `compose.yaml` (or the repository's chosen Compose filename)
- `requirements.txt`
- `pytest.ini`
- `tests/` and `tests/fixtures/`
- `pipeline/` stage modules and `pipeline/dashboard/app.py`

### Risks and design concerns
- This stage's baseline intentionally has no worker SIGTERM handler. With Python as container PID 1, `docker compose stop` is expected to wait for the default grace period (about 10 seconds) and then kill train and infer; capture their exit codes before Stage 7.
- Without `PYTHONUNBUFFERED=1`, stdout buffering can make live worker output appear delayed in `docker compose logs -f`.
- A named volume avoids host bind-mount ownership problems, but does not automatically make files writable by a non-root container user. Prepare and verify the mount-point ownership in the image; do not assume `USER` changes volume ownership.
- The workers currently publish whole files directly to their final names. A consumer can observe an incomplete CSV or checkpoint; Stage 7 addresses whole-file outputs. The append-only quality log remains a documented limitation.
- `restart: unless-stopped` restarts a failed worker but does not make shared-file writes atomic or make multi-replica processing safe. Keep every worker at one replica.
- The test profile is opt-in and must not be started as a long-running service.

### Automated tests   (Unit / Regression / Integration)
- Unit: retain all existing unit tests; Stage 6 adds no Python behavior that requires changing their contracts.
- Regression: run the complete existing host suite and preserve all 32 tests. Stage 6 adds no Python behavior, so no new pytest tests are required.
- Integration: `docker compose config -q` must succeed, the shared image must build, and `docker compose --profile test run --rm tests` must pass the full suite inside the image. No pytest tests that parse the Dockerfile/Compose files: they would need PyYAML and would only assert on file text; the build, config validation, and smoke test verify the real behavior.

### Manual Smoke Test

#### What we're proving
The shared image starts all five single-instance services, their logs and shared-volume files are visible, Model Pulse is healthy on port 8501, and the pre-Stage-7 train/infer stop behavior is recorded.

#### Terminal
Terminal 1:
```sh
docker compose down -v
docker compose up --build -d
docker compose logs -f simulator preprocess train infer dashboard
```
Leave the log-following command running long enough to see a trained checkpoint and inference output; press Ctrl+C to stop following logs, not the services.

Terminal 2:
```sh
docker compose ps
docker compose exec -T train python -c "from pathlib import Path; root=Path('/app/data'); print(*(str(p.relative_to(root)) for p in sorted(root.rglob('*')) if p.is_file()), sep='\\n')"
docker compose port dashboard 8501
time docker compose stop train infer
docker inspect "$(docker compose ps -aq train)" --format 'train exit={{.State.ExitCode}}'
docker inspect "$(docker compose ps -aq infer)" --format 'infer exit={{.State.ExitCode}}'
```

#### Watch for
- All five long-running services are up, with one container each; the dashboard port maps to host port 8501.
- Live logs show simulator, preprocess, train, and infer progress without waiting for process exit.
- The shared volume contains files across `raw/`, `features/`, `models/`, `predictions/`, and `quality/`; the dashboard healthcheck reports healthy.
- Record the exact `time docker compose stop train infer` duration and both inspect exit codes as the BEFORE-fix evidence. Expected: approximately 10 seconds and exit code 137 for train and infer.

#### Stop
```sh
docker compose stop simulator preprocess dashboard
docker compose down -v
```

### Definition of done
- A clean checkout can build and start the one-image Compose stack with one named data volume and one replica per long-running service.
- The non-root application can write to the first-mounted volume; dashboard health and live logs are observable.
- The opt-in container test profile runs the complete suite, and the existing 32 host tests remain green.
- The smoke test records the pre-fix stop duration and train/infer exit codes, then removes the stack and volume.

## Stage 7 — Container Readiness

### Goal
Make data location, file handoffs, and worker shutdown reliable in the Compose deployment while preserving the current host defaults and test behavior.

### Requirements
- Support `DATA_ROOT` as the path to the data directory itself. Resolve paths at call time with precedence: explicit `base` argument, then `DATA_ROOT`, then `PROJECT_ROOT/data`.
- Preserve the existing `base` argument contract: it is a project base directory containing `data/`; `DATA_ROOT` is the data directory itself.
- Make the dashboard use the same shared resolver as the pipeline stages.
- Add one atomic-write helper for whole-file outputs: raw batches, feature batches, checkpoints, metrics, train state, and predictions. Write a `.tmp` temporary filename in the destination directory that cannot match a consumer glob, then publish with `os.replace`.
- Keep the append-only quality log unchanged and document that its append is not atomic.
- Add graceful SIGTERM handling to simulator, preprocess, train, and infer using a `threading.Event`. A handler requests shutdown; each loop finishes its current operation and exits without waiting for the full polling interval.
- Keep the single-replica Compose policy. Do not add a multi-worker claim/shard mechanism.

### Proposed changes
- Update the shared path resolver to evaluate the explicit `base`, environment, and default paths in the selected order each time it is called; do not cache `DATA_ROOT` at import time.
- Route dashboard feature, prediction, and quality reads through the same resolver rather than anchoring the dashboard to `PROJECT_ROOT`.
- Add a same-directory atomic publication helper using a temporary name outside the raw, features, checkpoint, metrics, prediction, and other consumer glob patterns, followed by `os.replace`.
- Use atomic publication for all whole-file outputs, including `train_state.json`; leave `batch_quality.csv` as a direct append and document that limitation.
- Add a stop event to each worker loop, handle SIGTERM (and SIGINT for local foreground use), and use the event for interruptible poll waits. Keep signal handlers limited to requesting shutdown.
- Update the container smoke instructions and design notes to distinguish atomic whole-file handoffs from the non-atomic quality-log append.
- Update README.md with Docker/Compose usage and a section that separates what came from the course guide (one image, Compose, DATA_ROOT) from my additions.

### Architecture / boundaries
- `pipeline.paths` remains the single owner of data-root resolution. Explicit `base` retains its current project-root meaning; `DATA_ROOT` is an exact data-directory path.
- Atomic temporary files live beside their final files so `os.replace` stays on the same filesystem. Temporary names must remain invisible to existing `glob()` consumers.
- Each producer publishes complete final files atomically; consumers continue polling the same directories and keep their existing file contracts.
- Each worker owns its loop and stop event. SIGTERM only requests shutdown; the worker exits at a safe loop boundary after its active operation returns.
- The quality CSV remains append-only and is explicitly outside the atomic-write guarantee. The shared named volume remains persistent across `docker compose down` and is removed only with `down -v`.

### Important files
- `pipeline/paths.py`
- `pipeline/config.py`
- `pipeline/simulator.py`
- `pipeline/preprocess.py`
- `pipeline/train.py`
- `pipeline/infer.py`
- `pipeline/dashboard/app.py`
- `tests/unit/`, `tests/regression/`, and `tests/integration/`
- `README.md`
- `compose.yaml`

### Risks and design concerns
- Tests currently pass an explicit project base and expect paths under `base/data`; treating that argument as the data directory itself would break the established test and caller contract. Only `DATA_ROOT` is the exact data directory.
- Reading `DATA_ROOT` at call time is required for monkeypatching and for callers that change the environment after importing the module.
- Temporary files must be in the same directory as their final destination and must not match consumer globs. A process killed before replacement can leave a harmless temporary file, which should not be consumed as pipeline data.
- Atomic replacement is per file, not a transaction across checkpoint, metrics, and state files. Preserve the existing checkpoint naming and inference discovery contract.
- The quality log remains susceptible to partial append/interleaving if a write is interrupted; keep all its writers at one replica and document this limitation.
- Shutdown handling must not do file work inside a signal handler. An event-based wait avoids making SIGTERM responsiveness depend on `POLL_INTERVAL_SECONDS`.
- Keep the Compose test profile and host gate green; do not make the existing host suite depend on a running Docker daemon.

### Automated tests   (Unit / Regression / Integration)
- Unit: add tests that fail on current code for explicit-base-over-environment precedence, `DATA_ROOT` over the default, call-time environment lookup after import, and dashboard use of the common resolver.
- Unit: test atomic publication, including that final paths appear only after replacement and temporary names do not match consumer globs. Exercise raw, feature, checkpoint/metrics/state, and prediction writers; verify the quality-log append remains explicitly outside this helper.
- Regression: retain the existing path, stage, dashboard, and golden-output behavior; run the full existing 32-test suite unchanged and add assertions that the default remains `PROJECT_ROOT/data` when neither override is present.
- Integration: launch each of the four worker modules as a subprocess, send SIGTERM, and assert prompt clean exit (code 0) rather than waiting for the Compose grace timeout. Include a case showing an in-progress whole-file output is never visible under its final glob name before `os.replace`.
- Run both the host pytest gate and `docker compose --profile test run --rm tests`; every new behavior must have an automated test that fails against the current implementation.

### Manual Smoke Test

#### What we're proving
With a fresh named volume, all workers and the dashboard use the configured data directory, complete files appear under their final names, train and infer stop promptly with exit code 0, and the named volume's data survives `docker compose down` followed by `up` without `-v`.

#### Terminal
Terminal 1:
```sh
docker compose down -v
docker compose up --build -d
docker compose logs -f simulator preprocess train infer dashboard
```
Wait until the logs show feature output, a checkpoint, and predictions; press Ctrl+C to stop following logs only.

Terminal 2:
```sh
docker compose ps
docker compose exec -T train python -c "from pathlib import Path; root=Path('/app/data'); print(*(str(p.relative_to(root)) for p in sorted(root.rglob('*')) if p.is_file()), sep='\\n')"
docker compose exec -T train python -c "from pathlib import Path; stale=sorted(Path('/app/data').rglob('*.tmp')); assert not stale, stale; print('no .tmp files anywhere under /app/data')"
docker compose exec -T train python -c "from pathlib import Path; Path('/app/data/.persistence-smoke').write_text('named volume survives down and up')"
time docker compose stop train infer
docker inspect "$(docker compose ps -aq train)" --format 'train exit={{.State.ExitCode}}'
docker inspect "$(docker compose ps -aq infer)" --format 'infer exit={{.State.ExitCode}}'
docker compose down
docker compose up -d
docker compose exec -T train python -c "from pathlib import Path; p=Path('/app/data/.persistence-smoke'); print(p.read_text())"
docker compose exec -T train python -c "from pathlib import Path; root=Path('/app/data'); print(*(str(p.relative_to(root)) for p in sorted(root.rglob('*')) if p.is_file()), sep='\\n')"
docker compose down -v
```

#### Watch for
- The listed runtime files are under `/app/data` in the shared volume, and live service logs show complete pipeline progress.
- The `.tmp` check finds no stale temporary files anywhere under `/app/data` after the pipeline has settled.
- `time docker compose stop train infer` completes promptly, well below the default stop grace period; both workers report exit code 0.
- The `.persistence-smoke` contents and previously generated pipeline files remain after `docker compose down` and `docker compose up -d` without `-v`.
- Final `docker compose down -v` removes the stack and its volume so the next demo begins cleanly.

#### Stop
```sh
docker compose down -v
```

### Definition of done
- Explicit base, call-time `DATA_ROOT`, and default path precedence all behave as specified, including through the dashboard.
- Every whole-file output is atomically published under its existing final naming convention; the quality-log append limitation is documented.
- All four worker loops respond to SIGTERM promptly and exit cleanly after their active operation.
- The repeated stop smoke test records fast shutdown and exit code 0 for train and infer; the named-volume smoke test proves persistence across `down`/`up` without `-v`.
- All newly introduced behavior has automated coverage that fails on the current code, and all 32 existing tests remain green on host and in the Compose test profile.
- README documents what came from the course guide vs. my additions.
