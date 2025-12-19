# Copilot Instructions for whatsthedamage

This guide enables AI coding agents to be immediately productive in the `whatsthedamage` codebase.

## Architecture Overview
- **Purpose:** Processes bank transaction CSV exports, categorizes, filters, and summarizes them. Offers three interfaces: CLI, Flask-based web interface, and REST API (v1 & v2). Includes experimental ML-based categorization.
- **Pattern:** Model-View-Controller (MVC) with Service Layer for business logic separation (v0.8.0+).
- **Key Components:**
  - `src/whatsthedamage/services/`: Business logic services (ProcessingService, ValidationService, ConfigurationService, etc.) - introduced in v0.8.0.
  - `src/whatsthedamage/models/`: Data models (`CsvRow`), row processing (`RowsProcessor`, `CSVProcessor`), ML, enrichment, filtering, summarizing, calculators.
  - `src/whatsthedamage/controllers/`: CLI controller (`CLIController`, `cli_app.py`) and web routing (`routes.py`, `routes_helpers.py`).
  - `src/whatsthedamage/api/`: REST API endpoints (`v1/`, `v2/`), helpers, error handlers, OpenAPI docs.
  - `src/whatsthedamage/view/`: Output formatting (console, HTML, CSV), templates, forms.
  - `src/whatsthedamage/config/`: App context, config loading, pattern sets, data models.
  - `src/whatsthedamage/scripts/`: ML model training, feature engineering, documentation.

## Developer Workflows
- **Build & Run:**
  - CLI: `python -m whatsthedamage <file.csv>` or `make dev` then run from venv
  - Web: `make web` (Flask development server) or use gunicorn in production
  - API: Available at `/api/v1/process` and `/api/v2/process` endpoints, docs at `/docs`
  - Use `Makefile` for common tasks (`make help` for targets)
- **Testing:** 
  - All tests in `tests/` (pytest compatible). Run with `pytest` or `make test`.
  - Unit tests for services, API endpoints, and core logic.
  - Always write tests for new features/bug fixes.
- **Code Quality (v0.8.0+):**
  - `make ruff` - Lint with ruff
  - `make mypy` - Type checking with mypy
  - `make docs` - Build Sphinx documentation
- **ML Model:** Train/test via scripts in `src/whatsthedamage/scripts/`. Uses scikit-learn, joblib for persistence. See `scripts/README.md` for feature engineering and hyperparameter tuning.

## Project-Specific Patterns
- **Service Layer (v0.8.0+):** Business logic isolated in services. Controllers depend on services via dependency injection. Services include: ProcessingService, ValidationService, ConfigurationService, SessionService, FileUploadService, ResponseBuilderService, DataFormattingService.
- **Config/Context:** Centralized in `AppContext` (`config/config.py`). Pattern sets for enrichment in `config/enricher_pattern_sets`.
- **Row Processing:** `CSVProcessor` orchestrates overall flow. `RowsProcessor` handles filtering, enrichment (ML or regex), categorization, and summarization. ML and regex enrichment are interchangeable via flags/context.
- **Calculator Pattern (v0.8.0+):** `DataTablesResponseBuilder` accepts calculator functions (e.g., `create_balance_rows`, `create_total_spendings`) for extensible transaction calculations. See `docs/calculator_pattern_example.py`.
- **API Versioning:** v1 (summary totals), v2 (detailed transactions). Blueprints for each version. Shared `ProcessingService` for consistency.
- **Localization:** Locale folders under `src/whatsthedamage/locale/`. English and Hungarian supported. Uses Python `gettext`.
- **Output:** Console, HTML, CSV, and JSON reports. Output formatting centralized in `DataFormattingService`.
- **Integration:** External libraries: scikit-learn (ML), Flask (web), joblib (model persistence). CSV format customizable via config.

### Example: Config Pattern
```yaml
csv:
  delimiter: ","
  attribute_mapping:
    date: "Transaction Date"
    amount: "Amount"
    currency: "Currency"
enricher_pattern_sets:
  partner:
    grocery: ["TESCO", "ALDI", "LIDL"]
```

### Example: Row Processing Flow (v0.8.0+)
1. Controller receives request (CLI args, web upload, or API POST)
2. `ValidationService` validates file and parameters
3. `ConfigurationService` loads config (or uses default)
4. `ProcessingService` orchestrates processing:
   - `CSVProcessor` manages workflow
   - `CsvFileHandler` parses CSV to `CsvRow` objects
   - `RowsProcessor` filters (`RowFilter`), enriches (`RowEnrichment` or `RowEnrichmentML`), summarizes (`RowSummarizer`)
   - For API v2: `DataTablesResponseBuilder` builds detailed response with calculators
5. `DataFormattingService` formats output (HTML, CSV, JSON, or console)
6. `ResponseBuilderService` constructs final response (API only)

## Security Conventions
- Never log sensitive data (e.g., account numbers, personal info).
- Always validate user and file input before processing.
- Close file handles promptly after use; do not leave stale handles.
- Do not expose internal errors or stack traces to end users.
- Use trusted sources for ML models; loading via joblib can execute arbitrary code (known issue).

## Known Limitations
- Assumes single-currency account exports
- ML model is currently English-centric (language-agnostic models planned)
- Categorization may be imperfect; uncategorized transactions default to 'Other'
- REST API does not include authentication by default

## Python Conventions
- See `.github/instructions/python.instructions.md` for code style, documentation, and testing guidelines

## Extending & Integrating
- **Add Transaction Category:** Update config pattern sets and enrichment logic in `RowEnrichment`.
- **Support New CSV Format:** Adjust config `attribute_mapping` and parsing logic in `CsvFileHandler`.
- **Run ML Categorization:** Pass `--ml` to CLI or set in context/API parameters.
- **Custom Calculator (v0.8.0+):** Implement `RowCalculator` function, inject into `DataTablesResponseBuilder`. See `docs/calculator_pattern_example.py`.
- **New Service:** Follow dependency injection pattern, add to service layer, inject into controllers.
- **API Integration:** POST to `/api/v1/process` (summary) or `/api/v2/process` (detailed). See `API.md`.

## Useful Files
- `README.md` (project overview, CLI usage, features, interface comparison)
- `ARCHITECTURE.md` (detailed architecture documentation with Mermaid diagram)
- `PRODUCT.md` (product overview, use cases, workflows)
- `API.md` (complete REST API documentation)
- `src/whatsthedamage/scripts/README.md` (ML details)
- `AGENTS.md` (AI agent guidance)
- `Makefile` (workflow automation with dev, test, ruff, mypy, docs targets)
- `config/config.py` (central config/context, AppContext, AppArgs)
- `src/whatsthedamage/app.py` (Flask entrypoint, dependency injection setup)
- `docs/calculator_pattern_example.py` (calculator pattern examples)
- `pyproject.toml` (project metadata, dependencies)

---
**Feedback:** If any section is unclear or missing, please specify so it can be improved.
