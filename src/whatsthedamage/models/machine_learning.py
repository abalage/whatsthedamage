import json
import pandas as pd
from typing import List, Any, Dict, Union, Optional
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
        return None
    except json.JSONDecodeError:
        print(f"Error: File '{filepath}' is not valid JSON.")
        return None
    except Exception as e:
        print(f"Error: An unexpected error occurred while reading '{filepath}': {e}")
        return None


def save(
    model: Pipeline,
    output_dir: str,
    manifest: Dict[str, Any],
    classifier_short_name: str,
    model_version: str
) -> None:
    """Save the trained model and its manifest metadata to disk in the specified directory."""
    model_filename = f"model-{classifier_short_name}-{model_version}.joblib"
    model_save_path = os.path.join(output_dir, model_filename)
    model_manifest_save_path = os.path.join(
        output_dir, model_filename.replace(".joblib", ".manifest.json")
    )

    dir_path = output_dir if os.path.isdir(output_dir) else os.path.dirname(output_dir)
    if dir_path and not os.path.isdir(dir_path):
        os.makedirs(dir_path, exist_ok=True)

    try:
        joblib.dump(model, model_save_path)
        print(f"Model training complete and saved as {model_save_path}")
    except Exception as e:
        print(f"Error: Failed to save model to '{model_save_path}': {e}")

    try:
        with open(model_manifest_save_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"Manifest saved as {model_manifest_save_path}")
    except Exception as e:
        print(f"Error: Failed to save manifest to '{model_manifest_save_path}': {e}")


def load(model_path: str) -> Pipeline:
    """Load a model from disk."""
    model: Any = None
    try:
        model = joblib.load(model_path)
    except Exception as e:
        print(f"Error: Failed to load model from '{model_path}': {e}")

    return model


class MLConfig(BaseModel):
    hungarian_type_stop_words: List[str] = [
        "ft", "forint", "bol"
    ]
    hungarian_partner_stop_words: List[str] = [
        "es", "bt", "kft", "zrt", "rt", "nyrt", "ev", "korlatolt", "felelossegu",
        "tarsasag", "alapitvany", "kisker", "szolgaltato", "kereskedelmi",
        "kereskedes", "sz", "u.", "utca", "ut", "&", "huf", "otpmobl", "paypal",
        "crv", "sumup", "www", "toltoall"
    ]
    classifier_short_name: str = "rf"
    classifier_imbalance_threshold: float = 0.2
    random_state: int = 42
    min_samples_split: int = 10
    n_estimators: int = 200
    max_depth: Union[int, None] = None
    test_size: float = 0.2
    model_version: str = "v5alpha_en"
    feature_columns: List[str] = ["type", "partner", "currency", "amount"]

    @property
    def model_path(self) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(base_dir, "..", "static")
        return os.path.abspath(
            os.path.join(
                static_dir,
                f"model-{self.classifier_short_name}-{self.model_version}.joblib"
            )
        )

    @property
    def manifest_path(self) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(base_dir, "..", "static")
        return os.path.abspath(
            os.path.join(
                static_dir,
                f"model-{self.classifier_short_name}-{self.model_version}.manifest.json"
            )
        )


class TrainingData:
    def __init__(self, training_data_path: str, config: MLConfig):
        self.required_columns: set[str] = set(config.feature_columns)
        raw_data = load_json_data(training_data_path)
        df = pd.DataFrame(raw_data)
        self._df = self._validate_and_clean_data(df)

    def _validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if df.empty:
            raise ValueError("Loaded DataFrame is empty.")
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        df_clean = df.dropna(subset=list(self.required_columns))
        if df_clean.empty:
            raise ValueError("All rows were dropped due to missing values.")
        return df_clean

    def get_training_data(self) -> pd.DataFrame:
        return self._df


class Train:
    """Prepare data and pipeline for model training."""
    def __init__(
        self,
        training_data_path: str,
        config: Optional[MLConfig] = None,
        output: str = "",
        verbose: bool = False
    ) -> None:
        self.training_data_path = training_data_path
        self.output = output
        self.config = config or MLConfig()
        self.model_save_path = self.output if self.output else self.config.model_path
        self.class_weight = None
        self.verbose = verbose

        # Load and validate data
        tdo = TrainingData(self.training_data_path, config=self.config)
        self.df: pd.DataFrame = tdo.get_training_data()
        self.y: pd.Series = self.df["category"]

        # Validate class sizes for stratified split
        class_counts = self.y.value_counts()
        if (class_counts < 2).any():
            raise ValueError(
                f"Each class must have at least 2 samples for stratified splitting. "
                f"Found class counts: {class_counts.to_dict()}"
            )

        # Always split data to prevent Data Leakage
        self.df_train, self.df_test, self.y_train, self.y_test = train_test_split(
            self.df, self.y, test_size=self.config.test_size, random_state=self.config.random_state, stratify=self.y
        )

        # Detect class imbalance
        class_counts = self.y_train.value_counts(normalize=True)
        if class_counts.min() < self.config.classifier_imbalance_threshold:
            if self.verbose:
                print("Class distribution in training set:")
                print(self.y_train.value_counts())
            self.class_weight = "balanced"
        else:
            self.class_weight = None

        # Prepare feature columns
        self.X_train = self.df_train[self.config.feature_columns]
        self.X_test = self.df_test[self.config.feature_columns]

        # Create the preprocessor ONCE and use everywhere
        self.preprocessor: ColumnTransformer = self._create_preprocessor()
        self.pipe: Pipeline = self._create_pipeline()
        self.model: Any = None

    def _create_preprocessor(self) -> ColumnTransformer:
        """Create and return the feature engineering pipeline."""
        return ColumnTransformer(
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

    def _create_pipeline(self) -> Pipeline:
        """Create and return the full model pipeline using the single preprocessor instance."""
        classifier = RandomForestClassifier(
            random_state=self.config.random_state,
            min_samples_split=self.config.min_samples_split,
            n_estimators=self.config.n_estimators,
            max_depth=self.config.max_depth,
            class_weight=self.class_weight if self.class_weight in ('balanced', 'balanced_subsample', None) else None
        )
        return Pipeline([
            ("preprocessor", self.preprocessor),
            ("classifier", classifier)
        ])

    def train(self) -> None:
        """Train the model, optionally with hyperparameter search."""
        if self.X_train is None or self.y_train is None:
            raise ValueError("Training data (X_train or y_train) is None.")
        self.pipe.fit(self.X_train, self.y_train)
        self.model = self.pipe

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

        save(
            self.model,
            self.model_save_path,
            MANIFEST,
            self.config.classifier_short_name,
            self.config.model_version
        )

    def hyperparameter_tuning(self, method: str) -> None:
        """Perform hyperparameter tuning and evaluate the best model."""
        cross_validation_params: Dict[str, List[Any]] = {
            "classifier__n_estimators": [50, 100, 200],
            "classifier__max_depth": [None, 10, 20, 30],
            "classifier__min_samples_split": [2, 5, 10],
        }
        grid_search = GridSearchCV(self.pipe, cross_validation_params, cv=3, n_jobs=-1)
        random_search = RandomizedSearchCV(
            self.pipe, cross_validation_params, n_iter=10, cv=3, n_jobs=-1,
            random_state=self.config.random_state
        )

        if self.X_train is None or self.y_train is None:
            raise ValueError("Training data (X_train or y_train) is None.")

        if method == "grid":
            print("Using GridSearchCV for hyperparameter tuning. This may take a while.")
            grid_search.fit(self.X_train, self.y_train)
            print("Best parameters:", grid_search.best_params_)
            self.model = grid_search.best_estimator_
            self.evaluate()
        elif method == "random":
            print("Using RandomizedSearchCV for hyperparameter tuning. This may take a while.")
            random_search.fit(self.X_train, self.y_train)
            print("Best parameters:", random_search.best_params_)
            self.model = random_search.best_estimator_
            self.evaluate()
        else:
            print("No hyperparameter tuning method selected.")

    def evaluate(self) -> None:
        """Evaluate the model and print metrics."""
        if self.model is not None and self.y_test is not None:
            y_pred: Any = self.model.predict(self.X_test)
            print("\nModel Evaluation Metrics:")
            print("Accuracy:", accuracy_score(self.y_test, y_pred))
            print(classification_report(self.y_test, y_pred))
        else:
            print("Error: y_test is None. Cannot evaluate model.")


class Inference:
    def __init__(self, new_data: Union[str, List[CsvRow]], config: Optional[MLConfig] = None) -> None:
        self.config = config or MLConfig()
        self.model: Pipeline = load(self.config.model_path)
        self.df_input = self._prepare_input_data(new_data)
        self.df_output = self._make_predictions(self.df_input)

    def _prepare_input_data(self, new_data: Union[str, List[CsvRow]]) -> pd.DataFrame:
        """Prepare input data as a DataFrame."""
        if isinstance(new_data, str):
            loaded = load_json_data(new_data)
            df_input = pd.DataFrame(loaded)
        elif isinstance(new_data, List):
            df_input = pd.DataFrame([row.__dict__ for row in new_data])
        else:
            raise ValueError("Input must be a JSON file path or a List[dict].")

        if df_input.empty:
            raise ValueError("Input DataFrame is empty.")
        return df_input

    def _make_predictions(self, df_input: pd.DataFrame) -> pd.DataFrame:
        """Make predictions and add them to the DataFrame."""
        predicted_categories = self.model.predict(df_input)
        proba = self.model.predict_proba(df_input)
        confidence = proba.max(axis=1)
        df_output = df_input.copy()
        df_output["predicted_category"] = predicted_categories
        df_output["prediction_confidence"] = confidence
        return df_output

    def get_predictions(self) -> List[CsvRow]:
        """Return predictions as a list of CsvRow objects with 'category' overwritten."""
        df_filtered = self.df_output.copy()
        df_filtered["category"] = df_filtered["predicted_category"]

        return [
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

    def print_inference_data(self, with_confidence: bool = False) -> None:
        """Print the DataFrame with inference data."""
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', 130)
        pd.set_option('display.expand_frame_repr', False)

        cols = self.config.feature_columns + ["predicted_category"]
        if with_confidence:
            cols += ["prediction_confidence"]
        print(self.df_output[cols])
