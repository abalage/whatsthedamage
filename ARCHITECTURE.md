# whatsthedamage Architecture Overview

## Purpose
`whatsthedamage` is an open-source Python tool for processing bank transaction CSV exports. It provides both a command-line interface (CLI) and a Flask-based web interface for categorizing, filtering, and summarizing transactions. The project supports customizable CSV formats, localization, and experimental machine learning-based categorization.

## High-Level Structure
The project follows a Model-View-Controller (MVC) and Service Layer patterns for clear separation of concerns:

- **Models**: Data representation, row processing, enrichment, filtering, summarization, and ML logic.
- **Views**: Output formatting for console, HTML, and CSV.
- **Controllers**: CLI and web routing, orchestration of processing.
- **Config**: Centralized configuration, context, and pattern sets.
- **Scripts**: ML model training, feature engineering, documentation.
- **Services**: Place for business logic.

### Architecture decisions
- Dependencies point inward (Controller → Service → Model), never outward.
- Single Responsibility Principle.

## Major Components

### 1. Models (`src/whatsthedamage/models/`)
- **CsvRow**: Represents a single transaction row.
- **RowsProcessor**: Orchestrates filtering, enrichment (regex/ML), categorization, and summarization.
- **RowEnrichment / RowEnrichmentML**: Categorization via regex or ML.
- **RowFilter**: Filters rows by date/month.
- **RowSummarizer**: Aggregates values by category.
- **CsvFileHandler / CsvProcessor**: Reads and parses CSV files, manages row objects.

### 2. Controllers (`src/whatsthedamage/controllers/`)
- **CLI Controller**: Entry point for command-line usage (`__main__.py`, `cli_app.py`).
- **Web Controller**: Flask routes for file upload, processing, and result rendering (`app.py`, `routes.py`).
- **API Controllers**: REST API endpoints in `api/v1/` and `api/v2/` directories.
- **Orchestration**: Main logic (`whatsthedamage.py`) coordinates config loading, processing, and output.

### 3. Views (`src/whatsthedamage/view/`)
- **row_printer.py**: Console output formatting.
- **templates/**: Jinja2 templates for HTML output (server-side rendered web interface).
- **data_frame_formatter.py**: CSV/HTML table formatting.
- **Interactive elements**: JavaScript enhancements (fetch API, DataTables) for improved UX without full page reloads.

### 4. Config (`src/whatsthedamage/config/`)
- **config.py**: Central config, context, and pattern sets.
- **flask_config.py**: Web-specific config.
- **enricher_pattern_sets/**: Regex patterns for enrichment.

### 5. Scripts (`src/whatsthedamage/scripts/`)
- **ML Training**: Scripts for training, evaluating, and tuning ML models.
- **Documentation**: Sphinx docs and ML model details.

### 6. Services (`src/whatsthedamage/services/`)
- **ProcessingService**: Core business logic shared between web routes, CLI, and REST API.
- Ensures consistent behavior across all interfaces.
- Decouples processing logic from presentation/delivery layer.

### 7. API Layer (`src/whatsthedamage/api/`)
- **REST API** (`/api/v1/`, `/api/v2/`): Provides programmatic access to transaction processing.
- Uses Flask Blueprints for versioning (`v1_bp`, `v2_bp`).
- Returns JSON responses for automation, scripting, and potential mobile apps.
- Shares the same `ProcessingService` as web routes and CLI for consistency.
- **API Versioning Strategy**:
  - HTTP clients choose endpoint version via URL (`/api/v1/` vs `/api/v2/`).
  - CLI users choose package version via installation.
  - Explicit HTTP API versions in the URL for any breaking wire-level change.
  - Route handlers for unchanged endpoints can call shared functions.
- **Documentation**: API documentation available via `/docs` endpoint.

## Data Flow
1. **Input**: User uploads or specifies a CSV file (and optional config).
2. **Parsing**: `CsvFileHandler` reads and parses the CSV into `CsvRow` objects.
3. **Processing**: `RowsProcessor` filters, enriches, categorizes, and summarizes rows.
   - Enrichment uses either regex patterns or ML model (if enabled).
   - Filtering by date/month, optional category filter.
4. **Aggregation**: `RowSummarizer` computes totals per category/time period.
5. **Formatting**: `DataFormattingService` prepares output for console, HTML, CSV, or JSON.
6. **Output**: Results are displayed in CLI or rendered in the web frontend (HTML table, CSV download) or returned as JSON (API).

## Frontend Architecture: Hybrid Approach

The application uses a **hybrid server-side + progressive enhancement** architecture, combining the simplicity of server-side rendering with selective client-side interactivity.

### Web Interface (`/process`, `/clear`, `/download`)
- **Server-Side Rendering**: Flask renders HTML templates with Jinja2.
- **Form Submission**: Traditional POST requests for file uploads and processing.
- **Full Page Reloads**: Primary navigation pattern for simplicity and reliability.
- **Session Management**: Flask sessions handle user state between requests.

### Interactive Enhancements
- **JavaScript Fetch API**: Used for actions that don't require page reloads:
  - Form clearing (`/clear` endpoint)
  - File downloads (`/download` endpoint)
- **DataTables Integration**: Client-side table enhancement for transaction results:
  - Sorting, searching, pagination without server round-trips
  - Fixed headers for better UX with large datasets
  - Operates on server-rendered HTML tables
- **Progressive Enhancement**: Core functionality works without JavaScript; JS adds convenience.

### REST API (`/api/v1/`, `/api/v2/`)
- **Purpose**: Programmatic access for automation, scripting, and potential mobile apps.
- **Separation**: API routes are separate from web routes but share the same service layer.
- **JSON Responses**: All API endpoints return structured JSON.
- **Use Cases**:
  - CI/CD pipelines for automated transaction analysis
  - Third-party integrations
  - Future mobile applications
  - Batch processing scripts

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
- `README.md`: Project overview, CLI usage, API documentation, config, categories.
- `src/whatsthedamage/scripts/README.md`: ML details.
- `Makefile`: Workflow automation.
- `config/config.py`: Central config/context.
- `src/whatsthedamage/app.py`: Flask entrypoint.
- `src/whatsthedamage/view/templates/`: Web frontend templates.
- `src/whatsthedamage/api/`: REST API endpoints (v1, v2) and OpenAPI documentation.
- `src/whatsthedamage/services/`: Shared business logic layer.

---
For further details, see `README.md` (includes comprehensive API documentation), and `src/whatsthedamage/scripts/README.md`.
