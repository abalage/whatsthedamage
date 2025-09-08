import sys
import json
import pandas as pd
from typing import List, Any, Dict, Union
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV
from sklearn.metrics import classification_report, accuracy_score
import joblib
from whatsthedamage.models.csv_row import CsvRow
from pydantic import BaseModel
from datetime import datetime
import os


def load_json_data(filepath: str) -> Any:
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


def save(model: Pipeline, output_dir: str, manifest: Dict[str, Any]) -> None:
    """Save the trained model and its manifest metadata to disk in the specified directory."""
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    model_filename = f"model-{ml_config.classifier_short_name}-{ml_config.model_version}.joblib"
    model_save_path = os.path.join(output_dir, model_filename)
    model_manifest_save_path = os.path.join(
        output_dir, model_filename.replace(".joblib", ".manifest.json")
    )

    try:
        joblib.dump(model, model_save_path)
        print(f"Model training complete and saved as {model_save_path}")
    except Exception as e:
        print(f"Error: Failed to save model to '{model_save_path}': {e}")
        sys.exit(1)

    try:
        with open(model_manifest_save_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"Manifest saved as {model_manifest_save_path}")
    except Exception as e:
        print(f"Error: Failed to save manifest to '{model_manifest_save_path}': {e}")


def load(model_path: str) -> Pipeline:
    """Load a model from disk."""
    try:
        model = joblib.load(model_path)
    except Exception as e:
        print(f"Error: Failed to load model from '{model_path}': {e}")
        sys.exit(1)

    return model


class MLConfig(BaseModel):
    hungarian_type_stop_words: List[str] = [
        "ft", "forint", "bol"
    ]
    hungarian_partner_stop_words: List[str] = [
        "es", "bt", "kft", "zrt", "rt", "nyrt", "ev", "korlatolt", "felelossegu",
        "tarsasag", "alapitvany", "kisker", "szolgaltato", "kereskedelmi",
        "kereskedes", "sz", "u.", "utca", "ut", "&", "huf", "otpmobl", "paypal",
        "crv", "sumup", "www"
    ]
    classifier_short_name: str = "rf"
    classifier_imbalance_threshold: float = 0.2
    random_state: int = 42
    min_samples_split: int = 10
    n_estimators: int = 200
    test_size: float = 0.2
    model_version: str = "v2alpha"
    model_path: str = "src/whatsthedamage/static/model-{short}-{ver}.joblib".format(
        short=classifier_short_name, ver=model_version
    )
    manifest_path: str = "src/whatsthedamage/static/model-{short}-{ver}.manifest.json".format(
        short=classifier_short_name, ver=model_version
    )
    feature_columns: List[str] = ["type", "partner", "currency", "amount"]


# Singleton instance of MLConfig
ml_config = MLConfig()


class TrainingData:
    def __init__(self, training_data_path: str):
        self.required_columns: set[str] = set(ml_config.feature_columns)
        raw_data = load_json_data(training_data_path)
        df = pd.DataFrame(raw_data)
        self._df = self._validate_and_clean_data(df)

    def _validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        missing_columns: set[str] = self.required_columns - set(df.columns)
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

    def get_training_data(self) -> pd.DataFrame:
        return self._df


class Train:
    """Prepare data and pipeline for model training."""
    def __init__(self, training_data_path: str, output: str = ""):
        self.training_data_path = training_data_path
        self.output = output
        self.model_save_path = self.output if self.output else ml_config.model_path
        self.config = ml_config
        self.class_weight = None

        # Load and validate data
        tdo = TrainingData(self.training_data_path)
        print(f"Loaded {len(tdo.get_training_data())} rows from {self.training_data_path}")

        self.df: pd.DataFrame = tdo.get_training_data()
        self.y: pd.Series = self.df["category"]

        # Always split data to prevent Data Leakage
        self.df_train, self.df_test, self.y_train, self.y_test = train_test_split(
            self.df, self.y, test_size=self.config.test_size, random_state=self.config.random_state, stratify=self.y
        )

        # Optionally, set class_weight if imbalance is detected
        class_counts = self.y_train.value_counts(normalize=True)
        if class_counts.min() < self.config.classifier_imbalance_threshold:
            print("Warning: Class imbalance detected. Setting class_weight='balanced' for classifier.")
            # Print class distribution
            print("Class distribution in training set:")
            print(self.y_train.value_counts())
            self.class_weight = "balanced"

        # Prepare feature columns
        self.X_train = self.df_train[self.config.feature_columns]
        self.X_test = self.df_test[self.config.feature_columns]

        # Prepare preprocessor and pipeline
        self.preprocessor: ColumnTransformer = self.get_preprocessor()
        self.pipe: Pipeline = self.get_pipeline()
        self.model: Pipeline = self.pipe

    def get_preprocessor(self) -> ColumnTransformer:
        """Return the feature engineering pipeline."""
        self.preprocessor = ColumnTransformer(
            transformers=[
                ("type_tfidf", TfidfVectorizer(
                    lowercase=True,
                    strip_accents='unicode',
                    stop_words=self.config.hungarian_type_stop_words),
                    "type"),
                ("partner_tfidf", TfidfVectorizer(
                    lowercase=True,
                    strip_accents='unicode',
                    ngram_range=(1, 1),
                    stop_words=self.config.hungarian_partner_stop_words),
                    "partner"),
                ("currency_ohe", OneHotEncoder(handle_unknown="ignore"), ["currency"]),
                ("amount_scaler", StandardScaler(), ["amount"]),
            ]
        )
        return self.preprocessor

    def get_pipeline(self) -> Pipeline:
        """Return the full model pipeline."""
        preprocessor = self.get_preprocessor()
        classifier = RandomForestClassifier(
            random_state=self.config.random_state,
            min_samples_split=self.config.min_samples_split,
            n_estimators=self.config.n_estimators,
            class_weight=getattr(self, "class_weight", None)
        )
        return Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", classifier)
        ])

    def train(self) -> None:
        """Train the model, optionally with hyperparameter search."""
        pipe = self.get_pipeline()
        if self.X_train is None or self.y_train is None:
            raise ValueError("Training data (X_train or y_train) is None.")
        pipe.fit(self.X_train, self.y_train)
        self.model = pipe

        # Always evaluate if test data is available
        if self.df_test is not None and self.y_test is not None:
            self.evaluate()

        # Get processed feature matrix shape after fitting the pipeline
        processed_shape = self.model.named_steps["preprocessor"].transform(self.X_train).shape

        # Create MANIFEST after training and evaluation
        MANIFEST = {
            "model_file": self.model_save_path,
            "model_version": self.config.model_version,
            "training_data": self.training_data_path,
            "training_date": datetime.now().isoformat(),
            "parameters": {
                "classifier_short_name": self.config.classifier_short_name,
                "random_state": self.config.random_state,
                "min_samples_split": self.config.min_samples_split,
                "n_estimators": self.config.n_estimators
            },
            "data_info": {
                "row_count": len(self.df),
                "feature_matrix_shape": processed_shape,
                "test_size": self.config.test_size,
                "feature_columns": self.config.feature_columns,
            }
        }

        print(f"Feature matrix shape after preprocessing: {processed_shape}")

        save(self.model, self.model_save_path, MANIFEST)

    def hyperparameter_tuning(self, method: str) -> None:
        """Perform hyperparameter tuning."""
        pipe = self.get_pipeline()
        param_grid: Dict[str, List[Any]] = {
            "classifier__n_estimators": [50, 100, 200],
            "classifier__max_depth": [None, 10, 20, 30],
            "classifier__min_samples_split": [2, 5, 10],
        }
        param_dist: Dict[str, List[Any]] = param_grid.copy()
        if method == "grid":
            print("Using GridSearchCV for hyperparameter tuning...")
            grid_search: GridSearchCV = GridSearchCV(pipe, param_grid, cv=3, n_jobs=-1)
            if self.X_train is None or self.y_train is None:
                raise ValueError("Training data (X_train or y_train) is None.")
            grid_search.fit(self.X_train, self.y_train)
            print("Best parameters:", grid_search.best_params_)
        elif method == "random":
            print("Using RandomizedSearchCV for hyperparameter tuning...")
            random_search: RandomizedSearchCV = RandomizedSearchCV(
                pipe, param_dist, n_iter=10, cv=3, n_jobs=-1, random_state=self.config.random_state)
            if self.X_train is None or self.y_train is None:
                raise ValueError("Training data (X_train or y_train) is None.")
            random_search.fit(self.X_train, self.y_train)
            print("Best parameters:", random_search.best_params_)
        else:
            print("No hyperparameter tuning method selected.")

    def evaluate(self) -> None:
        """Evaluate the model and print metrics."""
        if self.y_test is not None:
            y_pred: Any = self.model.predict(self.X_test)
            print("\nModel Evaluation Metrics:")
            print("Accuracy:", accuracy_score(self.y_test, y_pred))
            print(classification_report(self.y_test, y_pred))
        else:
            print("Error: y_test is None. Cannot evaluate model.")


class Inference:
    def __init__(self, new_data: Union[str, List[CsvRow]]) -> None:
        self.config = ml_config
        self.model: Pipeline = load(self.config.model_path)
        self.df_new: pd.DataFrame

        if isinstance(new_data, str):
            # Assume it's a JSON file path
            loaded = load_json_data(new_data)
            self.df_new = pd.DataFrame(loaded)
        elif isinstance(new_data, List):
            # Assume it's a list of CsvRow objects or dicts
            self.df_new = pd.DataFrame([row.__dict__ for row in new_data])
        else:
            raise ValueError("Input must be a JSON file path or a List[dict].")

        if self.df_new.empty:
            raise ValueError("Input DataFrame is empty.")

        # Use feature_columns from config for inference
        X_new = self.df_new[self.config.feature_columns]

        predicted_categories = self.model.predict(X_new)
        proba = self.model.predict_proba(X_new)
        confidence = proba.max(axis=1)

        self.df_new["predicted_category"] = predicted_categories
        self.df_new["prediction_confidence"] = confidence.round(2)

    def get_predictions(self) -> List[CsvRow]:
        """Return predictions as a list of CsvRow objects with 'category' overwritten."""

        # Prepare DataFrame: keep only CsvRow fields, overwrite 'category'
        df_filtered = self.df_new.copy()
        df_filtered["category"] = df_filtered["predicted_category"]

        # Create a List[CsvRow] object.
        loc = [
            CsvRow(
                row.to_dict(),
                mapping={
                    "date": "date",
                    "type": "type",
                    "partner": "partner",
                    "amount": "amount",
                    "currency": "currency",
                    "category": "category"
                }
            ) for _, row in df_filtered.iterrows()
        ]
        return loc

    def print_inference_data(self, with_confidence: bool = False) -> None:
        """Print the DataFrame with inference data."""

        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', 130)
        pd.set_option('display.expand_frame_repr', False)

        if with_confidence:
            print(self.df_new[["type", "partner", "amount", "currency", "category", "predicted_category", "prediction_confidence"]])  # noqa: E501
        else:
            print(self.df_new[["type", "partner", "amount", "currency", "predicted_category"]])
