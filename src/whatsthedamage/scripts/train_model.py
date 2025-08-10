import sys
import json
import argparse
import pandas as pd
from typing import List, Any, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV
from sklearn.metrics import classification_report, accuracy_score
import joblib
from datetime import datetime

# Constants for RandomForestClassifier
CLASSIFIER_SHORT_NAME: str = "rf"
RANDOM_STATE: int = 42
MIN_SAMPLES_SPLIT: int = 10
N_ESTIMATORS: int = 200

# Hungarian stop words for type and partner fields
# Make sure that stop words are lowercase and unicode stripped to match TfidfVectorizer's settings.
HUNGARIAN_TYPE_STOP_WORDS: List[str] = [
    "ft", "forint", "bol"
]

HUNGARIAN_PARTNER_STOP_WORDS: List[str] = [
    "es", "bt", "kft", "zrt", "rt", "nyrt", "ev", "korlatolt", "felelossegu",
    "tarsasag", "alapitvany", "kisker", "szolgaltato", "kereskedelmi",
    "kereskedes", "sz", "u.", "utca", "ut", "&", "huf", "otpmobl", "paypal",
    "crv", "sumup", "www"
]

# Some stop words are excluded on purpose
# "iskola", "bolt", "étterem", "cukrászda", "gyógyszertár", "patika",
# "abc", "market", "biztosító", "bank", "posta", "dr"


def load_json_data(filepath: str) -> Any:
    """Loads JSON data from a file and handles errors."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON file '{filepath}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred while reading '{filepath}': {e}")
        sys.exit(1)


def validate_and_clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate required columns, check for emptiness, and drop missing values."""
    required_columns: set[str] = {"type", "partner", "currency", "amount", "category"}
    missing_columns: set[str] = required_columns - set(df.columns)
    if missing_columns:
        print(f"Error: Missing required columns: {', '.join(missing_columns)}")
        sys.exit(1)
    if df.empty:
        print("Error: Loaded DataFrame is empty.")
        sys.exit(1)
    if df.isnull().any().any():
        print("Warning: Data contains missing values. Dropping rows with missing values.")
        df = df.dropna()
        if df.empty:
            print("Error: All rows were dropped due to missing values.")
            sys.exit(1)
    return df


def get_preprocessor() -> ColumnTransformer:
    """Return the feature engineering pipeline."""
    return ColumnTransformer(
        transformers=[
            ("type_tfidf", TfidfVectorizer(
                lowercase=True,
                strip_accents='unicode',
                stop_words=HUNGARIAN_TYPE_STOP_WORDS),
                "type"),
            ("partner_tfidf", TfidfVectorizer(
                lowercase=True,
                strip_accents='unicode',
                ngram_range=(1, 1),
                stop_words=HUNGARIAN_PARTNER_STOP_WORDS),
                "partner"),
            ("currency_ohe", OneHotEncoder(handle_unknown="ignore"), ["currency"]),
            ("amount_scaler", StandardScaler(), ["amount"]),
        ]
    )


def get_pipeline(preprocessor: ColumnTransformer) -> Pipeline:
    """Return the full model pipeline."""
    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            random_state=RANDOM_STATE,
            min_samples_split=MIN_SAMPLES_SPLIT,
            n_estimators=N_ESTIMATORS))
    ])


def train_model(
    pipe: Pipeline,
    df_train: pd.DataFrame,
    y_train: pd.Series,
    args: argparse.Namespace
) -> Any:
    """Train the model, optionally with hyperparameter search."""
    param_grid: Dict[str, List[Any]] = {
        "classifier__n_estimators": [50, 100, 200],
        "classifier__max_depth": [None, 10, 20, 30],
        "classifier__min_samples_split": [2, 5, 10],
    }
    param_dist: Dict[str, List[Any]] = param_grid.copy()
    if args.gridsearch:
        print("Using GridSearchCV for hyperparameter tuning...")
        grid_search: GridSearchCV = GridSearchCV(pipe, param_grid, cv=3, n_jobs=-1)
        grid_search.fit(df_train, y_train)
        print("Best parameters:", grid_search.best_params_)
        return grid_search.best_estimator_
    elif args.randomsearch:
        print("Using RandomizedSearchCV for hyperparameter tuning...")
        random_search: RandomizedSearchCV = RandomizedSearchCV(
            pipe, param_dist, n_iter=10, cv=3, n_jobs=-1, random_state=RANDOM_STATE)
        random_search.fit(df_train, y_train)
        print("Best parameters:", random_search.best_params_)
        return random_search.best_estimator_
    else:
        pipe.fit(df_train, y_train)
        return pipe


def evaluate_model(model: Pipeline, df_test: pd.DataFrame, y_test: pd.Series) -> None:
    """Evaluate the model and print metrics."""
    y_pred: Any = model.predict(df_test)
    print("\nModel Evaluation Metrics:")
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print(classification_report(y_test, y_pred))


def save_model(model: Pipeline, output_path: str) -> None:
    """Save the trained model to disk."""
    try:
        joblib.dump(model, output_path)
        print(f"Model training complete and saved as {output_path}")
    except Exception as e:
        print(f"Error: Failed to save model to '{output_path}': {e}")
        sys.exit(1)


def get_model_filename() -> str:
    """Generate a unique model filename based on timestamp."""
    now = datetime.now().strftime("%Y%m%d_%H%M")
    return f"model_{CLASSIFIER_SHORT_NAME}_{now}.joblib"


def save_manifest(manifest: dict, manifest_path: str) -> None:
    """Save manifest metadata as JSON."""
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"Manifest saved as {manifest_path}")
    except Exception as e:
        print(f"Error: Failed to save manifest to '{manifest_path}': {e}")


def predict_new_data(model_path: str, data_path: str) -> None:
    """Load model and new data, predict categories and confidence, print results."""

    # Load the trained pipeline
    try:
        model = joblib.load(model_path)
    except Exception as e:
        print(f"Error: Failed to load model from '{model_path}': {e}")
        sys.exit(1)

    # Load new transactions
    new_data = load_json_data(data_path)

    df_new = pd.DataFrame(new_data)

    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', 130)
    pd.set_option('display.expand_frame_repr', False)

    # Predict categories
    predicted_categories = model.predict(df_new)

    # Get prediction probabilities (confidence)
    proba = model.predict_proba(df_new)
    confidence = proba.max(axis=1)

    df_new["predicted_category"] = predicted_categories
    df_new["prediction_confidence"] = confidence.round(2)

    print(df_new[["type", "partner", "amount", "currency", "category", "predicted_category", "prediction_confidence"]])


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Train or test transaction categorizer model."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Train subcommand
    train_parser = subparsers.add_parser("train", help="Train the model")
    train_parser.add_argument("training_data", help="Path to training data JSON file")
    train_parser.add_argument("--metrics", action="store_true", help="Print evaluation metrics")
    train_parser.add_argument("--gridsearch", action="store_true", help="Use GridSearchCV for hyperparameter tuning") # noqa
    train_parser.add_argument("--randomsearch", action="store_true", help="Use RandomizedSearchCV for hyperparameter tuning") # noqa
    train_parser.add_argument("--output", help="Output path for trained model (auto-generated if not set)")

    # Predict subcommand
    predict_parser = subparsers.add_parser("predict", help="Predict categories for new data")
    predict_parser.add_argument("model", help="Path to trained model file")
    predict_parser.add_argument("new_data", help="Path to new data JSON file")

    args: argparse.Namespace = parser.parse_args()

    if args.command == "train":
        data: Any = load_json_data(args.training_data)
        df: pd.DataFrame = pd.DataFrame(data)
        df = validate_and_clean_data(df)
        y: pd.Series = df["category"]

        if args.metrics:
            df_train, df_test, y_train, y_test = train_test_split(
                df, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y)
        else:
            df_train = df
            y_train = y
            df_test = None
            y_test = None

        preprocessor: ColumnTransformer = get_preprocessor()
        X_train: Any = preprocessor.fit_transform(df_train)
        print(f"Feature matrix shape after preprocessing: {X_train.shape}")

        pipe: Pipeline = get_pipeline(preprocessor)
        model: Pipeline = train_model(pipe, df_train, y_train, args)

        if args.metrics and df_test is not None and y_test is not None:
            evaluate_model(model, df_test, y_test)

        # Generate model filename if not provided
        model_filename = args.output if args.output else get_model_filename()
        save_model(model, model_filename)

        manifest = {
            "model_file": model_filename,
            "training_data": args.training_data,
            "training_date": datetime.now().isoformat(),
            "parameters": {
                "classifier_short_name": CLASSIFIER_SHORT_NAME,
                "random_state": RANDOM_STATE,
                "min_samples_split": MIN_SAMPLES_SPLIT,
                "n_estimators": N_ESTIMATORS,
            },
            "data_info": {
                "row_count": len(df),
                "num_features": X_train.shape[1],
                "columns": [
                    # Only columns used in ColumnTransformer
                    "type", "partner", "currency", "amount"
                ],
            }
        }
        manifest_filename = model_filename.replace(".joblib", ".manifest.json")
        save_manifest(manifest, manifest_filename)

    elif args.command == "predict":
        predict_new_data(args.model, args.new_data)


if __name__ == "__main__":
    main()
