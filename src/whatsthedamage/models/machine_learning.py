import sys
import json
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
#from whatsthedamage.config.config import MLConfig
from pydantic import BaseModel
from datetime import datetime

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

def get_model_filename() -> str:
    # FIXME should be available without instantiation, MLConfig class might be overkill
    config = MLConfig()
    """Generate a unique model filename based on timestamp."""
    now = datetime.now().strftime("%Y%m%d_%H%M")
    return f"model_{config.classifier_short_name}_{now}.joblib"

def save(model: Pipeline, output: str, manifest: dict) -> None:
    """Save the trained model and its manifest metadata to disk."""
    if output == "":
        output = get_model_filename()
    # Ensure correct suffixes
    model_save_path = output if output.endswith(".joblib") else output + ".joblib"
    model_manifest_save_path = output if output.endswith(".manifest.json") else output + ".manifest.json"

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
    random_state: int = 42
    min_samples_split: int = 10
    n_estimators: int = 200

class TrainingData:
    def __init__(self, training_data_path: str):
        self.required_columns: set[str] = {"type", "partner", "currency", "amount", "category"}
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

    """Train the model with the provided training data."""
    def __init__(self, training_data_path: str, metrics: bool, gridsearch: bool, randomsearch: bool, output: str = ""):
        self.training_data_path = training_data_path
        self.metrics = metrics
        self.gridsearch = gridsearch
        self.randomsearch = randomsearch
        self.output = output
        self.df_train = None
        self.df_test = None
        self.y_train = None
        self.y_test = None
        self.model_save_path = self.output if self.output else get_model_filename()

        self.config = MLConfig()

        tdo = TrainingData(self.training_data_path)
        print(f"Loaded {len(tdo.get_training_data())} rows from {self.training_data_path}")

        self.df: pd.DataFrame = tdo.get_training_data()
        self.y: pd.Series = tdo.get_training_data()["category"]

        if self.metrics:
            # FIXME hardcoded amount of test size
            self.df_train, self.df_test, self.y_train, self.y_test = train_test_split(
                self.df, self.y, test_size=0.2, random_state=self.config.random_state, stratify=self.y)
        else:
            self.df_train = self.df
            self.df_test = None
            self.y_train = self.y
            self.y_test = None

        self.preprocessor: ColumnTransformer = self.get_preprocessor()

        X_train: Any = self.preprocessor.fit_transform(self.df_train)
        print(f"Feature matrix shape after preprocessing: {X_train.shape}")

        # FIXME not the nicest place to put this
        MANIFEST = {
            "model_file": self.model_save_path,
            "training_data": self.training_data_path,
            "training_date": datetime.now().isoformat(),
            "parameters": {
                "classifier_short_name": self.config.classifier_short_name,
                "random_state": self.config.random_state,
                "min_samples_split": self.config.min_samples_split,
                "n_estimators": self.config.n_estimators,
            },
            "data_info": {
                "row_count": len(self.df),
                "num_features": X_train.shape[1],
                "columns": [
                    # Only columns used in ColumnTransformer
                    "type", "partner", "currency", "amount"
                ],
            }
        }

        self.pipe: Pipeline = self.get_pipeline()
        self.model: Pipeline = self.train()

        if self.metrics and self.df_test is not None and self.y_test is not None:
            self.evaluate()

        save(self.model, self.model_save_path, MANIFEST)

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
        if not self.preprocessor:
            self.get_preprocessor()
        return Pipeline([
            ("preprocessor", self.preprocessor),
            ("classifier", RandomForestClassifier(
                random_state=self.config.random_state,
                min_samples_split=self.config.min_samples_split,
                n_estimators=self.config.n_estimators))
        ])

    def train(self, gridsearch=False, randomsearch=False) -> Pipeline:
        """Train the model, optionally with hyperparameter search."""
        pipe = self.get_pipeline()
        param_grid: Dict[str, List[Any]] = {
            "classifier__n_estimators": [50, 100, 200],
            "classifier__max_depth": [None, 10, 20, 30],
            "classifier__min_samples_split": [2, 5, 10],
        }
        param_dist: Dict[str, List[Any]] = param_grid.copy()
        if gridsearch:
            print("Using GridSearchCV for hyperparameter tuning...")
            grid_search: GridSearchCV = GridSearchCV(pipe, param_grid, cv=3, n_jobs=-1)
            grid_search.fit(self.df, self.y)
            print("Best parameters:", grid_search.best_params_)
            self.model = grid_search.best_estimator_
        elif randomsearch:
            print("Using RandomizedSearchCV for hyperparameter tuning...")
            random_search: RandomizedSearchCV = RandomizedSearchCV(
                pipe, param_dist, n_iter=10, cv=3, n_jobs=-1, random_state=self.config.random_state)
            random_search.fit(self.df, self.y)
            print("Best parameters:", random_search.best_params_)
            self.model = random_search.best_estimator_
        else:
            pipe.fit(self.df, self.y)
            self.model = pipe

        return self.model

    def evaluate(self) -> None:
        """Evaluate the model and print metrics."""
        y_pred: Any = self.model.predict(self.df_test)
        print("\nModel Evaluation Metrics:")
        print("Accuracy:", accuracy_score(self.y_test, y_pred))
        print(classification_report(self.y_test, y_pred))

class Inference:
    def __init__(self, model_path: str, new_data: str):
        self.model: Pipeline = load(model_path)
        self.df_new: pd.DataFrame = pd.DataFrame(load_json_data(new_data))

        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', 130)
        pd.set_option('display.expand_frame_repr', False)

        # Predict categories
        predicted_categories = self.model.predict(self.df_new)

        # Get prediction probabilities (confidence)
        proba = self.model.predict_proba(self.df_new)
        confidence = proba.max(axis=1)

        self.df_new["predicted_category"] = predicted_categories
        self.df_new["prediction_confidence"] = confidence.round(2)

        print(self.df_new[["type", "partner", "amount", "currency", "category", "predicted_category", "prediction_confidence"]])
