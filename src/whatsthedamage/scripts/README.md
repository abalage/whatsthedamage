# Use Machine Learning for predicting categories

EXPERIMENTAL

A script using scikit-learn to train ML models to predict categories.

## Usage

```bash
python3 src/whatsthedamage/scripts/train_module.py train <TRAINING_DATA_JSON_PATH>
python3 src/whatsthedamage/scripts/train_module.py predict <MODEL_PATH> <TEST_DATA_JSON_PATH>
```

## Example data structure for training and test data

Output is based on CsvRow objects.

```json
[
  {
    "amount": -38042,
    "category": "Loan",
    "currency": "HUF",
    "partner": "",
    "type": "Hitel törlesztés"
  },
  {
    "amount": -21141,
    "category": "Loan",
    "currency": "HUF",
    "partner": "",
    "type": "Hitelkamat törlesztés"
  }
]
```

