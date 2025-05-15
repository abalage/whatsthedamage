# Changelog

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