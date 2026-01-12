# AI Agent Guide for whatsthedamage

This document enables AI coding agents to be immediately productive in the `whatsthedamage` codebase. It consolidates architecture patterns, coding conventions, and project-specific guidance.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Developer Workflows](#developer-workflows)
- [Project-Specific Patterns](#project-specific-patterns)
- [Coding Conventions](#coding-conventions)
- [Security Conventions](#security-conventions)
- [Known Limitations](#known-limitations)
- [Extending & Integrating](#extending--integrating)
- [Useful Files](#useful-files)

---

## Architecture Overview

### Purpose
Processes bank transaction CSV exports, categorizes, filters, and summarizes them. Offers three interfaces:
- **CLI**: Command-line interface for direct file processing
- **Web**: Flask-based web interface with file uploads and interactive results
- **API**: REST API endpoints for programmatic integration

Includes experimental ML-based categorization alongside regex-based enrichment.

### Pattern
**Model-View-Controller (MVC) with Service Layer** for business logic separation (v0.8.0+).

### Key Components

```
src/whatsthedamage/
├── services/          # Business logic services (v0.8.0+)
│   ├── processing_service.py
│   ├── validation_service.py
│   ├── configuration_service.py
│   ├── session_service.py
│   ├── file_upload_service.py
│   ├── response_builder_service.py
│   └── data_formatting_service.py
├── models/            # Data models and processing
│   ├── csv_row.py
│   ├── rows_processor.py
│   ├── csv_processor.py
│   ├── row_enrichment.py
│   ├── row_enrichment_ml.py
│   ├── row_filter.py
│   ├── dt_response_builder.py
│   └── dt_calculators.py
├── controllers/       # Request handling
│   ├── cli_controller.py
│   ├── cli_app.py
│   ├── routes.py
│   └── routes_helpers.py
├── api/               # REST API
│   ├── v1/endpoints.py
│   ├── v2/endpoints.py
│   ├── helpers.py
│   └── docs.py
├── view/              # Output formatting
│   ├── templates/
│   ├── row_printer.py
│   └── data_frame_formatter.py
├── config/            # Configuration
│   ├── config.py
│   ├── dt_models.py
│   └── enricher_pattern_sets/
└── scripts/           # ML training and utilities
```

---

## Developer Workflows

### Build & Run

**Virtual Environment** (Always use):
```bash
python3 -m venv venv
source venv/bin/activate
```

**CLI Usage**:
```bash
python3 -m whatsthedamage <file.csv>
# or after make dev:
make dev  # Installs in development mode
```

**Web Interface**:
```bash
make web  # Flask development server
# Production: use gunicorn (see gunicorn_conf.py)
```

**API**:
- Available at `/api/v2/process`
- Documentation at `/docs` (Swagger UI)

**Common Tasks** (via Makefile):
```bash
make help    # Show all available targets
make test    # Run pytest
make ruff    # Lint with ruff
make mypy    # Type checking
make docs    # Build Sphinx documentation
```

### Testing

- All tests in `tests/` (pytest compatible)
- Run with `pytest` or `make test`
- Unit tests for services, API endpoints, and core logic
- **Always write tests for new features/bug fixes**
- Use virtual environment for testing

### Code Quality (v0.8.0+)

```bash
make ruff    # Linting
make mypy    # Type checking
make docs    # Documentation build
```

### ML Model

Train/test via scripts in `src/whatsthedamage/scripts/`:
- Uses scikit-learn, joblib for persistence
- See `scripts/README.md` for feature engineering and hyperparameter tuning

---

## Project-Specific Patterns

### Service Layer (v0.8.0+)

**Architecture**: Business logic isolated in services. Controllers depend on services via dependency injection.

**Available Services**:
- `ProcessingService`: CSV processing orchestration
- `ValidationService`: File and parameter validation
- `ConfigurationService`: Config loading and management
- `SessionService`: Web session management
- `FileUploadService`: File upload handling
- `ResponseBuilderService`: API/Web response construction
- `DataFormattingService`: Output formatting (HTML, CSV, JSON, console)

**Dependency Injection**:
- **CLI**: Uses `ServiceContainer` from `service_factory.py`
  ```python
  from whatsthedamage.services.service_factory import create_service_container
  
  container = create_service_container()
  processing_service = container.processing_service
  ```
- **Flask**: Uses `app.extensions` dictionary
  ```python
  processing_service = app.extensions['processing_service']
  ```

### Config/Context

**Centralized Configuration**: `AppContext` in `config/config.py`

**Pattern Sets**: Enrichment patterns in `config/enricher_pattern_sets`

**Example Config**:
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

### Row Processing Flow (v0.8.0+)

1. **Controller** receives request (CLI args, web upload, or API POST)
2. **CLI** initializes services via `create_service_container()` (returns `ServiceContainer` with lazy-loaded services)
3. **ValidationService** validates file and parameters
4. **ConfigurationService** loads config (or uses default)
5. **ProcessingService** orchestrates processing:
   - `CSVProcessor` manages workflow
   - `CsvFileHandler` parses CSV to `CsvRow` objects
   - `RowsProcessor` filters (`RowFilter`), enriches (`RowEnrichment` or `RowEnrichmentML`)
   - For API v2: `DataTablesResponseBuilder` builds detailed response with calculators
6. **DataFormattingService** formats output (HTML, CSV, JSON, or console)
7. **ResponseBuilderService** constructs final response (API only)

### Calculator Pattern (v0.8.0+)

**Purpose**: Extensible transaction calculations

`DataTablesResponseBuilder` accepts calculator functions:
```python
RowCalculator = Callable[[DataTablesResponseBuilder], List[AggregatedRow]]
```

**Built-in Calculators**:
- `create_balance_rows`: Running balance calculation
- `create_total_spendings`: Total spending aggregation

**Custom Calculator Example**:
```python
def custom_calculator(builder: DataTablesResponseBuilder) -> List[AggregatedRow]:
    # Access builder.build_aggregated_row() to create rows
    # Can access previously calculated rows
    return [aggregated_row1, aggregated_row2, ...]
```

See `docs/calculator_pattern_example.py` for complete examples.

### API Versioning

- **REST API** with detailed transactions
- **Shared `ProcessingService`** for consistency between CLI, Web, and API
- **Versioned Endpoints**: `/api/v1/process`, `/api/v2/process`
- **OpenAPI Documentation**: `/api/v1/openapi.json`, `/api/v2/openapi.json`

### Localization

- Locale folders: `src/whatsthedamage/locale/`
- Supported languages: English, Hungarian
- Uses Python `gettext` module

### Output Formats

- Console output (CLI)
- HTML reports (Web)
- CSV exports
- JSON responses (API)
- Output formatting centralized in `DataFormattingService`

### Integration

**External Libraries**:
- `scikit-learn`: Machine learning
- `Flask`: Web framework
- `joblib`: Model persistence
- CSV format customizable via config

---

## Coding Conventions

### General Principles

- **Single Responsibility Principle**: Each module/class/function should have one responsibility
- **SOLID Principles**: Apply for OOP design
- **Keep It Simple**: Avoid over-engineering
- **DRY (Don't Repeat Yourself)**: Reuse code via functions, classes, modules
- **No Breaking Changes**: Use deprecation warnings for public APIs
- **Never Log Sensitive Data**: No passwords, personal info, or secrets

### Python-Specific Guidelines

#### Code Style

- **Follow PEP 8**: Python style guide compliance
- **Indentation**: 4 spaces per level
- **Line Length**: Maximum 79 characters
- **Docstrings**: Follow PEP 257, use Sphinx flavor where applicable
- **Type Hints**: Always use with `typing` module
  ```python
  from typing import List, Dict, Optional
  
  def process_data(items: List[str], config: Optional[Dict[str, int]] = None) -> Dict[str, int]:
      """Process data items with optional configuration."""
      pass
  ```

#### Type Annotations

- Use `typing` module: `List[str]`, `Dict[str, int]`, `Optional[str]`
- **Avoid `Any` type** unless absolutely necessary
- Provide type hints for function parameters and return values

#### Documentation

- **Clear Comments**: Explain complex logic
- **Descriptive Names**: Functions and variables should be self-documenting
- **Docstrings**: Required for all public functions/classes
  ```python
  def calculate_area(radius: float) -> float:
      """
      Calculate the area of a circle given the radius.
      
      Parameters:
      radius (float): The radius of the circle.
      
      Returns:
      float: The area of the circle, calculated as π * radius^2.
      """
      import math
      return math.pi * radius ** 2
  ```

#### Code Organization

- **Break Down Complex Functions**: Split into smaller, manageable functions
- **Algorithm Comments**: Include explanations of approach used
- **Design Decision Comments**: Document why certain choices were made
- **Edge Case Handling**: Write clear exception handling

#### Testing

- **Test Critical Paths**: Always include test cases
- **Edge Cases**: Empty inputs, invalid data types, large datasets
- **Document Tests**: Docstrings explaining test cases
- **Parameterized Tests**: Use to reduce code duplication
- **Fixtures**: Leverage pytest fixtures
- **Maintainability Over Coverage**: Keep test files short and focused

#### Example

```python
from typing import List, Dict, Optional

def aggregate_transactions(
    transactions: List[Dict[str, float]],
    category: Optional[str] = None
) -> Dict[str, float]:
    """
    Aggregate transaction amounts by category.
    
    Parameters:
    transactions (List[Dict[str, float]]): List of transaction dictionaries
                                           with 'category' and 'amount' keys.
    category (Optional[str]): Filter by specific category. If None, aggregate all.
    
    Returns:
    Dict[str, float]: Dictionary mapping category to total amount.
    
    Raises:
    ValueError: If transactions list is empty or contains invalid data.
    """
    if not transactions:
        raise ValueError("Transactions list cannot be empty")
    
    result: Dict[str, float] = {}
    
    for tx in transactions:
        tx_category = tx.get('category', 'Unknown')
        if category and tx_category != category:
            continue
        
        amount = tx.get('amount', 0.0)
        result[tx_category] = result.get(tx_category, 0.0) + amount
    
    return result
```

### Virtual Environment

**Always use existing virtual environment** to run Python code unless it does not exist.

---

## Security Conventions

1. **Never log sensitive data**: Account numbers, personal info, passwords, secrets
2. **Validate all inputs**: User input and file input before processing
3. **Close file handles promptly**: Do not leave stale file handles
4. **Don't expose internal errors**: No stack traces to end users
5. **Trusted ML models only**: Loading via joblib can execute arbitrary code (known issue)
6. **Sanitize file uploads**: Validate MIME types and file extensions

---

## Known Limitations

- **Single-currency assumption**: Currently assumes single-currency account exports
- **English-centric ML**: ML model is primarily English-centric (language-agnostic models planned)
- **Imperfect categorization**: Uncategorized transactions default to 'Other'
- **No authentication**: REST API does not include authentication by default
- **Joblib security**: Model loading can execute arbitrary code (use trusted sources only)

---

## Extending & Integrating

### Add Transaction Category

1. Update config pattern sets in `config/enricher_pattern_sets`
2. Adjust enrichment logic in `RowEnrichment` or `RowEnrichmentML`

### Support New CSV Format

1. Adjust `attribute_mapping` in config YAML
2. Update parsing logic in `CsvFileHandler`

### Run ML Categorization

- **CLI**: `python3 -m whatsthedamage --ml <file.csv>`
- **API**: Set `ml_enabled: true` in request
- **Context**: Set flag in `AppContext`

### Create Custom Calculator (v0.8.0+)

1. Implement `RowCalculator` function:
   ```python
   def my_calculator(builder: DataTablesResponseBuilder) -> List[AggregatedRow]:
       # Use builder.build_aggregated_row() helper
       return [aggregated_rows...]
   ```
2. Inject into `DataTablesResponseBuilder`:
   ```python
   builder = DataTablesResponseBuilder(calculators=[create_balance_rows, my_calculator])
   ```
3. See `docs/calculator_pattern_example.py`

### Add New Service

1. Follow dependency injection pattern
2. Create service in `src/whatsthedamage/services/`
3. Add to service layer
4. Inject into controllers
5. Update `ServiceContainer` in `service_factory.py` for CLI usage

For CLI do not add services which are only required by web.

### API Integration

**POST to `/api/v2/process`** for detailed transaction processing:
```bash
curl -X POST http://localhost:5000/api/v2/process \
  -F "csv_file=@transactions.csv" \
  -F "start_date=2023-01-01" \
  -F "end_date=2023-12-31"
```

See `API.md` for complete documentation.

---

## Useful Files

### Documentation
- [`README.md`](README.md) - Project overview, CLI usage, features, interface comparison
- [`ARCHITECTURE.md`](ARCHITECTURE.md) - Detailed architecture with Mermaid diagram
- [`PRODUCT.md`](PRODUCT.md) - Product overview, use cases, workflows
- [`API.md`](API.md) - Complete REST API documentation
- [`AGENTS.md`](AGENTS.md) - This file (AI agent guidance)

### Configuration & Build
- [`Makefile`](Makefile) - Workflow automation (dev, test, ruff, mypy, docs targets)
- [`pyproject.toml`](pyproject.toml) - Project metadata, dependencies
- [`config.yml`](config.yml) - Application configuration example
- [`docs/config.yml.default`](docs/config.yml.default) - Default configuration template

### Key Source Files
- [`src/whatsthedamage/config/config.py`](src/whatsthedamage/config/config.py) - Central config/context (AppContext, AppArgs)
- [`src/whatsthedamage/app.py`](src/whatsthedamage/app.py) - Flask entrypoint, dependency injection setup
- [`src/whatsthedamage/services/service_factory.py`](src/whatsthedamage/services/service_factory.py) - CLI dependency injection via ServiceContainer
- [`src/whatsthedamage/models/rows_processor.py`](src/whatsthedamage/models/rows_processor.py) - Core row processing logic
- [`src/whatsthedamage/models/dt_response_builder.py`](src/whatsthedamage/models/dt_response_builder.py) - DataTables response builder
- [`docs/calculator_pattern_example.py`](docs/calculator_pattern_example.py) - Calculator pattern examples

### ML & Scripts
- [`src/whatsthedamage/scripts/README.md`](src/whatsthedamage/scripts/README.md) - ML model training, feature engineering, hyperparameter tuning

---

## Quick Start for AI Agents

1. **Read Architecture**: Start with [ARCHITECTURE.md](ARCHITECTURE.md) for system overview
2. **Check Product Context**: Review [PRODUCT.md](PRODUCT.md) for use cases
3. **Understand API**: Read [API.md](API.md) if working on API features
4. **Review Service Layer**: Services in `src/whatsthedamage/services/` for business logic
5. **Run Tests**: Always run `make test` or `pytest` before committing
6. **Check Code Quality**: Run `make ruff` and `make mypy`
7. **Use Virtual Environment**: Always activate before running Python
8. **Follow Patterns**: Use dependency injection, service layer, calculator pattern as appropriate
9. **Write Tests**: For every new feature or bug fix
10. **Document**: Update docstrings and relevant .md files

---

## Feedback

If any section is unclear or missing, please specify so it can be improved. This document is a living guide that evolves with the codebase.
