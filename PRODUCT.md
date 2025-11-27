# whatsthedamage Product Overview

## Purpose
`whatsthedamage` is a Python-based tool designed to help users analyze, categorize, and summarize bank account transaction exports from CSV files. It aims to make personal finance management and expense tracking easier, supporting both technical and non-technical users through a CLI and a web interface.

## Key Features

### 1. Transaction Categorization
- Automatically assigns transactions to well-known accounting categories (e.g., Grocery, Vehicle, Utility, Payment, etc.).
- Supports custom categories via user-defined regular expressions in the config file.
- Experimental machine learning model for automatic categorization, reducing the need for manual rule creation.

### 2. Filtering & Grouping
- Filter transactions by start and end dates, or group by month if no filter is set.
- Summarize amounts by category and time period for clear financial insights.

### 3. Reporting & Output
- Generates reports in both CSV and HTML formats.
- CLI output is formatted for readability; web output uses interactive HTML tables (with DataTables integration for sorting, filtering, and expandable details).
- Downloadable CSV reports for further analysis in spreadsheet tools.

### 4. Localization
- Supports English and Hungarian languages.
- All user-facing strings are translatable via standard gettext workflows.

### 5. Web Interface
- User-friendly Flask-based web app for uploading CSV files, configuring options, and viewing results.
- Interactive tables allow users to explore summarized data and drill down into transaction details.
- Secure file handling and input validation.

### 6. Machine Learning (Experimental)
- Optionally categorize transactions using a pre-trained Random Forest model.
- Model trained on 14 years of transaction data; supports feature engineering and hyperparameter tuning.
- ML mode can be enabled via CLI (`--ml`) or web interface.

## Typical User Workflow
1. **Upload or specify a CSV file** (bank transaction export).
2. **Configure options** (date filters, category, output format, ML mode, etc.).
3. **Run analysis** via CLI or web interface.
4. **Review results** in a summarized table, grouped by category and time period.
5. **Drill down** into details for each category/month (web: popovers/tooltips).
6. **Download CSV report** for further use.

## Supported Transaction Categories
- Balance, Clothes, Deposit, Fee, Grocery, Health, Home Maintenance, Interest, Loan, Other, Payment, Refund, Sports Recreation, Transfer, Utility, Vehicle, Withdrawal
- Custom categories can be added via config.

## Configuration & Customization
- YAML config file allows mapping CSV columns, defining categories, and enrichment patterns.
- Supports various bank export formats and custom attribute mappings.

## Security & Privacy
- Sensitive data (account numbers, personal info) is never logged.
- ML model loading via joblib can execute arbitrary code—use only trusted models.

## Limitations
- Categorization may be imperfect due to regex/ML model quality; uncategorized transactions default to 'Other'.
- Assumes single-currency account exports.
- ML model is currently English-centric.

## Example Use Cases
- Personal expense tracking and budgeting.
- Small business transaction analysis.
- Quick categorization and reporting for tax preparation.
- Exploring spending patterns over time.

## Getting Started
- Install via PyPI (`pip install whatsthedamage`) or use the Docker image.
- Run via CLI or start the web server (see `README.md` for details).
- Customize config for your bank’s CSV format and categories.

---
For more details, see `README.md`, `ARCHITECTURE.md`, and the web interface documentation.
