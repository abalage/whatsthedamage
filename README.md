# whatsthedamage

An opinionated open source tool written in Python to process bank account transaction exports in CSV files.

Efforts were made to be able to customize the behavior and potentially work with any CSV format finance companies may produce.

The project contains a command line tool as well as a web interface for easier usage.

An experimental Machine Learning model is also available to help reducing the burden of writing regular expressions.

_The slang phrase "what's the damage?" is often used to ask about the cost or price of something, typically in a casual or informal context. The phrase is commonly used in social settings, especially when discussing expenses or the results of an event._

## Features
 - Categorizes transactions into well known [accounting categories](#transaction-categories).
 - Categorizes transactions into custom categories by using regular expressions.
 - Calculator pattern for extensible custom transaction calculations.
 - Transactions can be filtered by start and end dates. If no filter is set, grouping is based on the number of months.
 - Shows a report about the summarized amounts grouped by transaction categories, including Total Spendings.
 - Reports can be saved into CSV or HTML files with interactive DataTable visualization (sorting, searching).
 - Localization support. Currently English (default) and Hungarian languages are supported.
 - Web interface for easier use.
 - REST API (v1 and v2) for programmatic access and integrations.

Example output on console. The values in the following example are arbitrary.
```
                         January          February
Balance            129576.00 HUF    1086770.00 HUF
Vehicle           -106151.00 HUF     -54438.00 HUF
Clothes            -14180.00 HUF          0.00 HUF
Deposit            725313.00 HUF    1112370.00 HUF
Fee                 -2494.00 HUF      -2960.00 HUF
Grocery           -172257.00 HUF    -170511.00 HUF
Health             -12331.00 HUF     -25000.00 HUF
Home Maintenance        0.00 HUF     -43366.00 HUF
Interest                5.00 HUF          8.00 HUF
Loan               -59183.00 HUF     -59183.00 HUF
Other              -86411.00 HUF     -26582.00 HUF
Payment            -25500.00 HUF     583580.00 HUF
Refund                890.00 HUF        890.00 HUF
Transfer                0.00 HUF          0.00 HUF
Utility            -68125.00 HUF     -78038.00 HUF
Withdrawal         -50000.00 HUF    -150000.00 HUF

```

### Calculator Pattern for Extensibility

`whatsthedamage` now supports a **calculator pattern** that allows you to define custom transaction calculations beyond the built-in categorization. This makes the tool extensible for specific business logic or custom reporting needs.

For implementation examples, see [calculator_pattern_example.py](docs/calculator_pattern_example.py) in the documentation.

### Machine Learning categorization (experimental)

Writing regular expressions might be easy for IT professionals, but it is definitely hard or even impossible for others. Maintaining them can also be challenging, even for professionals.

Using a machine learning model can automatically learn patterns from a given transaction history, making categorization faster and probably more accurate without manual rule creation.

If you want to read more about the ML model used by `whatsthedamage`, check out its own [README.md](src/whatsthedamage/scripts/README.md) file.

The repository has an experimental pre-built model.  

The model currently relies on the English language. Language-agnostic models are planned for the future.

**Warning**
 - The model is expected to be opinionated. Predicted categories could be completely wrong.
 - The model is currently persisted using 'joblib', which may pose a security risk of executing arbitrary code upon loading. __Use the model you trust; use it at your own risk.__

Try experimenting with it by providing the `--ml` command line argument to `whatsthedamage`.

## Architecture Overview

`whatsthedamage` provides **three interfaces** for different use cases:

1. **Command-Line Interface (CLI)** - For local, interactive use and automation scripts
2. **Web Interface** - Browser-based UI for users who prefer forms over terminal commands
3. **REST API** - Programmatic access for integrations, CI/CD pipelines, and external applications

All three interfaces share the same **core business logic** through a well-defined **service layer** (including `ProcessingService`, `ValidationService`, `ConfigurationService`, and others), ensuring consistent transaction processing regardless of how you access the tool. This architecture was introduced in version 0.8.0 and uses dependency injection for better testability and maintainability.

### Interface Comparison

| Feature | CLI | Web UI | REST API |
|---------|-----|--------|----------|
| **Access Method** | Terminal commands | Browser forms | HTTP requests |
| **Authentication** | None | Session-based | None (add if needed) |
| **Input** | File paths | File upload | Multipart form data |
| **Output** | Console/CSV/HTML | HTML page | JSON |
| **Use Case** | Local analysis, scripts | Ad-hoc exploration | Automation, integrations |
| **Requires Server** | ❌ No | ✅ Yes | ✅ Yes |
| **Interactive** | ✅ Yes | ✅ Yes | ❌ No (stateless) |

### When to Use What?

**Use the CLI when:**
- Running locally on your machine
- Automating with shell scripts
- Processing files in batch
- Integrating with terminal workflows
- You prefer command-line tools

**Use the Web UI when:**
- You prefer graphical interfaces
- Sharing access with non-technical users
- Quick ad-hoc analysis without installing anything
- You want interactive table features (sorting, searching)

**Use the REST API when:**
- Integrating with other applications
- Building custom frontends
- Automating in CI/CD pipelines
- Processing transactions from external systems
- Need programmatic access with JSON responses

For complete REST API documentation, see [API.md](API.md).

## Install

This chapter describes how to install `whatsthedamage` in production. For development purposes check out the [Development](#development) chapter.

### Manual install

The package is published to [https://pypi.org/project/whatsthedamage/](https://pypi.org/project/whatsthedamage/) therefore you can use pip / pipx to install it.
```shell
$ pipx install whatsthedamage
$ pip install --user whatsthedamage
```

The web interface requires you to start WSGI server (ie. gunicorn) manually.

Gunicorn requires either a configuration file or proper command line arguments passed when invoked from command line.

The repository contains an example [gunicorn_conf.py](gunicorn_conf.py) you can use out of the box.

```shell
$ cd
$ gunicorn --config gunicorn_conf.py whatsthedamage.app:app
```

### Docker image

There is also an experimental Docker image you can use hosted on GitHub.

```shell
$ docker run --rm -ti --publish 5000:5000/tcp ghcr.io/abalage/whatsthedamage:latest
```

You can access the web interface on [http://localhost:5000](http://localhost:5000).

## Usage:
```
usage: whatsthedamage [-h] [--start-date START_DATE] [--end-date END_DATE] [--verbose] [--version] [--config CONFIG] [--category CATEGORY] [--no-currency-format] [--output OUTPUT]
                      [--output-format OUTPUT_FORMAT] [--nowrap] [--filter FILTER] [--lang LANG] [--training-data] [--ml]
                      filename

A CLI tool to process KHBHU CSV files.

positional arguments:
  filename              The CSV file to read.

options:
  -h, --help            show this help message and exit
  --start-date START_DATE
                        Start date (e.g. YYYY.MM.DD.)
  --end-date END_DATE   End date (e.g. YYYY.MM.DD.)
  --verbose, -v         Print categorized rows for troubleshooting.
  --version             Show the version of the program.
  --config, -c CONFIG   Path to the configuration file.
  --category CATEGORY   The attribute to categorize by. (default: category)
  --no-currency-format  Disable currency formatting. Useful for importing the data into a spreadsheet.
  --output, -o OUTPUT   Save the result into a CSV file with the specified filename.
  --output-format OUTPUT_FORMAT
                        Supported formats are: html, csv. (default: csv).
  --nowrap, -n          Do not wrap the output text. Useful for viewing the output without line wraps.
  --filter, -f FILTER   Filter by category. Use it in conjunction with --verbose.
  --lang, -l LANG       Language for localization.
  --training-data       Print training data in JSON format to STDERR. Use 2> redirection to save it to a file.
  --ml                  Use machine learning for categorization instead of regular expressions. (experimental)
```

### Configuration File

The config file format and syntax has considerably changed in v0.6.0 (JSON to YAML). Please refer to the default config file for details.

A default configuration file is provided as [config.yml.default](docs/config.yml.default).

If you do not want to create a configuration file then you can try the experimental [Machine Learning](#machine-learning-categorization-experimental) mode to categorize transactions.

### Troubleshooting

To troubleshoot why a transaction was assigned to a particular category, enable verbose mode using the `-v` or `--verbose` command line option.  
By default, only the attributes (columns) specified by `selected_attributes` in the configuration file are displayed. The `category` attribute is generated by the tool.

Should you want to check your regular expressions then you can use a handy online tool like https://regex101.com/.

Note: Regexp values are not stored as raw strings, so watch out for possible backslashes. For more information, see [What exactly is a raw string regex and how can you use it?](https://stackoverflow.com/questions/12871066/what-exactly-is-a-raw-string-regex-and-how-can-you-use-it).

## Transaction categories

This is the list of transaction categories `whatsthedamage` uses by default.

- **Balance**: Your total balance per time period. Basically the sum of all deposits minus the sum of all your purchases.
- **Clothes**: Clothing related purchases.
- **Deposit**: Money added to the account, such as direct deposits from employers, cash deposits, or transfers from other accounts.
- **Fee**: Charges applied by the bank, such as monthly maintenance fees, overdraft fees, or ATM fees.
- **Grocery**: Everything considered to sustain your life. Mostly food and other basic things required by your household.
- **Health**: Medicines, vising a doctor, etc.
- **Home Maintenance**: Spendings on your housing, maintencance, reconstruction, etc.
- **Interest**: Earnings on the account balance, typically seen in savings accounts or interest-bearing checking accounts.
- **Loan**: Any type of loans, mortgage.
- **Other**: Any transactions which do not fit into any of the other categories.
- **Payment**: Scheduled payments for bills or loans, which can be set up as automatic payments.
- **Refund**: Money returned to the account, often from returned purchases or corrections of previous transactions.
- **Sports Recreation**: Spending related to sports and recreations like massage, going into a bar or cinema.
- **Transfer**: Movements of money between accounts, either within the same bank or to different banks.
- **Utility**: Regular, monthly recurring payments for stuff like Rent, Electricity, Gas, Water, Phone bills, etc.
- **Vehicle**: All purchases - except Insurance - related to owning a vehicle.
- **Withdrawal**: Money taken out of the account, including ATM withdrawals, cash withdrawals at the bank, and electronic transfers.

Custom categories can be user-defined via config. Feel free to add your own categories into config.yml.

Note: the Machine Learning model was trained on the categories listed here.

## Limitations

- The categorization process may fail to categorize transactions because of the quality of the regular expressions / ML model. The transaction might be categorized as 'other'.
- The tool assumes that account exports only use a single currency.
- The Machine Learning model is currently English-centric; language-agnostic models are planned for future releases.
- REST API currently does not include authentication.

## Development

The repository comes with a Makefile using 'GNU make' to automatize recurring actions. Here is the usage of the Makefile.

```shell
$ make help
Development workflow:
  dev            - Create venv, install pip-tools, sync all requirements
  web            - Run Flask development server
  test           - Run tests using tox
  ruff           - Run ruff linter/formatter
  mypy           - Run mypy type checker
  image          - Build Podman image with version tag
  lang           - Extract translatable strings to English .pot file
  docs           - Build Sphinx documentation

Dependency management:
  compile-deps   - Compile requirements files from pyproject.toml
  update-deps    - Update requirements to latest versions
  compile-deps-secure - Generate requirements with hashes

Cleanup:
  clean          - Clean up build files
  mrproper       - Clean + remove virtual environment
```

### Localization

The application by default uses the English language, however it also supports Hungarian language.

For translation support the tool uses Python's [gettext](https://docs.python.org/3/library/gettext.html) library.

1. To update the English .pot file with new translatable strings use `make lang`.
```shell
$ make lang
```
2. Create or edit the .po file to add translations by a tool like `poedit`.
```shell
$ poedit locale/en/LC_MESSAGES/messages.po
```
3. Compile the .po file into a .mo file. (`poedit` will do this for you):
```bash
$ msgfmt locale/en/LC_MESSAGES/messages.po -o locale/en/LC_MESSAGES/messages.mo
```

### Contributing

Contributions are welcome! If you have ideas for improvements, bug fixes, new features, or additional documentation, feel free to open an issue or submit a pull request.

To contribute:

1. **Fork the repository** and create your branch from `main`.
2. **Make your changes** with clear commit messages.
3. **Test your changes** to ensure nothing is broken.
4. **Open a pull request** describing your changes and the motivation behind them.

If you have questions or need help getting started, open an issue and we’ll be happy to assist.

Thank you for helping make this project better!
