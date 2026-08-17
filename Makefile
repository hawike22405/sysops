VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
BIN := $(HOME)/.local/bin

.PHONY: venv install run test

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install .
	mkdir -p $(BIN)
	ln -sf $(CURDIR)/$(VENV)/bin/sysops $(BIN)/sysops

run: install
	$(BIN)/sysops

test: install
	$(PY) -m pytest -q
