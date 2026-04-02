VENV := .venv
PYTHON := $(VENV)/bin/python
PYBABEL := $(VENV)/bin/pybabel
PIP := $(VENV)/bin/pip
PIP_SYNC := $(VENV)/bin/pip-sync
PIP_COMPILE := $(VENV)/bin/pip-compile
TOX := $(VENV)/bin/tox
RUFF := $(VENV)/bin/ruff
MYPY := $(VENV)/bin/mypy
PODMAN := /usr/bin/podman

# Frontend paths and commands
FRONTEND_DIR := src/whatsthedamage/view/frontend
NPM := npm
NPM_RUN := $(NPM) run

DOCKER_IMAGE := whatsthedamage
DOCKER_TAG ?= $(shell set -o pipefail; python3 -m setuptools_scm 2>/dev/null | sed 's/\+/_/' || echo "latest")
VERSION ?= $(shell set -o pipefail; python3 -m setuptools_scm 2>/dev/null || echo "v0.0.0")


.PHONY: web test lint lang clean mrproper image compile-deps update-deps compile-deps-secure help docs build frontend

# =============================================================================
# DEVELOPMENT TARGETS
# =============================================================================

# Frontend development
# Unified frontend interface - runs any npm script
# Usage: make frontend ARG=script-name
frontend:
	@if ! command -v $(NPM) >/dev/null 2>&1; then \
		echo "npm is not installed. Please install Node.js and npm first."; \
		exit 1; \
	fi
	cd $(FRONTEND_DIR) && $(NPM_RUN) $(ARG)

# Combined build
build: dev
	$(MAKE) frontend ARG=build

# Ensure build depends on dev being up to date
build: $(VENV)/.deps-synced $(FRONTEND_DIR)/node_modules/.installed

# Create venv and install pip-tools
$(VENV)/pyvenv.cfg:
	python3 -m venv $(VENV) || { echo "Failed to create virtual environment"; exit 1; }
	$(PIP) install --upgrade pip || { echo "Failed to upgrade pip"; exit 1; }
	$(PIP) install pip-tools || { echo "Failed to install pip-tools"; exit 1; }

# Track when dependencies were last synced
$(VENV)/.deps-synced: requirements.txt requirements-dev.txt requirements-web.txt $(VENV)/pyvenv.cfg pyproject.toml
	$(PIP_SYNC) requirements.txt requirements-dev.txt requirements-web.txt || { echo "Failed to sync dependencies"; exit 1; }
	$(PIP) install -e . || { echo "Failed to install package"; exit 1; }
	touch $(VENV)/.deps-synced

# Track when frontend dependencies were last installed
$(FRONTEND_DIR)/node_modules/.installed: $(FRONTEND_DIR)/package.json $(FRONTEND_DIR)/package-lock.json
	@if ! command -v $(NPM) >/dev/null 2>&1; then \
		echo "npm is not installed. Please install Node.js and npm first."; \
		exit 1; \
	fi
	cd $(FRONTEND_DIR) && $(NPM) install
	touch $@

# Set up development environment
dev: $(VENV)/.deps-synced $(FRONTEND_DIR)/node_modules/.installed

# Run Flask development server
web: dev $(FRONTEND_DIR)/node_modules/.installed
	$(MAKE) frontend ARG=build
	FLASK_APP=src.whatsthedamage.app $(PYTHON) -m flask run

# Run tests using tox
test: dev
	$(TOX)
	$(MAKE) frontend ARG=test

# Run linter/formatter
lint: dev
	$(TOX) -e lint
	$(TOX) -e type

lang: dev
	$(PYBABEL) extract -F babel.cfg -o src/whatsthedamage/locale/en/LC_MESSAGES/messages.pot src/whatsthedamage/

# Build Sphinx documentation
docs:
	$(PYTHON) $(VENV)/bin/sphinx-apidoc -f -M -T -o docs/ src/
	SPHINXBUILD=../$(VENV)/bin/sphinx-build $(MAKE) -C docs clean html

# =============================================================================
# PODMAN TARGETS
# =============================================================================

# Build Podman image with version tag
image:
	@echo "Building Podman image with version: $(VERSION)"
	$(PODMAN) build --build-arg VERSION=$(VERSION) --format docker -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

# =============================================================================
# DEPENDENCY MANAGEMENT
# =============================================================================

# Compile all requirements files from pyproject.toml
compile-deps: $(VENV)/pyvenv.cfg
	$(PIP_COMPILE) pyproject.toml
	$(PIP_COMPILE) --extra=dev pyproject.toml -o requirements-dev.txt
	$(PIP_COMPILE) --extra=web pyproject.toml -o requirements-web.txt
	rm -f $(VENV)/.deps-synced

# Update all requirements (allow upgrades)
update-deps: $(VENV)/pyvenv.cfg
	$(PIP_COMPILE) --upgrade pyproject.toml
	$(PIP_COMPILE) --upgrade --extra=dev pyproject.toml -o requirements-dev.txt
	$(PIP_COMPILE) --upgrade --extra=web pyproject.toml -o requirements-web.txt
	rm -f $(VENV)/.deps-synced

# Generate with hashes for security
compile-deps-secure: $(VENV)/pyvenv.cfg
	$(PIP_COMPILE) --generate-hashes pyproject.toml
	$(PIP_COMPILE) --generate-hashes --extra=dev pyproject.toml -o requirements-dev.txt
	$(PIP_COMPILE) --generate-hashes --extra=web pyproject.toml -o requirements-web.txt
	rm -f $(VENV)/.deps-synced

# =============================================================================
# CLEANUP TARGETS
# =============================================================================

# Clean up generated files
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .tox/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .coverage*
	find . -type f -name "*.pyc" -delete
	find . -type d -name __pycache__ -delete
	rm -rf $(FRONTEND_DIR)/../static/dist/

# Deep clean including virtual environment
mrproper: clean
	rm -rf $(VENV)
	rm -rf $(FRONTEND_DIR)/node_modules/

# =============================================================================
# HELP
# =============================================================================

# Help target
help:
	@echo "Development workflow:"
	@echo "  dev            - Create venv, install pip-tools, sync all requirements, install frontend dependencies"
	@echo "  web            - Run Flask development server (requires frontend build)"
	@echo "  test           - Run tests using tox"
	@echo "  lint           - Run linter/formatter on Python code"
	@echo "  image          - Build Podman image with version tag"
	@echo "  lang           - Extract translatable strings to English .pot file"
	@echo "  docs           - Build Sphinx documentation"
	@echo "  frontend ARG=script - Run any npm script (e.g., 'frontend ARG=dev', 'frontend ARG=build')"
	@echo "  build          - Full stack build (Python + JS)"
	@echo ""
	@echo "Dependency management for Python:"
	@echo "  compile-deps   - Compile requirements files from pyproject.toml"
	@echo "  update-deps    - Update requirements to latest versions"
	@echo "  compile-deps-secure - Compile requirements with security hashes"
	@echo ""
	@echo "Cleanup for Python and JavaScript:"
	@echo "  clean          - Clean up build files"
	@echo "  mrproper       - Clean + remove virtual environment, node_modules"
