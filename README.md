# whatsthedamage

An opinionated tool written in Python to process K&H HU's bank account transaction exports in CSV files.

The predefined settings works best with CSVs exported from K&H HU, but I made efforts to customize the behavior and potentially work with any other CSV format other finance companies may produce.

The project contains a web interface using Flask.

## Why?

I tried some self-hosted software like [Firefly III](https://www.firefly-iii.org/) and [Actualbudget](https://actualbudget. to create detailed reports about my accounting. However, I found that either the learning curve is too high or the burden of manually categorizing transactions is too great.

I wanted something much simpler to use that still provides the required details and works with transaction exports that one can download from their online banking.

## The name

The slang phrase "what's the damage?" is often used to ask about the cost or price of something, typically in a casual or informal context. The phrase is commonly used in social settings, especially when discussing expenses or the results of an event.

## Features:
 - Categorizes transactions into well known accounting categories like deposits, payments, etc.
 - Categorizes transactions into custom categories by using regular expressions.
 - Transactions can be filtered by start and end dates. If no filer is set then groupping is based on the number of month.
 - Shows a report about the summarized amounts grouped by transaction categories.
 - Reports can be saved as CSV file as well.

Example output on console. The values in the following example are arbitrary.
```
                          január          február
balance            129.576,00 Ft  1.086.770,00 Ft
cars              -106.151,00 Ft    -54.438,00 Ft
clothes            -14.180,00 Ft          0,00 Ft
deposits           725.313,00 Ft  1.112.370,00 Ft
fees                -2.494,00 Ft     -2.960,00 Ft
grocery           -172.257,00 Ft   -170.511,00 Ft
health             -12.331,00 Ft    -25.000,00 Ft
home_maintenance         0,00 Ft    -43.366,00 Ft
interest                 5,00 Ft          8,00 Ft
loan               -59.183,00 Ft    -59.183,00 Ft
other              -86.411,00 Ft    -26.582,00 Ft
payments           -25.500,00 Ft    583.580,00 Ft
refunds                890,00 Ft        890,00 Ft
transfers                0,00 Ft          0,00 Ft
utilities          -68.125,00 Ft    -78.038,00 Ft
withdrawals        -50.000,00 Ft   -150.000,00 Ft

```
## Install

Use `pipx install .` to deploy the package.

## Usage:
```
usage: whatsthedamage [-h] [--start-date START_DATE] [--end-date END_DATE] [--verbose] [--version] [--config CONFIG] [--category CATEGORY] [--no-currency-format] [--output OUTPUT]
                      [--output-format OUTPUT_FORMAT] [--nowrap] [--filter FILTER]
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
  --config CONFIG, -c CONFIG
                        Path to the configuration file. (default: config.json.default)
  --category CATEGORY   The attribute to categorize by. (default: category)
  --no-currency-format  Disable currency formatting. Useful for importing the data into a spreadsheet.
  --output OUTPUT, -o OUTPUT
                        Save the result into a CSV file with the specified filename.
  --output-format OUTPUT_FORMAT
                        Supported formats are: html, csv. (default: csv).
  --nowrap, -n          Do not wrap the output text. Useful for viewing the output without line wraps.
  --filter FILTER, -f FILTER
                        Filter by category. Use it conjunction with --verbose.

```

## Things which need attention

- The categorization process may fail to categories transactions because of the quality of the regular expressions. In such situations the transaction will be categorized as 'other'.
- The configured locale (default to Hungarian) sets the currency format (HUF). The tool assumes that accounts exports only use a single currency.

### Configuration File (config.json):

The configuration file must contain 'csv', 'main' and 'enricher_pattern_sets' keys with the following structure:
```json
{
  "csv": {
    "dialect": "excel-tab",
    "delimiter": "\t",
    "date_attribute_format": "%Y.%m.%d",
    "attribute_mapping": {
      "date": "könyvelés dátuma",
      "type": "típus",
      "partner": "partner elnevezése",
      "amount": "összeg",
      "currency": "összeg devizaneme"
    }
  },
  "main": {
    "locale": "hu_HU.UTF-8",
  },
  "enricher_pattern_sets": {
    "partner": {
      "grocery": [
        "bolt.*",
        "abc.*",
      ]
    },
    "type": {
      "loan": [
        "hitel.*",
        "késedelmi.*"
      ],
    }
  }
}
```

A default configuration file is provied as `config.json.default`. The installed package installs it to `<venv>/whatsthedamage/share/doc/whatsthedamage/config.json.default`.

## Troubleshooting
In case you want to troubleshoot why a certain transaction got into a specific category, turn on verbose mode by setting either `-v` or `--verbose` on the command line.  
By default only those attributes (columns) are printed which are set in `selected_attributes`. The attribute `category` is created by the tool.

Should you want to check your regular expressions then you can use use a handy online tool like https://regex101.com/.

Note: Regexp values are not stored as raw strings, so watch out for possible backslashes. For more information, see [What exactly is a raw string regex and how can you use it?](https://stackoverflow.com/questions/12871066/what-exactly-is-a-raw-string-regex-and-how-can-you-use-it).

### Transaction categories

A list of frequent transaction categories a bank account may have.

- **Deposits**: Money added to the account, such as direct deposits from employers, cash deposits, or transfers from other accounts.
- **Withdrawals**: Money taken out of the account, including ATM withdrawals, cash withdrawals at the bank, and electronic transfers.
- **Purchases**: Transactions made using a debit card or checks to pay for goods and services.
- **Fees**: Charges applied by the bank, such as monthly maintenance fees, overdraft fees, or ATM fees.
- **Interest**: Earnings on the account balance, typically seen in savings accounts or interest-bearing checking accounts.
- **Transfers**: Movements of money between accounts, either within the same bank or to different banks.
- **Payments**: Scheduled payments for bills or loans, which can be set up as automatic payments.
- **Refunds**: Money returned to the account, often from returned purchases or corrections of previous transactions.

## Bugs

- Fix time skew issues:
  - The 'könyvelés dátuma' attribute is most likely in local time but converting into epoch assumes UTC. Without timezone information we can only guess.
  - The arguments `--start-date` and `--end-date` assumes hours, minutes and seconds to be 00:00:00 and not 23:59:59.
- Mixed localization. The month names are localized but the category names are not.