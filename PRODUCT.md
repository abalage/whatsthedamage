# whatsthedamage Product Overview

## Purpose
`whatsthedamage` is a Python-based tool designed to help users analyze, categorize, and summarize bank account transaction exports from CSV files. It aims to make personal finance decisions and expense tracking easier, supporting both technical and non-technical users through three interfaces: CLI, web interface, and REST API.

## Key Features

### 1. Transaction Categorization
- Automatically assigns transactions to well-known accounting categories (e.g., Grocery, Vehicle, Utility, Payment, etc.).
- Supports custom categories via user-defined regular expressions in the config file.
- Experimental machine learning model for automatic categorization, reducing the need for manual rule creation.

### 2. Filtering & Grouping
- Filter transactions by start and end dates, or group by month if no filter is set.
- Summarize amounts by category and time period for clear financial insights.

### 3. Reporting & Output
- Generates reports in CSV, HTML, and JSON formats.
- CLI output is formatted for readability; web output uses interactive HTML tables (with DataTables integration for sorting, filtering, and expandable details).
- REST API returns structured JSON responses for programmatic access.
- Downloadable CSV reports for further analysis in spreadsheet tools.
- Displays Total Spendings alongside Balance for comprehensive financial overview.

### 4. REST API (v0.8.0+)
- Two API versions for different use cases:
  - **v1**: Summary totals by category/month (backward compatible)
  - **v2**: Detailed transaction data with DataTables support
- JSON responses for automation, CI/CD pipelines, and third-party integrations.
- OpenAPI documentation available at `/docs` endpoint.
- Shares same business logic as CLI and web interface for consistency.

### 5. Calculator Pattern for Extensibility (v0.8.0+)
- Flexible calculation system for custom transaction summaries.
- Built-in calculators: Balance, Total Spendings.
- Extensible pattern allows custom business logic without modifying core code.
- Example implementations available in documentation.

### 6. Localization
- Supports English and Hungarian languages.
- All user-facing strings are translatable via standard gettext workflows.

### 7. Web Interface
- User-friendly Flask-based web app for uploading CSV files, configuring options, and viewing results.
- Interactive tables allow users to explore summarized data and drill down into transaction details.
- Secure file handling and input validation via dedicated service layer.
- Session management for maintaining user state across requests.
- Progressive enhancement: core functionality works without JavaScript.

### 8. Machine Learning (Experimental)
- Optionally categorize transactions using a pre-trained Random Forest model.
- Model trained on 14 years of transaction data; supports feature engineering and hyperparameter tuning.
- ML mode can be enabled via CLI (`--ml`) or web interface.

## Typical User Workflows

### Interactive Analysis (CLI or Web)
1. **Upload or specify a CSV file** (bank transaction export).
2. **Configure options** (date filters, category, output format, ML mode, etc.).
3. **Run analysis** via CLI or web interface.
4. **Review results** in a summarized table, grouped by category and time period.
5. **Drill down** into details for each category/month (web: popovers/tooltips).
6. **Download CSV report** for further use.

### Programmatic Integration (API)
1. **POST CSV file** to `/api/v1/process` or `/api/v2/process` endpoint.
2. **Include processing parameters** in the request (dates, ML mode, etc.).
3. **Receive JSON response** with categorized transactions and summaries.
4. **Integrate with CI/CD pipelines**, automation scripts, or third-party applications.
5. **Build custom frontends** or mobile apps using the API.

## Supported Transaction Categories
- Balance, Total Spendings, Clothes, Deposit, Fee, Grocery, Health, Home Maintenance, Insurance, Interest, Loan, Other, Payment, Refund, Sports Recreation, Transfer, Utility, Vehicle, Withdrawal
- Custom categories can be added via config.
- Balance and Total Spendings are calculated automatically using the calculator pattern.

## Architecture Highlights (v0.8.0+)
- **Service Layer Pattern**: Business logic separated from presentation layer.
- **Dependency Injection**: Services injected into controllers for testability.
- **Three Interfaces**: CLI, Web, and REST API share same core processing logic.
- **Calculator Pattern**: Extensible system for custom transaction calculations.
- **MVC Pattern**: Clear separation between Models, Views, and Controllers.
- **Type Safety**: Comprehensive type hints and mypy validation.
- **Code Quality**: Automated linting with ruff, testing with pytest and tox.

## Configuration & Customization
- YAML config file allows mapping CSV columns, defining categories, and enrichment patterns.
- Supports various bank export formats and custom attribute mappings.
- Calculator pattern enables custom business logic extensions.

## Security & Privacy
- Sensitive data (account numbers, personal info) is never logged.
- ML model loading via joblib can execute arbitrary code—use only trusted models.

## Limitations
- Categorization may be imperfect due to regex/ML model quality; uncategorized transactions default to 'Other'.
- Assumes single-currency account exports.
- ML model is currently English-centric; language-agnostic models planned for future releases.
- REST API does not include authentication by default (add if deploying in production).

## Example Use Cases
- **Personal Finance**: Expense tracking and budgeting with reports.
- **CI/CD Integration**: Automated transaction processing in deployment pipelines.
- **Third-Party Apps**: Build custom frontends or mobile apps using the REST API.
- **Automation**: Script-based batch processing of multiple CSV files.

## Getting Started
- **Install**: Via PyPI (`pip install whatsthedamage`) or use the Docker image.
- **CLI**: Run `whatsthedamage <file.csv>` with optional arguments.
- **Web**: Start Flask server with `make web` or using gunicorn in production.
- **API**: POST requests to `/api/v1/process` or `/api/v2/process` endpoints.
- **Customize**: Edit `config.yml` for your bank's CSV format and categories.
- **Extend**: Implement custom calculators following the calculator pattern.

## Development Tools (v0.8.0+)
- `make dev` - Set up development environment
- `make test` - Run tests with tox
- `make ruff` - Lint code with ruff
- `make mypy` - Type check with mypy
- `make docs` - Build Sphinx documentation

---
For more details, see `README.md`, `ARCHITECTURE.md`, `API.md`, and the web interface documentation.
