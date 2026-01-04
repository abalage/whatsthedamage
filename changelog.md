# Changelog

## [0.10.0] - 2026-01-03

### BREAKING CHANGES
- **Removed deprecated API v1** (`/api/v1/process`). All users must migrate to v2 (`/api/v2/process`).
- **Removed `ProcessingService.process_summary()`** - Use `process_with_details()` instead.
- **Removed `RowSummarizer` class** - Replaced with inline sum calculations in v2 pipeline.
- **Removed `SummaryResponse` and `SummaryMetadata` models** - Use `DetailedResponse` for v2 API.
- **Removed `ResponseBuilderService.build_api_summary_response()`** - Use `build_api_detailed_response()`.
- **Removed `/download` web route** - CSV export now handled client-side via DataTables.
- **Removed `no_currency_format` parameter** - Currency formatting no longer applied to DataFrame outputs.
- **Removed `DataFormattingService.prepare_summary_table_data()`** - Unused v1 method with currency formatting.
- **Removed `DataFormattingService.prepare_datatables_summary_table_data()`** - Unused wrapper method.

### Removed
- API v1 endpoints and all related code
- Old summary-based data models (`SummaryResponse`, `SummaryMetadata`, `SummaryData`)
- Deprecated processing methods (`process_summary()`, `process_rows()`, `process()`)
- v1 web templates (`v1_results.html`) and routes (`/download`)
- v1 test files and mocking (API v1 tests, summary processing tests)
- Unused data formatting methods (`prepare_summary_table_data()`, `prepare_datatables_summary_table_data()`)
- Currency formatting from DataFrame output methods (HTML, CSV, String)
- RowSummarizer references from architecture documentation

### Changed
- **Web interface**: Now uses v2 processing exclusively with DataTables export functionality
- **Data formatting**: Removed automatic currency formatting from all DataFrame outputs (raw numeric values only)
- **Documentation**: Updated ARCHITECTURE.md and copilot-instructions.md to reflect v2-only architecture
- **Test suite**: Cleaned up to remove v1-specific tests, updated formatting tests to expect raw numbers

## [0.9.0]

Last version to support v1 API and old summary based methods (depending on DataFrames).

### Added
- **Feature**: Add multi-account support. Each account will be a separate entity. Currency is now belongs to the account's metadata.
- **Feature**: Further improve Service Layer contents.
- **Feature**: Add v2 view layer functions (`print_categorized_rows_v2()`, `print_training_data_v2()`) for multi-account verbose/training_data output.
- **Feature**: Add `skip_details` parameter to `DataTablesResponseBuilder` for performance optimization in summary-only workflows.

### Changed
- **Break**: CLI now uses v2 processing pipeline via `process_with_details()` for consistency with multi-account support.
- **Break**: Web summary route (`/process`) migrated to `process_with_details()`.
- **Break**: CsvRow objects now have 'account' metadata.
- **Refactor**: `process_rows_v2()` now handles verbose/training_data flags directly (no CLI bypass needed).
- **Refactor**: Remove unnecessary HTML parsing.
- **Refactor**: `SessionService` now uses dependency injection pattern like other services instead of direct instantiation.
- **Performance**: Optimize CSV processing by caching parsed rows in `CSVProcessor._rows` to avoid re-reading files.
- **Performance**: Skip building `DetailRow` objects when only summary data is needed (e.g., CLI, web summary, API v1).
- **Performance**: Significally reduce the amount of data stored in session storage.
- **Chore**: Unify canonical data format (DataTablesResponse) across all clients like CLI, API and Web.
- **Chore**: Unify DataFormattingService to support both panda's DataFrames and DataTablesResponse formats.
- **Chore**: Unify data flow: `Processing → Enhanced Data → Formatting → Output`
- **Chore**: Update tests to mock `_rows` attribute for improved test isolation.
- **Docs**: Fix reStructuredText formatting in docstrings for Sphinx compatibility.

### Deprecated
- **API v1** (`/api/v1/process`): Deprecated in favor of API v2. Will be removed in v0.10.0.
- **ProcessingService.process_summary()**: Use `process_with_details()` instead. Will be removed in v0.10.0.
- **RowsProcessor.process_rows()**: Use `process_rows_v2()` instead. Will be removed in v0.10.0.
- **CSVProcessor.process()**: Use `process_v2()` instead. Will be removed in v0.10.0.

### Bugs
- process_v1() is broken because multi-account support was intentionally not added. Upgrade to latest version or use "Use Machine Learning model for categorization" checkbox before submitting your CSV.

## [0.8.0] - 2025-12-19

Major architectural changes thanks to introducing Service Layer pattern.

API v1 is for backward compatibility, while API v2 is moving ahead with new features.

### Added
- **Feature**: Add service layer with FileUploadService, SessionService, ConfigurationService, ResponseBuilderService, ValidationService, and DataFormattingService.
- **Feature**: Add calculator pattern for extensibility.
- **Feature**: Add OpenAPI specs and implement v1/v2 API endpoints.
- **Feature**: Add API request/response models for structured processing.
- **Feature**: Add DataTable to visualize results with sorting capability.
- **Feature**: Add 'Total Spendings' to CLI output.
- **Feature**: Add markdowns for Copilot Agent.
- **Feature**: Add separate `ruff` and `mypy` Makefile shortcuts.
- **Tests**: Add unit tests for ProcessingService and API.

### Changed
- **Break**: Use dependency injection for processing_service.
- **Refactor**: Refactor routes to clean up responsibilities.
- **Refactor**: Refactor ValidationService to remove web dependency from CLI.
- **Refactor**: Update CLI to call service layer directly.
- **Chore**: Python-magic is now base requirement.
- **Chore**: Remove export endpoint from v2 API.
- **Chore**: Fix CLI separation of concerns.
- **Chore**: Move view functions.
- **Chore**: Remove explicit bank vendor mentions and generalize documentation.
- **Chore**: Add missing type hints and remove unused imports.
- **Chore**: Strings should be translatable.
- **Chore**: Do not track prompt files.
- **Docs**: Update API documentation and Sphinx docs.

### Fixed
- **Tests**: Don't break when HTML structure changes.

## [0.7.1] - 2025-10-07
### Added
- **Feature**: Add Docker support for easier deployment.
- **Feature**: Add basic `/health` endpoint.
- **Feature**: Add Makefile support for streamlined development workflow.
- **Feature**: Add sphinx autodoc for generating API Reference documentation.

### Changed
- **Tests**: Migrate from flake8 to ruff for linting.
- **Tests**: Fix errors reported by mypy.
- **Docker**: Use consistent version logic for Docker tags.
- **Docker**: Update Dockerfile for improved compatibility.

## [0.7.0] - 2025-09-18
### Changed
- **Feature**: (experimental) Add a self-developed Machine Learning (ML) algorithm to categorize transacions instead of regular expressions. See `ml_util.py` or `--ml` CLI argument.
- **Feature**: Export processed data in a format suitable for ML model training
- **Feature**: Add scikit-learn dependency
- **Feature**: Add new categories 'Insurance' and 'Sports Recreation'
- **Tests**: Upgrade tox environment from python3.11 to python3.13
- **Break**: Month names are no longer static but dynamically calculated. Side effect is that in the report the ordering of months is reversed.
- **Fix:**: Override empty 'type' attributes which might coming from card reservations. Increases accuracy of the ML model.

## [0.6.3] - 2025-07-01
### Changed
- **Feature**: Add localiztion to Flask frontend by using gettext for dynamic texts. Static files are served as-is.

## [0.6.2] - 2025-05-18
### Changed
- **Fix**: always categorize first by using type attribute

## [0.6.1] - 2025-05-15
### Changed
- **Chore**: update README to reflect changes since 0.4.0

## [0.6.0] - 2025-05-15
### Changed
- **Break**: Add `AppContext` to reduce coupling between config objects and application logic.
- **Break**: Move utility functions and classes into a dedicated `utils` directory.
- **Break**: Remove locale-based formatting; now rely on the value of the currency for formatting.
- **Break**: Switch configuration storage from JSON to YAML format.
- **Break**: Update config format and follow up changes in the web component.
- **Feature**: Add localization support with English and Hungarian languages.
- **Feature**: Localize datasets returned by the program.
- **Chore**: Remove `Optional` type hints and raise exceptions instead for missing values.
- **Fix**: Define missing variable in constructor.
- **Other**: Add initial gettext support for improved localization.
- **Other**: Rework enricher pattern sets for better maintainability.

## [0.5.0] - 2025-03-25
### Changed
- **Break**: Reorganize project layout to better fit MVC architecture
- **Feature**: Migrate web interface (Flask) to use a single repository
- **Chore**: Harmonize API calls between CLI and Web app

## [0.4.0] - 2025-03-18
### Changed
- **Chore**: Standardize data objects and get rid of ambiguous config settings in order to accommodate almost any type of CSVs.
- **Chore**: Improve code quality by using best practices like encapsulation, single responsibility, signaling private methods and attributes, etc.
- **Chore**: Attempts to generalize and share test dependencies like CsvRow fixtures among test cases
- **Chore**: Performance optimization to RowEnrichment class.
- **Break**: Renaming CsvFileReader to CsvFileHandler to avoid confusion about recently added write() method
- **Break**: Config file format has changed to reflect data object standardization

## [0.3.0] - 2025-02-05
### Added
- **Feature**: Single source version number. (commit: c2f1286)
- **Break**: Use unmatched positive amounts as deposits. (commit: 2087d6)
- **Fix**: Use proper access methods. (commit: 86cdf39)
- **Tests**: Fix flake8 and mypy regressions. (commit: 398f8df)
- **Break**: Different format is returned depending on caller. (commit: c276ddd)
- **Break**: `RowsProcessor` should use setters instead of accessing the config object. (commit: eec7448)
- **Break**: Use config models to enforce format and types. (commit: 27077da)
- **Break**: CLI should act as a CLI 'client' to the main module. (commit: 16cbd0e)

## [0.2.2] - 2025-01-26
### Changed
- **Break**: Different format is returned depending on caller. (commit: c276ddd)
- **Break**: `RowsProcessor` should use setters instead of accessing the config object. (commit: eec7448)
- **Break**: Use config models to enforce format and types. (commit: 27077da)
- **Break**: CLI should act as a CLI 'client' to the main module. (commit: 16cbd0e)
- **Fix**: Use proper access methods. (commit: 86cdf39)
- **Tests**: Fix flake8 and mypy regressions. (commit: 398f8df)

### Added
- **Test**: Add coverage report. (commit: 8a675eb)
- **Test**: Add tests for `rows_processor`. (commit: 112e232)
- **Test**: Add type hinting and documentation. (commit: 8c58fbc)

### Changed
- **Chore**: Improve error handling. (commit: ee6c302)
- **Break**: Encapsulate rows processing into a class method. (commit: c47f6dd)
- **Break**: Move data frame formatting into its own class. (commit: bf1d391)

## [0.2.1] - 2025-01-21
### Changed
- **Chore**: Minor version update to 0.2.1. (commit: c271eae)

## [0.2.0] - 2025-01-21
### Added
- **Feature**: Introduced filtering by category for troubleshooting. (commit: 3baa0a5)
- **CI/CD**: Added workflow for release lifecycle. Removes python-tox.yml. (commit: 5eeec65)

### Changed
- **Chore**: Increased version to 0.2.0. (commit: 8b0ee39)
- **Chore**: Improved code readability. (commit: 724a6e7)
- **Chore**: Updated Python classifiers. (commit: 3f878a1)
- **Test**: Reduced line length to fit within 200 characters. (commit: 383f625)
- **Test**: Removed unused `find_packages`. (commit: cd1595d)

### Added
- **CI**: Created `python-tox.yml` to use GitLab Workflow for running the test matrix. (commit: 62e998c)

## [0.1.0] - 2024-12-11
### Added
- **Feature**: Initial commit. (commit: e975eb4)