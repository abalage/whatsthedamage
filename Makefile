VENV := venv
PYTHON := $(VENV)/bin/python
PYBABEL := $(VENV)/bin/pybabel
PIP := $(VENV)/bin/pip
PIP_SYNC := $(VENV)/bin/pip-sync
PIP_COMPILE := $(VENV)/bin/pip-compile
TOX := $(VENV)/bin/tox
RUFF := $(VENV)/bin/ruff
MYPY := $(VENV)/bin/mypy
PODMAN := /usr/bin/podman

DOCKER_IMAGE := whatsthedamage
DOCKER_TAG ?= $(shell set -o pipefail; python3 -m setuptools_scm 2>/dev/null | sed 's/\+/_/' || echo "latest")
VERSION ?= $(shell set -o pipefail; python3 -m setuptools_scm 2>/dev/null || echo "v0.0.0")

.PHONY: docs web test lang clean mrproper image compile-deps update-deps compile-deps-secure help docs

# =============================================================================
# DEVELOPMENT TARGETS
# =============================================================================

# Create venv and install pip-tools
$(VENV)/pyvenv.cfg:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip==25.2
	$(PIP) install pip-tools==7.2.0

# Track when dependencies were last synced
$(VENV)/.deps-synced: requirements.txt requirements-dev.txt requirements-web.txt $(VENV)/pyvenv.cfg pyproject.toml
	$(PIP_SYNC) requirements.txt requirements-dev.txt requirements-web.txt
	$(PIP) install -e .
	touch $(VENV)/.deps-synced

# Set up development environment
dev: $(VENV)/.deps-synced

# Run Flask development server
web: dev
	export FLASK_APP=src.whatsthedamage.app && $(PYTHON) -m flask run

# Run tests using tox
test: dev
	$(TOX)

# Run ruff linter/formatter
ruff: dev
	$(RUFF) check .

# Run mypy type checker
mypy: dev
	$(MYPY) src/

lang: dev
	$(PYBABEL) extract -F babel.cfg -o src/whatsthedamage/locale/en/LC_MESSAGES/messages.pot src/whatsthedamage/

# Build Sphinx documentation
docs:
	$(PYTHON) $(VENV)/bin/sphinx-apidoc -f -M -T -o docs/ src/
	export SPHINXBUILD=../$(VENV)/bin/sphinx-build && $(MAKE) -C docs clean html

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

# Deep clean including virtual environment
mrproper: clean
	rm -rf $(VENV)

# =============================================================================
# HELP
# =============================================================================

# Help target
help:
	@echo "Development workflow:"
	@echo "  dev            - Create venv, install pip-tools, sync all requirements"
	@echo "  web            - Run Flask development server"
	@echo "  test           - Run tests using tox"
	@echo "  ruff           - Run ruff linter/formatter"
	@echo "  mypy           - Run mypy type checker"
	@echo "  image          - Build Podman image with version tag"
	@echo "  lang           - Extract translatable strings to English .pot file"
	@echo "  docs           - Build Sphinx documentation"
	@echo ""
	@echo "Dependency management:"
	@echo "  compile-deps   - Compile requirements files from pyproject.toml"
	@echo "  update-deps    - Update requirements to latest versions"
	@echo "  compile-deps-secure - Generate requirements with hashes"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean          - Clean up build files"
	@echo "  mrproper       - Clean + remove virtual environment"