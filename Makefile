# DashBite pipeline — common teaching commands
# Usage: make help

PYTHON      ?= python3
VENV        ?= .venv
BIN         := $(VENV)/bin
PY          := $(BIN)/python
PIP         := $(BIN)/pip
PYTEST      := $(BIN)/pytest
STREAMLIT   := $(BIN)/streamlit

# Demo-friendly defaults (override on the command line)
export TRAIN_EVERY_N_EVENTS    ?= 50
export BATCH_SIZE              ?= 20
export POLL_INTERVAL_SECONDS   ?= 15.0
export CORRUPT_BATCH_RATE      ?= 0.25
export PYTHONPATH              := $(CURDIR)

LOG_DIR := .logs
PIDS    := $(LOG_DIR)/pids

.PHONY: help install test test-unit test-regression test-integration \
	simulator preprocess train infer dashboard prompts prompts-static \
	run stop status clean clean-data

help:
	@echo "DashBite Make targets"
	@echo ""
	@echo "  make install              Create .venv and install requirements"
	@echo "  make test                 Run full pytest suite (unit+regression+integration)"
	@echo "  make test-unit            Run unit tests only"
	@echo "  make test-regression      Run regression tests only"
	@echo "  make test-integration     Run integration tests only"
	@echo "  make simulator            Run order feed (foreground)"
	@echo "  make preprocess           Run preprocess loop (foreground)"
	@echo "  make train                Run training loop (foreground)"
	@echo "  make infer                Run inference loop (foreground)"
	@echo "  make dashboard            Run Streamlit Model Pulse on :8501 (foreground)"
	@echo "  make prompts              Agent Prompt Board on :8502 (Architect→Implementer→Reviewer)"
	@echo "  make prompts-static       Rebuild docs/index.html for GitHub Pages"
	@echo "  make run                  Start all stages in background + dashboard"
	@echo "  make status               Show whether background stages are UP"
	@echo "  make stop                 Stop background pipeline processes"
	@echo "  make clean-data           Remove runtime files under data/ (keep .gitkeep)"
	@echo "  make clean                clean-data + logs + pytest cache"
	@echo ""
	@echo "Env defaults: TRAIN_EVERY_N_EVENTS=$(TRAIN_EVERY_N_EVENTS) BATCH_SIZE=$(BATCH_SIZE) POLL_INTERVAL_SECONDS=$(POLL_INTERVAL_SECONDS)"
	@echo "Foreground = one stage in this terminal. Background stack = make run / make stop."

install: $(VENV)/.installed

$(VENV)/.installed: requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@touch $@

test: install
	$(PYTEST)

test-unit: install
	$(PYTEST) -m unit

test-regression: install
	$(PYTEST) -m regression

test-integration: install
	$(PYTEST) -m integration

simulator: install
	$(PY) -m pipeline.simulator

preprocess: install
	$(PY) -m pipeline.preprocess

train: install
	$(PY) -m pipeline.train

infer: install
	$(PY) -m pipeline.infer

dashboard: install
	PYTHONPATH=$(CURDIR) $(STREAMLIT) run pipeline/dashboard/app.py \
		--server.headless true --server.port 8501

prompts: install
	PYTHONPATH=$(CURDIR) $(STREAMLIT) run pipeline/prompts/app.py \
		--server.headless true --server.port 8502

prompts-static: install
	PYTHONPATH=$(CURDIR) $(PY) -m pipeline.prompts.build_static

run: install stop
	@echo "Starting pipeline (logs in $(LOG_DIR)/, poll=$(POLL_INTERVAL_SECONDS)s)..."
	@LOG_DIR=$(LOG_DIR) PIDS=$(PIDS) PY=$(PY) STREAMLIT=$(STREAMLIT) \
		bash scripts/pipeline_bg.sh start

status:
	@LOG_DIR=$(LOG_DIR) PIDS=$(PIDS) bash scripts/pipeline_bg.sh status

stop:
	@LOG_DIR=$(LOG_DIR) PIDS=$(PIDS) PY=$(PY) STREAMLIT=$(STREAMLIT) \
		bash scripts/pipeline_bg.sh stop

clean-data:
	@rm -f data/raw/*.csv \
		data/features/features_*.csv data/features/.done_* \
		data/models/checkpoint_*.joblib data/models/metrics_*.json data/models/train_state.json \
		data/predictions/predictions_*.csv \
		data/quality/*.csv
	@echo "Runtime data cleared."

clean: clean-data
	@rm -rf $(LOG_DIR) .pytest_cache
	@find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete."
