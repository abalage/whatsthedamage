# Copilot Instructions for whatsthedamage

This guide enables AI coding agents to be immediately productive in the `whatsthedamage` codebase.

## Architecture Overview
- **Purpose:** Processes bank transaction CSV exports, categorizes, filters, and summarizes them. Offers both CLI and Flask-based web interfaces. Includes experimental ML-based categorization.
- **Pattern:** Model-View-Controller (MVC) for clear separation of concerns.
- **Key Components:**
  - `src/whatsthedamage/models/`: Data models (`CsvRow`), row processing (`RowsProcessor`), ML, enrichment, filtering, summarizing.
  - `src/whatsthedamage/controllers/`: CLI and web routing/controllers.
  - `src/whatsthedamage/view/`: Output formatting (console, HTML, CSV).
  - `src/whatsthedamage/config/`: App context, config loading, pattern sets.
  - `src/whatsthedamage/scripts/`: ML model training, feature engineering, documentation.

## Developer Workflows
- **Build & Run:**
  - CLI: `python -m whatsthedamage` (from `src/whatsthedamage/`)
  - Web: Flask app entry in `app.py`
  - Use `Makefile` for common tasks (`make help` for targets)
- **Testing:** 
  - All tests in `tests/` (pytest compatible). Run with `pytest` or `make test`.
  - Always write tests for new features/bug fixes.
- **ML Model:** Train/test via scripts in `src/whatsthedamage/scripts/`. Uses scikit-learn, joblib for persistence. See `scripts/README.md` for feature engineering and hyperparameter tuning.

## Project-Specific Patterns
- **Config/Context:** Centralized in `AppContext` (`config/config.py`). Pattern sets for enrichment in `config/enricher_pattern_sets`.
- **Row Processing:** `RowsProcessor` orchestrates filtering, enrichment (ML or regex), categorization, and summarization. ML and regex enrichment are interchangeable via flags/context.
- **Localization:** Locale folders under `src/whatsthedamage/locale/`. English and Hungarian supported. Uses Python `gettext`.
- **Output:** Console and HTML/CSV reports. Output formatting in `view/`.
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

### Example: Row Processing Flow
1. Parse CSV to `CsvRow` objects
2. Filter rows by date/month (`RowFilter`)
3. Enrich/categorize rows (`RowEnrichment` or `RowEnrichmentML`)
4. Summarize by category (`RowSummarizer`)
5. Format for output (`DataFrameFormatter`)

## Security Conventions
- Never log sensitive data (e.g., account numbers, personal info).
- Always validate user and file input before processing.
- Close file handles promptly after use; do not leave stale handles.
- Do not expose internal errors or stack traces to end users.
- Use trusted sources for ML models; loading via joblib can execute arbitrary code (known issue).

## Known Limitations
- Assumes single-currency account exports
- ML model is currently English-centric
- Categorization may be imperfect; uncategorized transactions default to 'Other'

## Python Conventions
- See `.github/instructions/python.instructions.md` for code style, documentation, and testing guidelines

## Extending & Integrating
- To add a transaction category: update config pattern sets and enrichment logic.
- To support a new CSV format: adjust config and parsing logic in models.
- To run ML categorization: pass `--ml` to CLI or set in context.

## Useful Files
- `README.md` (project overview, CLI usage, config, categories)
- `src/whatsthedamage/scripts/README.md` (ML details)
- `AGENTS.md` (AI agent guidance)
- `Makefile` (workflow automation)
- `config/config.py` (central config/context)
- `src/whatsthedamage/app.py` (Flask entrypoint)

---
**Feedback:** If any section is unclear or missing, please specify so it can be improved.
