# whatsthedamage

This tool is designed to categorize your bank transactions and generate insightful reports. It relies on your bank's export functionality to save your historical data into CSV format.

_The slang phrase "what's the damage?" is often used to ask about the cost or price of something, typically in a casual or informal context. The phrase is commonly used in social settings, especially when discussing expenses or the results of an event._

`whatsthedamage` provides **three interfaces** for different use cases:

1. **Command-Line Interface (CLI)** - For local, interactive use, mostly for troubleshooting.
2. **Web Interface (SPA)** - For users who prefer browser-based UI, this provides the most features.
3. **REST API** - See [API.md](API.md).

## Main Features
 - Process CSV exports. Supports multi-account and multi-currency.
 - Categorizes transactions into well known [accounting categories](#transaction-categories).
 - Categorizes transactions into custom categories by using regular expressions or a [machine learning model](#machine-learning-categorization).
 - Transactions can be pre-filtered by start and end dates. If no filter is set, grouping is based on the number of months.
 - Statistical algorithms to highlight outlier categories or transactions. (Web interface only)
 - Visualize reports using Bar charts, Pie charts, etc. (Web interface only)
 - Pivot table to set up your own reports. (Web interface only)

## Tested Bank providers
- K&H Bank Zrt.

## Transaction categories

This is the list of transaction categories `whatsthedamage` uses by default.

- **Balance** (calculated): Your total balance per time period. Basically the sum of all deposits minus the sum of all your purchases.
- **Clothes**: Clothing related purchases.
- **Cost of Living:** (calculated): The summary of Grocery, Loan, Transportation, Utility, Payment, Fee and Health categories. See: [COST_OF_LIVING_CATEGORY_IDS](src/whatsthedamage/config/config.py)
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
- **Total Spendings** (calculated): The sum of all spending transactions in a given period.
- **Transfer**: Movements of money between accounts, either within the same bank or to different banks.
- **Transportation**: Public transport, taxi, fuel, parking, tolls, etc.
- **Utility**: Regular, monthly recurring payments for stuff like Rent, Electricity, Gas, Water, Phone bills, etc.
- **Withdrawal**: Money taken out of the account, including ATM withdrawals, cash withdrawals at the bank, and electronic transfers.

Custom categories can be user-defined via config. Feel free to add your own categories into config.yml.

Note: the Machine Learning model was trained on the categories listed above.

## Privacy

My financial details are considered a private matter between myself and my chosen bank. To process my bank account exports, I need a solution that ensures only I have access to the data.

- Support for Open Banking (PSD2) is out of the scope.
- Nothing is persisted on local storage. The web interface implements a **30-minute caching strategy** to improve performance and user experience. Once cache expires the data gets deleted.
- Machine Learning models can be built to help reducing the burden of writing regular expressions to categorize your transactions. Your data, your model.

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

You can use a pre-built Docker image to try the software.

```shell
$ docker run --rm -ti --publish 5000:5000/tcp ghcr.io/abalage/whatsthedamage:latest
```

You can access the web interface on [http://localhost:5000](http://localhost:5000).

## CLI Usage

The CLI interface provides `--help` to show you the available options. For start you can simply provide a path to your CSV export.

```bash
whatsthedamage /path/to/transactions.csv
```

## Advanced usage

### CSV profiles

To properly read a bank provider's CSV format `CSV profiles` are used. A CSV profile (`CsvProfile`) provides settings to parse the CSV format as well as a mapping to match parsed CSV fields to attributes the software expects.

The list of available CSV profiles and their format is stored in [csv_profiles](src/whatsthedamage/config/csv_profiles.py).

### Configuration File

Providing custom categories and regular expressions can be done by creating a custom configuration file.

A default configuration in YAML format is provided as [config.yml.default](src/whatsthedamage/config/config.yml.default). You can use this as a base to extend it. This is the format of the configuration file.

The field `enricher_pattern_sets` are used for matching transactions defined in `partner` and `type` fields to categories.

The field `text_cleaning` provides regular expressions to strip off information from `partner` attribute values not required for categorization like `company_suffixes` or fixing mispelled or buggy texts with `buggy_partner_replacements`. 

Warning: Only use these if you know what you are doing.

```
enricher_pattern_sets:
  partner:
    grocery:
      - "abc.*"
  ...

  type:
    loan:
      - "hitel.*"
      - "késedelmi.*"
    withdrawal:
      - "Készpénzfelvét.*"
  ...

text_cleaning:
  company_suffixes:
    - "\\s+(?:[Kk]ft|[Zz]rt|[Rr]t|[Nn]yrt)\\.*\\b"
    - "\\s*(es\\s+)?tarsasag\\s*$"
    - "\\s*korlatolt\\s+felelossegu\\s*$"
    - "\\s*kisker\\s*$"
    - "\\s*szolgaltato\\s*$"
    - "\\s*kereskedelmi\\s*$"
    ...
  buggy_partner_replacements:
    "CUKRA SZDA": "Cukrászda"
    "vende glo": "Vendeglő"
```

Note: Currently adding a new category also requires adding them to `AVAILABLE_CATEGORIES` in [config.py](src/whatsthedamage/config/config.py). #FIXME

### Machine Learning categorization

Writing regular expressions might be easy for IT professionals, but it is definitely hard or even impossible for others. Maintaining them can also be challenging, even for professionals.

Using a machine learning model can automatically learn patterns from a given transaction history, making categorization faster and probably more accurate without manual rule creation.

This project however repository does not provide any pre-built model on purpose because of the risk of model inversion. Model inversion may reveal transaction data used for training the model to possible third parties which would defeat the purpose of the tool.  

However you can create your own model for categorization, just follow the steps in [README_ML.md](README_ML.md) file.

### Troubleshooting

CLI usage only.

To troubleshoot why a transaction was assigned to a particular category, enable verbose mode using the `-v` or `--verbose` command line option.  

Should you want to check your regular expressions then you can use a handy online tool like https://regex101.com/.

Note: Regexp values are not stored as raw strings, so watch out for possible backslashes. For more information, see [What exactly is a raw string regex and how can you use it?](https://stackoverflow.com/questions/12871066/what-exactly-is-a-raw-string-regex-and-how-can-you-use-it).

## Limitations

- The categorization process may fail to categorize transactions because of the quality of the regular expressions / ML model. The transaction might be categorized as 'other'.
- The tool assumes that an account only uses a single currency.
- No user management, no authentication.

## Development

1. Clone the project repository: `git clone https://github.com/abalage/whatsthedamage.git`
2. Change directory containing the clone.
3. Issue `make dev`

The repository comes with a Makefile using 'GNU make' to automatize recurring actions. Issue `make help` to see the usage.

### Frontend Development

The frontend is a standalone **Vue 3 Single Page Application (SPA)** with TypeScript. The frontend communicates with the backend exclusively through REST API endpoints, enabling independent development, deployment, and scaling.

**Frontend Location**: `frontend/` (project root directory)

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

The application frontend by default uses the English language, however it also supports Hungarian language.

For translation support [vue3-gettext](https://github.com/jshmrtn/vue3-gettext) is used.

1. To update the English .pot file with new translatable strings use `make lang`.
```shell
$ make lang
```
2. Create or edit the .po file to add translations by a tool like `poedit`.
```shell
$ poedit frontend/src/locales/en/LC_MESSAGES/messages.po
```
3. Compile the .po file into a .mo file. (`poedit` will do this for you):
```bash
$ msgfmt frontend/src/locales/en/LC_MESSAGES/messages.po -o frontend/src/locales/en/LC_MESSAGES/messages.mo
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
