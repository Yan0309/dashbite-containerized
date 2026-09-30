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
