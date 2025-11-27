# whatsthedamage Architecture Overview

## Purpose
`whatsthedamage` is an open-source Python tool for processing bank transaction CSV exports. It provides both a command-line interface (CLI) and a Flask-based web interface for categorizing, filtering, and summarizing transactions. The project supports customizable CSV formats, localization, and experimental machine learning-based categorization.

## High-Level Structure
The project follows a Model-View-Controller (MVC) pattern for clear separation of concerns:

- **Models**: Data representation, row processing, enrichment, filtering, summarization, and ML logic.
- **Views**: Output formatting for console, HTML, and CSV.
- **Controllers**: CLI and web routing, orchestration of processing.
- **Config**: Centralized configuration, context, and pattern sets.
- **Scripts**: ML model training, feature engineering, documentation.

## Major Components

### 1. Models (`src/whatsthedamage/models/`)
- **CsvRow**: Represents a single transaction row.
- **RowsProcessor**: Orchestrates filtering, enrichment (regex/ML), categorization, and summarization.
- **RowEnrichment / RowEnrichmentML**: Categorization via regex or ML.
- **RowFilter**: Filters rows by date/month.
- **RowSummarizer**: Aggregates values by category.
- **CsvFileHandler / CsvProcessor**: Reads and parses CSV files, manages row objects.
- **DataFrameFormatter**: Formats aggregated data for output.

### 2. Controllers (`src/whatsthedamage/controllers/`)
- **CLI Controller**: Entry point for command-line usage (`__main__.py`, `cli_app.py`).
- **Web Controller**: Flask routes for file upload, processing, and result rendering (`app.py`, `routes.py`).
- **Orchestration**: Main logic (`whatsthedamage.py`) coordinates config loading, processing, and output.

### 3. Views (`src/whatsthedamage/view/`)
- **row_printer.py**: Console output formatting.
- **templates/**: Jinja2 templates for HTML output (web frontend).
- **data_frame_formatter.py**: CSV/HTML table formatting.

### 4. Config (`src/whatsthedamage/config/`)
- **config.py**: Central config, context, and pattern sets.
- **flask_config.py**: Web-specific config.
- **enricher_pattern_sets/**: Regex patterns for enrichment.

### 5. Scripts (`src/whatsthedamage/scripts/`)
- **ML Training**: Scripts for training, evaluating, and tuning ML models.
- **Documentation**: Sphinx docs and ML model details.

### 6. API development
- Keep core business logic in a separate, unversioned Python package (or set of modules) and have both the CLI and Flask layer call into that core.
- HTTP clients choose endpoint version, CLI users choose package version.
- One project version (semantic) for the distribution as a whole.
- Explicit HTTP API versions in the URL for any breaking wire-level change.
- The CLI is tied to the project version and evolves with it.
- Uses Flask Blueprints for each API version. 
- The route handlers for unchanged endpoints call the shared functions.

## Data Flow
1. **Input**: User uploads or specifies a CSV file (and optional config).
2. **Parsing**: `CsvFileHandler` reads and parses the CSV into `CsvRow` objects.
3. **Processing**: `RowsProcessor` filters, enriches, categorizes, and summarizes rows.
   - Enrichment uses either regex patterns or ML model (if enabled).
   - Filtering by date/month, optional category filter.
4. **Aggregation**: `RowSummarizer` computes totals per category/time period.
5. **Formatting**: `DataFrameFormatter` prepares output for console, HTML, or CSV.
6. **Output**: Results are displayed in CLI or rendered in the web frontend (HTML table, CSV download).

## Machine Learning Integration
- ML model (Random Forest) is trained on historical transaction data.
- Feature engineering uses TF-IDF for text, one-hot encoding for currency, and scaling for amounts.
- Model is loaded via joblib (security warning: only use trusted models).
- ML categorization is enabled via CLI/web flag (`--ml`).

## Localization
- Uses Python `gettext` for translation.
- Locale folders: `src/whatsthedamage/locale/en/`, `src/whatsthedamage/locale/hu/`.
- Translatable strings extracted via `make lang`.

## Configuration
- YAML config file defines CSV format, attribute mapping, enrichment patterns, and categories.
- Centralized in `config/config.py` and loaded at startup.

## Extensibility
- **Add Category**: Update config pattern sets and enrichment logic.
- **Support New CSV Format**: Adjust config and parsing logic in models.
- **ML Model**: Train/test via scripts; see `src/whatsthedamage/scripts/README.md`.

## Security & Conventions
- Never log sensitive data (account numbers, personal info).
- Always validate user and file input.
- Close file handles promptly.
- Do not expose internal errors to end users.
- Known issue: joblib model loading can execute arbitrary code.

## Key Files & Directories
- `README.md`: Project overview, CLI usage, config, categories.
- `src/whatsthedamage/scripts/README.md`: ML details.
- `Makefile`: Workflow automation.
- `config/config.py`: Central config/context.
- `src/whatsthedamage/app.py`: Flask entrypoint.
- `src/whatsthedamage/view/templates/`: Web frontend templates.

---
For further details, see `README.md`, `AGENTS.md`, and `src/whatsthedamage/scripts/README.md`.
