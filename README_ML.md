# Use Machine Learning for Predicting Categories

EXPERIMENTAL FEATURE

Multi-class transaction classifier.

## The Model

The model is a multi-class classification model implemented by using [Random Forest Classifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html) trained on 11,769 transaction data points spanning over 14 years.

It predicts the category of bank transactions. Its goal is to replace the "hard-to-maintain" regexp-based approach.

The machine-learning library in `whatsthedamage` uses [scikit-learn 1.7.2](https://scikit-learn.org/stable).

## Architecture Overview

The ML module follows a layered architecture:

- **Controllers**: `ml_cli.py` - Command-line interface handling
- **Services**: `MLService` - Business logic and orchestration
- **Models**: Machine learning classes (`Train`, `Inference`, `Metrics`, `TrainingData`)
- **Configuration**: `MLConfig` - Centralized configuration management

This separation of concerns makes the system more maintainable and testable.

### Feature Engineering

The following transformers are used for feature engineering, also referenced in the source code as feature columns:

1. `type`:
   - Transformation: [TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
   - Description: Text feature representing the transaction type, processed with TF-IDF and Hungarian stop words.

2. `partner`:
   - Transformation: [TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
   - Description: Text feature representing the transaction partner, processed with TF-IDF and custom stop words. The text undergoes ML-specific cleaning using the self-contained `TextCorrectionService` for consistent preprocessing.

3. `amount`:
   - Transformation: `AmountSignTransformer` (custom transformer)
   - Description: Categorical feature extracting the sign (positive/negative/zero) from transaction amounts, representing the direction of cash flow.

### Hyperparameter Tuning

The machine learning library in `whatsthedamage` provides support for hyperparameter tuning when training your transaction categorization model. It could help to find the best model parameters for improved accuracy and generalization.

You can choose between two popular hyperparameter search strategies:

- **Grid Search (`GridSearchCV`)**: Exhaustively tests all combinations of specified parameter values.
- **Randomized Search (`RandomizedSearchCV`)**: Randomly samples parameter combinations, which can be faster for large search spaces.

By default the following Random Forest parameters are tuned by default:

- `n_estimators`: Number of trees in the forest (e.g., 50, 100, 200)
- `max_depth`: Maximum depth of the trees (e.g., None, 10, 20, 30)
- `min_samples_split`: Minimum number of samples required to split a node (e.g., 2, 5, 10)

You can customize these in the [MLConfig](../config/ml_config.py) class if needed.

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

### Model Evaluation with Metrics Class

The `Metrics` class provides comprehensive model evaluation capabilities beyond basic accuracy metrics.

**Important Note on Data Splitting:**
The `Metrics` class evaluates performance on **unseen test data only** to prevent data leakage and overfitting. The `Train` class automatically exports test data to `MLConfig.test_data_path` during training, so you don't need to manually export it.

#### Features:

1. **Accuracy & Classification Report**: Standard scikit-learn metrics
2. **Confusion Matrix**: With automatic class abbreviation generation for readability
3. **Confused Pairs Analysis**: Identifies the most frequently misclassified category pairs
4. **Confidence Analysis**: 
   - Low confidence errors (confidence < 0.7)
   - High confidence errors (confidence ≥ 0.9) - potential data issues
5. **Merchant Error Analysis**: Top 10 merchants causing classification errors
6. **Automatic Test Set Validation**: Warns about small or imbalanced test sets

#### Usage:

```bash
$ python3 src/whatsthedamage/controllers/ml_cli.py metrics --model <MODEL_PATH> --data <TEST_DATA_JSON_PATH>
```

The metrics command generates a detailed report including:
- Overall accuracy score
- Confusion matrix with class abbreviations
- Full classification report
- Table of most confused category pairs
- Analysis of low and high confidence errors
- Top merchants causing classification errors

#### Test Set Requirements:

For reliable metrics, your test set should:
- **Contain only unseen data** (never used in training)
- **Have at least 100-200 samples** (minimum 50 for basic evaluation)
- **Include 5-10+ samples per class** for meaningful per-class metrics
- **Be representative** of your real-world data distribution

If your test set is too small, the `Metrics` class will warn you and suggest improvements.

### Manifest

After training, a manifest JSON is saved with metadata (model version, parameters, feature info).

Example manifest: [model-rf-v6alpha_en.manifest.json](../static/model-rf-v6alpha_en.manifest.json)

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

### Usage of 'ml_cli.py' Script

The script `ml_cli.py` uses `whatsthedamage`'s machine-learning API to train ML models, make predictions, and calculate comprehensive evaluation metrics.

Features:

- Automated categorization of transactions using the trained model.
- Hyperparameter tuning can optionally be done via GridSearchCV or RandomizedSearchCV.
- Comprehensive model evaluation with the new Metrics class.
- Prediction confidence scores can optionally be printed during inference.

Usage:

```bash
$ python3 src/whatsthedamage/controllers/ml_cli.py train <TRAINING_DATA_JSON_PATH>
$ python3 src/whatsthedamage/controllers/ml_cli.py predict <MODEL_PATH> <TEST_DATA_JSON_PATH>
$ python3 src/whatsthedamage/controllers/ml_cli.py metrics --model <MODEL_PATH> --data <TEST_DATA_JSON_PATH>
```

```bash
$ python3 src/whatsthedamage/controllers/ml_cli.py -h
usage: ml_cli.py [-h] {train,predict,metrics} ...

Train or test transaction categorizer model (modular version).

positional arguments:
  {train,predict,metrics}
    train          Train the model
    predict        Predict categories for new data
    metrics        Calculate model evaluation metrics

options:
  -h, --help       show this help message and exit

$ python3 src/whatsthedamage/controllers/ml_cli.py train -h
usage: ml_cli.py train [-h] [--gridsearch] [--randomsearch] [--verbose] training_data

positional arguments:
  training_data    Path to training data JSON file

options:
  -h, --help       show this help message and exit
  --gridsearch     Use GridSearchCV for hyperparameter tuning
  --randomsearch   Use RandomizedSearchCV for hyperparameter tuning
  --verbose, -v    Enable verbose output during training

$ python3 src/whatsthedamage/controllers/ml_cli.py predict -h
usage: ml_cli.py predict [-h] [--confidence] model new_data

positional arguments:
  model         Path to trained model file
  new_data      Path to new data JSON file

options:
  -h, --help    show this help message and exit
  --confidence  Show prediction confidence scores and verbose data

$ python3 src/whatsthedamage/controllers/ml_cli.py metrics -h
usage: ml_cli.py metrics [-h] [--model MODEL] [--data DATA] [--verbose]

options:
  -h, --help           show this help message and exit
  --model MODEL        Path to trained model file
  --data DATA          Path to test data JSON file
  --verbose, -v        Enable verbose output during metrics calculation
```

## Model Improvement and Troubleshooting

The comprehensive metrics provided by the `Metrics` class can help identify areas for model improvement:

### Proper Data Splitting Strategies

**Why unseen test data is essential:**
- Evaluating on training data causes **overfitting** and **overly optimistic metrics**
- Unseen test data provides **unbiased performance estimates**
- This is fundamental to proper ML evaluation methodology

**Recommended approaches:**

1. **Using Train Class** (recommended):
   The `Train` class handles everything in one streamlined operation - training, saving the model, manifest, and automatically exporting test data:
   ```bash
   # Train and save everything automatically (model, manifest, and test data)
   python3 src/whatsthedamage/controllers/ml_cli.py train your_full_data.json
   
   # For programmatic use:
   python3 -c "
   from whatsthedamage.models.machine_learning import Train, TrainingData, Metrics
   from whatsthedamage.config.ml_config import MLConfig
   
   config = MLConfig()
   training_data = TrainingData('your_full_data.json', config)
   train = Train(training_data=training_data, config=config)
   train.train()  # Automatically saves model, manifest, AND test data
   
   # All files are now available at MLConfig paths
   # Immediately evaluate using the automatically saved test data
   metrics = Metrics(config.model_path, config.test_data_path)
   print(f'Accuracy: {metrics.get_metrics_data()[\"accuracy\"]}')
   "

2. **Manual Splitting** (for full control):
   ```python
   from sklearn.model_selection import train_test_split
   import pandas as pd
   
   # Load your full dataset
   full_data = pd.read_json('full_data.json')
   
   # Split into training and test sets
   train_df, test_df = train_test_split(
       full_data, 
       test_size=0.2, 
       random_state=42,
       stratify=full_data['category']  # Maintain class distribution
   )
   
   # Save the splits
   train_df.to_json('train_data.json', orient='records')
   test_df.to_json('test_data.json', orient='records')
   
   # Train and evaluate
   python3 src/whatsthedamage/controllers/ml_cli.py train train_data.json
   python3 src/whatsthedamage/controllers/ml_cli.py metrics --model model.joblib --data test_data.json
   ```

3. **For Small Datasets** (<1000 samples):
   - Use **cross-validation** during training
   - Still hold out a small test set (10-20%) for final evaluation
   - Consider collecting more data if possible

**Pro Tip:** Always use `random_state` for reproducible splits!

### Interpreting Confidence Analysis

- **Low Confidence Errors** (confidence < 0.7): These transactions are genuinely ambiguous and may require:
  - Additional features to better distinguish between categories
  - Manual review and potential category reassignment
  - Rule-based post-processing for specific edge cases

- **High Confidence Errors** (confidence ≥ 0.9): These indicate potential data quality issues:
  - Incorrect labels in the training data
  - Inconsistent category naming conventions
  - Transactions that should be excluded from training

### Using Merchant Analysis

The top merchants causing classification errors can help identify:
- Merchants that span multiple categories (e.g., large retailers)
- Data quality issues with specific merchant names
- Opportunities for merchant-specific rules or preprocessing

### Best Practices for Model Improvement

1. **Review Confused Pairs**: Focus on the most frequently misclassified category pairs
2. **Analyze High Confidence Errors**: These often indicate labeling issues
3. **Examine Merchant Patterns**: Identify merchants that consistently cause problems
4. **Iterative Training**: Use metrics to guide feature engineering and data cleaning
5. **Combine Approaches**: Use ML predictions as a starting point, then apply rule-based refinements

## Bugs

The whole ML feature is currently in the experimental phase. If you find any bugs or have suggestions, feel free to open an issue or contact me.