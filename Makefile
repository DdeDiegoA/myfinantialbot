VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn

.PHONY: install ingest serve up

# Source install: creates/reuses .venv so every command below runs against
# one consistent interpreter -- prior bare `pip install` runs landed deps
# split across the pyenv global env and .venv, breaking `python rag.py`/
# `uvicorn serve:app` depending on which shell happened to be active.
install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

ingest:
	$(PYTHON) ingest.py

# One command: rebuild the index, then bring the endpoint up.
up: ingest
	$(UVICORN) serve:app --host 0.0.0.0 --port 8000
