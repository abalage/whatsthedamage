# whatsthedamage

This tool is designed to process CSV files and generate insightful reports. It relies on your bank's export functionality to save your historical data into CSV format.

_The slang phrase "what's the damage?" is often used to ask about the cost or price of something, typically in a casual or informal context. The phrase is commonly used in social settings, especially when discussing expenses or the results of an event._

## Why

My bank service provider gives me reports about my finances but they are not detailed enough, so I created `whatsthedamage` to provide the reports with details I found useful.

`whatsthedamage` provides **three interfaces** for different use cases:

1. **Command-Line Interface (CLI)** - For local, interactive use and automation scripts
2. **Web Interface (SPA)** - Standalone Vue 3 Single Page Application for users who prefer browser-based UI
3. **REST API** - Programmatic access for integrations, CI/CD pipelines, and external applications. For complete REST API documentation, see [API.md](API.md).

## Privacy

My financial details are considered a private matter between myself and my chosen bank. To process my bank account exports, I need a solution that ensures only I have access to the data.

- Support for Open Banking (PSD2) is out of the scope currently.
- Nothing is persisted on local storage. The web interface implements a **30-minute caching strategy** to improve performance and user experience. After that users need to re-upload and process their files.
- A Machine Learning models can be built to help reducing the burden of writing regular expressions to categorize your transactions. Your data, your model.

## Features
 - Process CSV exports. Multi-account, multi-currency support.
 - Categorizes transactions into well known [accounting categories](#transaction-categories).
 - Categorizes transactions into custom categories by using regular expressions or machine learning model.
 - Custom calculators for creating custom transaction calculations.
 - Transactions can be filtered by start and end dates. If no filter is set, grouping is based on the number of months.
 - Shows a report about the summarized amounts grouped by transaction categories, including Total Spendings, Balance.
 - Reports can be saved into CSV, XLS files with interactive DataTable visualization (sorting, searching).
 - Localization support. Currently English (default) and Hungarian languages are supported.
 - Frontend is a standalone Vue 3 SPA for easier use with API-only backend communication.
 - REST API v2 for programmatic access and integrations.

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

## Tested Bank providers
- K&H Bank

### Custom Calculators

`whatsthedamage` provides an internal API for creating custom transaction calculations beyond the built-in categorization. This makes the tool extensible for specific business logic or custom reporting needs.

For implementation examples, see [calculator_pattern_example.py](docs/calculator_pattern_example.py) in the documentation.

### Machine Learning categorization

Writing regular expressions might be easy for IT professionals, but it is definitely hard or even impossible for others. Maintaining them can also be challenging, even for professionals.

Using a machine learning model can automatically learn patterns from a given transaction history, making categorization faster and probably more accurate without manual rule creation.

The repository does not provide any pre-built model on purpose because of the risk of model inversion. Model inversion may reveal transaction data used for training the model to possible third parties which would defeat the purpose of the tool.  

If you want to read about how you can make a model for yourself check out its own [README_ML.md](src/whatsthedamage/README_ML.md) file.

## Install

This chapter describes how to install `whatsthedamage` in production. For development purposes check out the [Development](#development) chapter.

**Note**: The CLI tool works independently without the frontend. For web interface usage, see the [Frontend Development](#frontend-development) section for additional requirements (Node.js 24+, npm 10+).

### Manual install

The package is published to [https://pypi.org/project/whatsthedamage/](https://pypi.org/project/whatsthedamage/) therefore you can use pip / pipx to install it.
```shell
$ pipx install whatsthedamage
$ pip install --user whatsthedamage
```

The web interface requires you to start WSGI server (ie. gunicorn) manually.

Gunicorn requires either a configuration file or proper command line arguments passed when invoked from command line.

The repository contains an example [gunicorn_conf.py](config/gunicorn_conf.py) you can use out of the box.

```shell
$ cd
$ gunicorn --config gunicorn_conf.py whatsthedamage.app:app
```

### Docker image

There is also a Docker image you can use hosted on GitHub.

```shell
$ docker run --rm -ti --publish 5000:5000/tcp ghcr.io/abalage/whatsthedamage:latest
```

You can access the web interface on [http://localhost:5000](http://localhost:5000).

## Usage:
```
usage: whatsthedamage [-h] [--start-date START_DATE] [--end-date END_DATE] [--verbose] [--version] [--config CONFIG] [--category CATEGORY] [--output OUTPUT] [--output-format OUTPUT_FORMAT] [--nowrap]
                      [--filter FILTER] [--lang LANG] [--training-data] [--ml] [--log-level LOG_LEVEL] [--log-output LOG_OUTPUT] [--log-format LOG_FORMAT]
                      filename

A CLI tool to process bank account transaction exports in CSV files.

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
  --output, -o OUTPUT   Save the result into a CSV file with the specified filename.
  --output-format OUTPUT_FORMAT
                        Supported formats are: html, csv. (default: csv).
  --nowrap, -n          Do not wrap the output text. Useful for viewing the output without line wraps.
  --filter, -f FILTER   Filter by category. Use it in conjunction with --verbose.
  --lang, -l LANG       Language for localization.
  --training-data       Print training data in JSON format to STDERR. Use 2> redirection to save it to a file.
  --ml                  Use machine learning for categorization instead of regular expressions. (experimental)
  --log-level LOG_LEVEL
                        Set the logging level (DEBUG, INFO, WARN, ERROR). Default: WARN
  --log-output LOG_OUTPUT
                        Set the logging output (stdout or filename). Default: stdout
  --log-format LOG_FORMAT
                        Set the logging format (text or json). Default: text
```

### Configuration File

Please refer to the default config file for details.

A default configuration file is provided as [config.yml.default](config/config.yml.default).

### Troubleshooting

To troubleshoot why a transaction was assigned to a particular category, enable verbose mode using the `-v` or `--verbose` command line option.  

Should you want to check your regular expressions then you can use a handy online tool like https://regex101.com/.

Note: Regexp values are not stored as raw strings, so watch out for possible backslashes. For more information, see [What exactly is a raw string regex and how can you use it?](https://stackoverflow.com/questions/12871066/what-exactly-is-a-raw-string-regex-and-how-can-you-use-it).

## Transaction categories

This is the list of transaction categories `whatsthedamage` uses by default.

- **Balance**: Your total balance per time period. Basically the sum of all deposits minus the sum of all your purchases.
- **Clothes**: Clothing related purchases.
- **Deposit**: Money added to the account, such as direct deposits from employers, cash deposits, or transfers from other accounts.
- **Dining Out**: Restaurants, takeaway food, etc.
- **Electronics and Digital Services**: Purchases of electronics, software, digital subscriptions, streaming services, etc.
- **Entertainment and Leisure**: Spending related to entertainment, leisure activities, sports, recreation, massage, going to a bar or cinema.
- **Fee**: Charges applied by the bank, such as monthly maintenance fees, overdraft fees, or ATM fees.
- **Grocery**: Everything considered to sustain your life. Mostly food and other basic things required by your household.
- **Health**: Medicines, visiting a doctor, etc.
- **Home Maintenance**: Spendings on your housing, maintenance, reconstruction, etc.
- **Insurance**: Insurance premiums for health, vehicle, property, etc.
- **Interest**: Earnings on the account balance, typically seen in savings accounts or interest-bearing checking accounts.
- **Loan**: Any type of loans, mortgage.
- **Other**: Any transactions which do not fit into any of the other categories.
- **Payment**: Scheduled payments for bills or loans, which can be set up as automatic payments.
- **Refund**: Money returned to the account, often from returned purchases or corrections of previous transactions.
- **Total Spendings**: The sum of all spending transactions in a given period.
- **Transportation**: Public transport, taxi, fuel, parking, tolls, etc.
- **Transfer**: Movements of money between accounts, either within the same bank or to different banks.
- **Utility**: Regular, monthly recurring payments for stuff like Rent, Electricity, Gas, Water, Phone bills, etc.
- **Withdrawal**: Money taken out of the account, including ATM withdrawals, cash withdrawals at the bank, and electronic transfers.

Custom categories can be user-defined via config. Feel free to add your own categories into config.yml.

Note: the Machine Learning model was trained on the categories listed here.

## Limitations

- The categorization process may fail to categorize transactions because of the quality of the regular expressions / ML model. The transaction might be categorized as 'other'.
- The tool assumes that an account only uses a single currency.
- No authentication.

## Development

1. Clone the project repository: `git clone https://github.com/abalage/whatsthedamage.git`
2. Change directory containing the clone.
3. Issue `make dev`

The repository comes with a Makefile using 'GNU make' to automatize recurring actions. Here is the usage of the Makefile.

```shell
Development workflow:
  dev            - Create venv, install pip-tools, sync all requirements, install frontend dependencies

Development servers:
  backend        - Run API-only Flask backend development server
  frontend       - Run frontend development server (Vite)

Testing:
  test           - Run all tests (backend + frontend)
  test-backend   - Run backend tests only (pytest via tox)
  test-frontend  - Run frontend tests only (vitest)

Frontend scripts:
  frontend-build  - Build frontend for production
  frontend-test   - Run frontend tests (same as test-frontend)
  frontend-lint   - Run frontend linter
  frontend-knip   - Find unused code with knip
  frontend-%      - Run any npm script (e.g., 'frontend-build', 'frontend-test')

Build:
  build          - Full stack build (Python + JS)

Dependency management for Python:
  compile-deps   - Compile requirements files from pyproject.toml
  update-deps    - Update requirements to latest versions
  compile-deps-secure - Compile requirements with security hashes

Cleanup for Python and JavaScript:
  clean          - Clean up build files
  mrproper       - Clean + remove virtual environment, node_modules
```

### Frontend Development

The frontend is a standalone **Vue 3 Single Page Application (SPA)** with TypeScript. The frontend communicates with the backend exclusively through REST API endpoints, enabling independent development, deployment, and scaling.

**Frontend Location**: `frontend/` (project root directory)

**Architecture**:
- **Framework**: Vue 3 with Composition API
- **Type System**: TypeScript 5.x
- **State Management**: Pinia stores
- **Routing**: Vue Router 4
- **Build Tool**: Vite 8
- **UI Framework**: Bootstrap 5
- **Data Grid**: DataTables.net with Bootstrap 5 integration

**Frontend Structure**:
```
frontend/
├── src/
│   ├── main.ts                  # Application entry point
│   ├── App.vue                  # Root Vue component
│   ├── router/
│   │   └── index.ts             # Vue Router configuration
│   ├── components/
│   │   ├── Layout.vue           # Main layout component
│   │   ├── ErrorDisplay.vue      # Error display component
│   │   └── ui/                  # UI component library
│   │       ├── ButtonComponent.vue
│   │       ├── CardComponent.vue
│   │       └── StatisticalControls.vue
│   ├── pages/                   # Page-level components (routes)
│   │   ├── About.vue
│   │   ├── Details.vue
│   │   ├── Legal.vue
│   │   ├── Privacy.vue
│   │   ├── Results.vue
│   │   ├── Statistics.vue
│   │   ├── CategoryMonthTransactions.vue
│   │   └── MonthCategoriesList.vue
│   ├── stores/                  # Pinia state management
│   │   ├── form.ts              # Form state
│   │   ├── locale.ts            # Locale/language state
│   │   ├── statistical.ts       # Statistical analysis state
│   │   └── feedback.ts          # User feedback state
│   ├── js/                      # Utility functions and API client
│   │   ├── api.ts               # API client for backend communication
│   │   ├── main.ts              # DataTables initialization
│   │   ├── statistical-analysis.ts
│   │   ├── utils.ts
│   │   └── index.ts
│   ├── types/                   # TypeScript type definitions
│   │   ├── api.ts
│   │   └── index.ts
│   └── config/                  # Frontend configuration
│       └── highlight-config.ts
├── public/                     # Static assets
│   └── favicon.ico
├── dist/                        # Production build output
├── package.json
├── vite.config.js
├── tsconfig.json
└── README.md
```

**API Communication**:
- All frontend-backend communication happens via **REST API v2** endpoints
- Development: Vite proxies `/api` requests to `http://localhost:5000/api/v2`
- Production: Frontend uses relative `/api/v2` paths or configurable base URL via `VITE_API_BASE_URL`
- CORS-enabled for cross-origin requests

**Build Process**:
- Development: `npm run dev` (Vite dev server with HMR on port 3000)
- Production: `npm run build:prod` (builds to `dist/` with `/api/v2` base URL)
- For integrated deployment: Build output must be copied to `src/whatsthedamage/view/static/dist/`

### Localization

The application by default uses the English language, however it also supports Hungarian language.

For translation support [gettext](https://docs.python.org/3/library/gettext.html) is used.

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

If you have questions or need help getting started, open an issue and we'll be happy to assist.

Thank you for helping make this project better!
