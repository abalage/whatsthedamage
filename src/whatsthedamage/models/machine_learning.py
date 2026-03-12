import json
import pandas as pd
import numpy as np
from typing import List, Any, Dict, Union, Optional, cast
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.base import BaseEstimator, TransformerMixin
import joblib
from whatsthedamage.models.csv_row import CsvRow
from pydantic import BaseModel
from datetime import datetime
import os
from whatsthedamage.utils.logging import get_logger

logger = get_logger(__name__)


def load_json_data(filepath: str) -> Any:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        error_msg = f"Error: File '{filepath}' not found."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg) from e
    except json.JSONDecodeError as e:
        error_msg = f"Error: File '{filepath}' is not valid JSON."
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    except Exception as e:
        error_msg = f"Error: An unexpected error occurred while reading '{filepath}': {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


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

    dir_path = os.path.dirname(model_save_path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

    try:
        joblib.dump(model, model_save_path)
        logger.info(f"Model training complete and saved as {model_save_path}")
    except Exception as e:
        error_msg = f"Error: Failed to save model to '{model_save_path}': {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        with open(model_manifest_save_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        logger.info(f"Manifest saved as {model_manifest_save_path}")
    except Exception as e:
        error_msg = f"Error: Failed to save manifest to '{model_manifest_save_path}': {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def load(model_path: str) -> Pipeline:
    """Load a model from disk."""
    try:
        return joblib.load(model_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load model from '{model_path}': {e}") from e

def apply_ml_text_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply ML-specific text cleaning to the partner field.

    This shared utility function is used by both TrainingData and Inference classes
    to ensure consistent text cleaning between training and inference.

    Args:
        df: DataFrame containing data with partner field

    Returns:
        DataFrame with cleaned partner field
    """
    # Import here to avoid circular dependency
    from whatsthedamage.services.text_correction_service import TextCorrectionService

    # Create text correction service with ML-specific cleaning (default config)
    text_service = TextCorrectionService()

    # Apply ML-specific cleaning to partner field
    df_cleaned = df.copy()
    df_cleaned['partner'] = df_cleaned['partner'].apply(text_service.clean_partner_field)

    logger.info(f"Applied ML-specific text cleaning to {len(df_cleaned)} samples")
    return df_cleaned


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
    model_version: str = "v6alpha_en"
    feature_columns: List[str] = ["type", "partner", "amount"]

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

        # Apply ML-specific text cleaning to partner field
        df_clean = apply_ml_text_cleaning(df_clean)

        return df_clean

    def get_training_data(self) -> pd.DataFrame:
        return self._df


class AmountSignTransformer(BaseEstimator, TransformerMixin):
    """Custom transformer to extract sign (positive/negative) from amount values."""

    def fit(self, X: Any, y: Optional[Any] = None) -> 'AmountSignTransformer':
        """Fit method (no operation needed for this transformer)."""
        return self

    def transform(self, X: Any) -> np.ndarray:
        """
        Transform amount values to their sign (1 for positive, 0 for zero, -1 for negative).

        Args:
            X: Input array of amount values

        Returns:
            Array of sign values (-1, 0, 1)
        """
        if isinstance(X, pd.DataFrame) or isinstance(X, pd.Series):
            X = X.values

        # Convert to numpy array if not already
        x_array = np.asarray(X)

        # Extract sign: 1 for positive, 0 for zero, -1 for negative
        signs = np.sign(x_array)

        # Reshape to 2D array as expected by scikit-learn
        result = signs.reshape(-1, 1).astype(float)
        return cast(np.ndarray, result)

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
                logger.info("Class distribution in training set:")
                logger.info(f"{self.y_train.value_counts()}")
            self.class_weight = "balanced"
        else:
            self.class_weight = None

        # Prepare feature columns
        self.x_train = self.df_train[self.config.feature_columns]
        self.x_test = self.df_test[self.config.feature_columns]

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
                ("amount_sign", AmountSignTransformer(), ["amount"]),
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
        ], memory=None)

    def train(self) -> None:
        """Train the model, optionally with hyperparameter search."""
        if self.x_train is None or self.y_train is None:
            raise ValueError("Training data (X_train or y_train) is None.")
        self.pipe.fit(self.x_train, self.y_train)
        self.model = self.pipe

        # Always evaluate if test data is available
        if self.df_test is not None and self.y_test is not None:
            self.evaluate()

        # Get processed feature matrix shape after fitting the pipeline
        processed_shape = self.model.named_steps["preprocessor"].transform(self.x_train).shape

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

        logger.info(f"Feature matrix shape after preprocessing: {processed_shape}")

        save(
            self.model,
            os.path.dirname(self.model_save_path),
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

        if self.x_train is None or self.y_train is None:
            raise ValueError("Training data (X_train or y_train) is None.")

        if method == "grid":
            logger.info("Using GridSearchCV for hyperparameter tuning. This may take a while.")
            grid_search.fit(self.x_train, self.y_train)
            logger.info(f"Best parameters: {grid_search.best_params_}")
            self.model = grid_search.best_estimator_
            self.evaluate()
        elif method == "random":
            logger.info("Using RandomizedSearchCV for hyperparameter tuning. This may take a while.")
            random_search.fit(self.x_train, self.y_train)
            logger.info(f"Best parameters: {random_search.best_params_}")
            self.model = random_search.best_estimator_
            self.evaluate()
        else:
            logger.info("No hyperparameter tuning method selected.")

    def evaluate(self) -> None:
        """Evaluate the model and print metrics."""
        if self.model is not None and self.y_test is not None:
            y_pred: Any = self.model.predict(self.x_test)
            print("\nModel Evaluation Metrics:")
            print(f"Accuracy: {accuracy_score(self.y_test, y_pred)}")
            print(f"Classification Report:\n{classification_report(self.y_test, y_pred)}")
        else:
            logger.error("Error: y_test is None. Cannot evaluate model.")

class Metrics:
    """Calculate model evaluation metrics - PURE DATA LAYER."""

    def __init__(self, model_path: str, test_data_path: str, config: Optional[MLConfig] = None) -> None:
        """
        Initialize Metrics with a trained model and test data.

        Args:
            model_path: Path to trained model file
            test_data_path: Path to test data JSON file
            config: ML configuration (optional)
        """
        self.config = config or MLConfig()
        self.model = load(model_path)

        # Load and prepare test data
        self.test_data = self._load_and_prepare_test_data(test_data_path)
        self.x_all = self.test_data[self.config.feature_columns]
        self.y_all = self.test_data["category"]

        # Split data into training and validation sets to prevent overfitting
        # Use same test_size as Train class for consistency

        self.x_train, self.x_val, self.y_train, self.y_val = train_test_split(
            self.x_all, self.y_all,
            test_size=self.config.test_size,
            random_state=self.config.random_state,
            stratify=self.y_all
        )
        # Use validation set for unbiased evaluation
        self.x_test = self.x_val
        self.y_test = self.y_val

        # Get predictions on validation/test set
        self.y_pred = self.model.predict(self.x_test)
        self.y_proba = self.model.predict_proba(self.x_test)

    def _load_and_prepare_test_data(self, test_data_path: str) -> pd.DataFrame:
        """Load and prepare test data for evaluation."""
        raw_data = load_json_data(test_data_path)
        df = pd.DataFrame(raw_data)

        # Validate required columns
        missing_columns = [col for col in self.config.feature_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        # Apply ML-specific text cleaning
        df_cleaned = apply_ml_text_cleaning(df)

        # Drop rows with missing values in required columns
        df_cleaned = df_cleaned.dropna(subset=self.config.feature_columns + ["category"])
        if df_cleaned.empty:
            raise ValueError("All rows were dropped due to missing values.")

        return df_cleaned

    def get_metrics_data(self) -> Dict[str, Any]:
        """Return raw data for rendering - NO FORMATTING."""
        return {
            'accuracy': accuracy_score(self.y_test, self.y_pred),
            'confusion_matrix': self._get_confusion_matrix_data(),
            'confusion_matrix_content': self._get_confusion_matrix_content(),
            'classification_report': classification_report(self.y_test, self.y_pred),
            'confused_pairs': self._get_confused_pairs_data(),
            'confidence_analysis': self._get_confidence_analysis_data(),
            'merchant_analysis': self._get_merchant_analysis_data(),
            'predictions': self._convert_to_list(self.y_pred),
            'probabilities': self._convert_to_list(self.y_proba),
            'test_samples': self._get_test_samples_data()
        }

    def _get_confusion_matrix_data(self) -> Dict[str, Any]:
        """Return raw confusion matrix data."""
        classes = sorted(self.y_test.unique())
        cm = confusion_matrix(self.y_test, self.y_pred, labels=classes)
        abbr_classes = [self._create_abbreviation(cls, classes) for cls in classes]

        return {
            'classes': classes,
            'matrix': cm.tolist() if hasattr(cm, 'tolist') else cm,
            'abbreviations': abbr_classes
        }

    def _get_confusion_matrix_content(self) -> str:
        """Return formatted confusion matrix content for display."""
        cm_data = self._get_confusion_matrix_data()
        classes = cm_data['classes']
        matrix = cm_data['matrix']
        abbreviations = cm_data['abbreviations']

        # Create DataFrame for confusion matrix display
        cm_df = pd.DataFrame(matrix, index=abbreviations, columns=abbreviations)

        confusion_matrix_header = "Confusion Matrix (rows = actual, columns = predicted):"
        confusion_matrix_table = cm_df.to_string()
        legend_items = [f"  {abbr} = {full_name}" for abbr, full_name in zip(abbreviations, classes)]
        legend = "\n".join(legend_items)

        return f"{confusion_matrix_header}\n{confusion_matrix_table}\n\nLegend:\n{legend}"

    def _create_abbreviation(self, class_name: str, all_classes: List[str]) -> str:
        """
        Create a unique abbreviation for a class name.

        Args:
            class_name: The full class name
            all_classes: List of all class names to ensure uniqueness

        Returns:
            A unique abbreviation (3-4 characters)
        """
        # If class name is short enough, use it as-is
        if len(class_name) <= 4:
            return class_name

        return self._find_unique_abbreviation(class_name, all_classes)

    def _find_unique_abbreviation(self, class_name: str, all_classes: List[str]) -> str:
        """
        Find a unique abbreviation by progressively increasing length.

        Args:
            class_name: The full class name
            all_classes: List of all class names to ensure uniqueness

        Returns:
            A unique abbreviation
        """
        abbr_length = 3
        max_length = len(class_name)

        while abbr_length <= max_length:
            abbr = class_name[:abbr_length].upper()
            if self._is_abbreviation_unique(abbr, class_name, all_classes, abbr_length):
                return abbr
            abbr_length += 1

        # Fallback: use first 3 chars + last char if no unique abbreviation found
        return (class_name[:3] + class_name[-1]).upper()

    def _is_abbreviation_unique(self, abbr: str, class_name: str, all_classes: List[str], abbr_length: int) -> bool:
        """
        Check if an abbreviation is unique among all class names.

        Args:
            abbr: The abbreviation to check
            class_name: The original class name
            all_classes: List of all class names
            abbr_length: Length of the abbreviation

        Returns:
            True if the abbreviation is unique, False otherwise
        """
        for other_class in all_classes:
            if other_class == class_name:
                continue
            # Check if other class would generate the same abbreviation
            other_abbr = other_class[:abbr_length].upper() if len(other_class) >= abbr_length else other_class.upper()
            if other_abbr == abbr:
                return False
        return True

    def _get_confused_pairs_data(self) -> List[Dict[str, Any]]:
        """Return raw confused pairs data for rendering."""
        classes = sorted(self.y_test.unique())
        cm = confusion_matrix(self.y_test, self.y_pred, labels=classes)

        confused_pairs = []
        for i, actual_class in enumerate(classes):
            for j, predicted_class in enumerate(classes):
                if i != j and cm[i, j] > 0:
                    confused_pairs.append({
                        'actual': actual_class,
                        'predicted': predicted_class,
                        'count': int(cm[i, j]),
                        'percent_of_actual': float((cm[i, j] / cm[i, :].sum()) * 100)
                    })

        # Sort by confusion count
        confused_pairs.sort(key=lambda x: x['count'], reverse=True)

        return confused_pairs[:10]  # Top 10 confused pairs

    def _get_confidence_analysis_data(self) -> Dict[str, Any]:
        """Return raw confidence analysis data."""
        # Create DataFrame with predictions and confidence for the validation/test set
        if hasattr(self.x_test, 'index'):
            # If x_test has index, use it to align with original data
            test_data_subset = self.test_data.loc[self.x_test.index].copy()
        else:
            # If no index, create a subset based on the prediction length
            test_data_subset = self.test_data.iloc[:len(self.y_pred)].copy()

        results_df = test_data_subset.copy()
        results_df['predicted'] = self.y_pred
        results_df['confidence'] = self.y_proba.max(axis=1)
        results_df['correct'] = results_df['category'] == results_df['predicted']

        # Misclassified samples
        misclassified = results_df[~results_df['correct']]

        if len(misclassified) == 0:
            return {
                'low_conf_count': 0,
                'low_conf_percentage': 0.0,
                'low_conf_errors': [],
                'high_conf_count': 0,
                'high_conf_errors': []
            }

        # Low confidence errors
        low_conf = misclassified[misclassified['confidence'] < 0.7]
        low_conf_errors = []
        for _, row in low_conf.sort_values('confidence').head(20).iterrows():
            low_conf_errors.append({
                'actual': row['category'],
                'predicted': row['predicted'],
                'confidence': float(row['confidence']),
                'partner': str(row['partner'])
            })

        # High confidence errors
        high_conf = misclassified[misclassified['confidence'] >= 0.9]
        high_conf_errors = []
        for _, row in high_conf.head(20).iterrows():
            high_conf_errors.append({
                'actual': row['category'],
                'predicted': row['predicted'],
                'confidence': float(row['confidence']),
                'partner': str(row['partner'])
            })

        return {
            'low_conf_count': len(low_conf),
            'low_conf_percentage': float((len(low_conf) / len(misclassified)) * 100),
            'low_conf_errors': low_conf_errors,
            'high_conf_count': len(high_conf),
            'high_conf_errors': high_conf_errors
        }

    def _get_merchant_analysis_data(self) -> List[Dict[str, Any]]:
        """Return raw merchant analysis data."""
        # Create DataFrame with predictions for the validation/test set
        test_indices = self.test_data.index.isin(self.x_test.index)
        results_df = self.test_data[test_indices].copy()
        results_df['predicted'] = self.y_pred
        results_df['correct'] = results_df['category'] == results_df['predicted']

        # Misclassified samples
        misclassified = results_df[~results_df['correct']]

        if len(misclassified) == 0:
            return []

        # Merchant error analysis
        merchant_errors = misclassified.groupby('partner').size().sort_values(ascending=False)

        merchant_data = []
        for merchant, count in merchant_errors.head(10).items():
            percentage = float((count / len(misclassified)) * 100)
            merchant_str = str(merchant)  # Ensure merchant is a string
            display_name = (merchant_str[:25] + '...') if len(merchant_str) > 28 else merchant_str
            merchant_data.append({
                'display_name': display_name,
                'count': int(count),
                'percentage': percentage
            })

        return merchant_data

    def _get_test_samples_data(self) -> List[Dict[str, Any]]:
        """Return raw test sample data for rendering."""
        return [{
            'actual': str(actual),
            'predicted': str(predicted),
            'confidence': float(confidence),
            'partner': str(partner),
            'amount': float(amount)
        } for actual, predicted, confidence, partner, amount in zip(
            self.y_test, self.y_pred, self.y_proba.max(axis=1),
            self.test_data['partner'], self.test_data['amount']
        )]

    def _convert_to_list(self, data: Any) -> List[Any]:
        """
        Convert array-like data to a list format.

        Handles numpy arrays, tuples of arrays, and other iterable types that can be
        returned by scikit-learn's predict() and predict_proba() methods.

        Args:
            data: Array-like data to convert (predictions or probabilities)

        Returns:
            List representation of the input data
        """
        if hasattr(data, 'tolist'):
            # Single numpy array case
            return data.tolist()  # type: ignore[no-any-return]
        elif isinstance(data, tuple) and len(data) > 0:
            # Tuple case - convert each array in the tuple
            if len(data) == 1:
                return data[0].tolist()  # type: ignore[no-any-return]
            else:
                # For multiple arrays, return a list of lists
                return [arr.tolist() for arr in data]  # type: ignore[no-any-return]
        else:
            # Fallback - try to convert to list
            try:
                return list(data)
            except (TypeError, ValueError):
                # If all else fails, return empty list
                return []

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
        """Return predictions as a list of CsvRow objects with 'category' overwritten and confidence included."""
        df_filtered = self.df_output.copy()
        df_filtered["category"] = df_filtered["predicted_category"]

        csv_rows = []
        for _, row in df_filtered.iterrows():
            csv_row = CsvRow(
                row.to_dict(),
                mapping={
                    "date": "date",
                    "type": "type",
                    "partner": "partner",
                    "amount": "amount",
                    "currency": "currency",
                    "category": "category"
                }
            )
            # Set confidence from prediction
            csv_row.confidence = row["prediction_confidence"]
            csv_rows.append(csv_row)

        return csv_rows

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