# Use Machine Learning for Predicting Categories

EXPERIMENTAL FEATURE

## The Model

The model is a [Random Forest Classifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html) trained on 11,769 transaction data points spanning over 14 years.

It predicts the category of bank transactions. Its goal is to replace the "hard-to-maintain" regexp-based approach.

The machine-learning library in `whatsthedamage` uses [scikit-learn 1.7.2](https://scikit-learn.org/stable).

### Feature Engineering

The following transformers are used for feature engineering, also referenced in the source code as feature columns:

1. `type`:
   - Transformation: [TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
   - Description: Text feature representing the transaction type, processed with TF-IDF and Hungarian stop words.

2. `partner`:
   - Transformation: [TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
   - Description: Text feature representing the transaction partner, processed with TF-IDF and custom stop words.

3. `currency`:
   - Transformation: [OneHotEncoder](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html)
   - Description: Categorical feature for the currency, one-hot encoded.

4. `amount`:
   - Transformation: [StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)
   - Description: Numerical feature for the transaction amount, standardized.

### Hyperparameter Tuning

The machine learning library in `whatsthedamage` provides support for hyperparameter tuning when training your transaction categorization model. It could help to find the best model parameters for improved accuracy and generalization.

You can choose between two popular hyperparameter search strategies:

- **Grid Search (`GridSearchCV`)**: Exhaustively tests all combinations of specified parameter values.
- **Randomized Search (`RandomizedSearchCV`)**: Randomly samples parameter combinations, which can be faster for large search spaces.

By default the following Random Forest parameters are tuned by default:

- `n_estimators`: Number of trees in the forest (e.g., 50, 100, 200)
- `max_depth`: Maximum depth of the trees (e.g., None, 10, 20, 30)
- `min_samples_split`: Minimum number of samples required to split a node (e.g., 2, 5, 10)

You can customize these in the [MLConfig](../models/machine_learning.py) class if needed.

Note, that hyperparameter tuning may take longer than standard training, depending on dataset size and parameter ranges.

### Accuracy

The 'v5alpha_en' model's accuracy is shown below:

```
Model Evaluation Metrics:
Accuracy: 0.9855564995751912
                   precision    recall  f1-score   support

          Clothes       1.00      0.99      0.99        83
          Deposit       1.00      0.99      1.00       159
              Fee       1.00      1.00      1.00       323
          Grocery       0.99      0.99      0.99       697
           Health       1.00      1.00      1.00        67
 Home Maintenance       0.94      0.94      0.94        94
        Insurance       1.00      0.88      0.93         8
         Interest       0.98      1.00      0.99        64
             Loan       1.00      0.96      0.98        24
            Other       0.94      0.97      0.96       325
          Payment       1.00      1.00      1.00        81
           Refund       1.00      1.00      1.00        48
Sports Recreation       1.00      0.94      0.97        36
         Transfer       0.98      0.98      0.98        47
          Utility       0.99      0.98      0.99       161
          Vehicle       1.00      0.97      0.99       108
       Withdrawal       0.97      1.00      0.98        29

         accuracy                           0.99      2354
        macro avg       0.99      0.98      0.98      2354
     weighted avg       0.99      0.99      0.99      2354
```

### Manifest

After training, a manifest JSON is saved with metadata (model version, parameters, feature info).

Example manifest: [model-rf-v5alpha_en.manifest.json](../static/model-rf-v5alpha_en.manifest.json)

## How to Train the Model on Your Data

The app `whatsthedamage` provides a CLI option `--training-data` to print transactions to STDERR categorized by the existing regexp-based enrichment. If you redirect STDERR into a file, you will have all transactions in a JSON file, which can be directly provided to the machine learning script (`ml_util.py`).

It is highly recommended to match the `--language` setting with the language of the data used for inference, as currently the model learns the category names as-is.

This might change in the future.

### Training Data Structure

Data objects are based on [CsvRow](../models/csv_row.py) objects.

Example:
```json
[
  {
    "amount": -11111,
    "category": "Loan",
    "currency": "HUF",
    "partner": "",
    "type": "Hitel törlesztés"
  },
  {
    "amount": -22222,
    "category": "Loan",
    "currency": "HUF",
    "partner": "",
    "type": "Hitelkamat törlesztés"
  }
]
```

### Usage of 'ml_util.py' Script

The script `ml_util.py` uses `whatsthedamage`'s machine-learning API to train ML models and provide basic category prediction features.

Features:

- Automated categorization of transactions using the trained model.
- Hyperparameter tuning can optionally be done via GridSearchCV or RandomizedSearchCV.
- Provides model evaluation.
- Prediction confidence scores can optionally be printed during inference.

Usage:

```bash
$ python3 src/whatsthedamage/scripts/ml_util.py train <TRAINING_DATA_JSON_PATH>
$ python3 src/whatsthedamage/scripts/ml_util.py predict <MODEL_PATH> <TEST_DATA_JSON_PATH>
```

```bash
$ python3 src/whatsthedamage/scripts/ml_util.py -h
usage: ml_util.py [-h] {train,predict} ...

Train or test transaction categorizer model (modular version).

positional arguments:
  {train,predict}
    train          Train the model
    predict        Predict categories for new data

options:
  -h, --help       show this help message and exit

$ python3 src/whatsthedamage/scripts/ml_util.py train -h
usage: ml_util.py train [-h] [--gridsearch] [--randomsearch] [--verbose] [--output OUTPUT] training_data

positional arguments:
  training_data    Path to training data JSON file

options:
  -h, --help       show this help message and exit
  --gridsearch     Use GridSearchCV for hyperparameter tuning
  --randomsearch   Use RandomizedSearchCV for hyperparameter tuning
  --verbose, -v    Enable verbose output during training
  --output OUTPUT  Output directory for trained model (auto-generated if not exists)

$ python3 src/whatsthedamage/scripts/ml_util.py predict -h
usage: ml_util.py predict [-h] [--confidence] model new_data

positional arguments:
  model         Path to trained model file
  new_data      Path to new data JSON file

options:
  -h, --help    show this help message and exit
  --confidence  Show prediction confidence scores and verbose data
```

## Bugs

The whole ML feature is currently in the experimental phase. If you find any bugs or have suggestions, feel free to open an issue or contact me.