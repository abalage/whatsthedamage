# whatsthedamage

An opinionated open source tool written in Python to process K&H HU's bank account transaction exports in CSV files.

The predefined settings works best with CSVs exported from K&H HU, but I made efforts to customize the behavior and potentially work with any other CSV format other finance companies may produce.

The project contains a web interface using Flask.

## Why?

I tried some self-hosted software like [Firefly III](https://www.firefly-iii.org/) and [Actualbudget](https://actualbudget). to create detailed reports about my accounting. However, I found that either the learning curve is too high or the burden of manually categorizing transactions is too great.

I wanted something much simpler to use that still provides the required details and works with transaction exports that one can download from their online banking.

## The name

The slang phrase "what's the damage?" is often used to ask about the cost or price of something, typically in a casual or informal context. The phrase is commonly used in social settings, especially when discussing expenses or the results of an event.

## Features:
 - Categorizes transactions into well known accounting categories like deposits, payments, etc.
 - Categorizes transactions into custom categories by using regular expressions.
 - Transactions can be filtered by start and end dates. If no filter is set, grouping is based on the number of months.
 - Shows a report about the summarized amounts grouped by transaction categories.
 - Reports can be saved as CSV file as well.
 - Localization support. Currently English (default) and Hungarian languages are supported.
 - Web interface for easier use.

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
## Install

Use `pipx install .` to deploy the package.

## Usage:
```
usage: whatsthedamage [-h] [--start-date START_DATE] [--end-date END_DATE] [--verbose] [--version] [--config CONFIG] [--category CATEGORY] [--no-currency-format] [--output OUTPUT]
                      [--output-format OUTPUT_FORMAT] [--nowrap] [--filter FILTER] [--lang LANG]
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
                        Path to the configuration file. (default: config.yml.default)
  --category CATEGORY   The attribute to categorize by. (default: category)
  --no-currency-format  Disable currency formatting. Useful for importing the data into a spreadsheet.
  --output OUTPUT, -o OUTPUT
                        Save the result into a CSV file with the specified filename.
  --output-format OUTPUT_FORMAT
                        Supported formats are: html, csv. (default: csv).
  --nowrap, -n          Do not wrap the output text. Useful for viewing the output without line wraps.
  --filter FILTER, -f FILTER
                        Filter by category. Use it in conjunction with --verbose.
  --lang LANG, -l LANG  Language for localization.
```

## Web interface

Currently you can only run it locally by using Flask.
```bash
pip3 install -r requirements.txt
cd src/whatsthedamage
python3 -m flask run
```

Access the web interface on [http://0.0.0.0:5000](http://0.0.0.0:5000).

## Things which need attention

- The categorization process may fail to categorize transactions because of the quality of the regular expressions. In such situations the transaction will be categorized as 'other'.
- The tool assumes that account exports only use a single currency.

### Configuration File (config.yml):

The config file format and syntax has considerably changed in v0.6.0. Please refer to the default config file for details.

A default configuration file is provided as `config.yml.default`. The installed package installs it to `<venv>/whatsthedamage/share/doc/whatsthedamage/config.yml.default`.

## Troubleshooting
In case you want to troubleshoot why a certain transaction got into a specific category, turn on verbose mode by setting either `-v` or `--verbose` on the command line.  
By default only those attributes (columns) are printed which are set in `selected_attributes` in config file. The attribute `category` is created by the tool.

Should you want to check your regular expressions then you can use a handy online tool like https://regex101.com/.

Note: Regexp values are not stored as raw strings, so watch out for possible backslashes. For more information, see [What exactly is a raw string regex and how can you use it?](https://stackoverflow.com/questions/12871066/what-exactly-is-a-raw-string-regex-and-how-can-you-use-it).

### Transaction categories

A list of frequent transaction categories a bank account may have.

- **Deposit**: Money added to the account, such as direct deposits from employers, cash deposits, or transfers from other accounts.
- **Withdrawal**: Money taken out of the account, including ATM withdrawals, cash withdrawals at the bank, and electronic transfers.
- **Purchase**: Transactions made using a debit card or checks to pay for goods and services.
- **Fee**: Charges applied by the bank, such as monthly maintenance fees, overdraft fees, or ATM fees.
- **Interest**: Earnings on the account balance, typically seen in savings accounts or interest-bearing checking accounts.
- **Transfer**: Movements of money between accounts, either within the same bank or to different banks.
- **Payment**: Scheduled payments for bills or loans, which can be set up as automatic payments.
- **Refund**: Money returned to the account, often from returned purchases or corrections of previous transactions.

Custom categories (like "Vehicle", "Grocery", etc.) are user-defined via config, and the listed categories are just examples. Feel free to add your own categories into config.yml.

## Localization
Install `gettext` and `poedit`.

1. Extract translatable strings into a .pot file:
```bash
cd src/whatsthedamage
xgettext -o locale/en/LC_MESSAGES/messages.pot config/config.py utils/date_converter.py
```

2. Create a .po file for each language (e.g., Hungarian):
```bash
msginit -l en -o locale/en/LC_MESSAGES/messages.po --input locale/en/LC_MESSAGES/messages.pot
```

3. In case the file has been recently created make sure to change encoding from ASCII to UTF-8.
```bash
sed -i 's/ASCII/UTF-8/g' locale/en/LC_MESSAGES/messages.po
```

4. Edit the .po file to add translations (creates the .mo file upon Save):
```bash
poedit locale/en/LC_MESSAGES/messages.po
```

5. (optional) Compile the .po file into a .mo file. Poedit will do this for you:
```bash
msgfmt locale/en/LC_MESSAGES/messages.po -o locale/en/LC_MESSAGES/messages.mo
```

## Bugs, TODO

- Fix time skew issues:
  - The 'könyvelés dátuma' attribute is most likely in local time but converting into epoch assumes UTC. Without timezone information we can only guess.
  - The arguments `--start-date` and `--end-date` assumes hours, minutes and seconds to be 00:00:00 and not 23:59:59.
- A docker image is planned for the future to make it easier to start using it.

## Contributing

Contributions are welcome! If you have ideas for improvements, bug fixes, new features, or additional documentation, feel free to open an issue or submit a pull request.

To contribute:

1. **Fork the repository** and create your branch from `main`.
2. **Make your changes** with clear commit messages.
3. **Test your changes** to ensure nothing is broken.
4. **Open a pull request** describing your changes and the motivation behind them.

If you have questions or need help getting started, open an issue and we’ll be happy to assist.

Thank you for helping make this project better!
