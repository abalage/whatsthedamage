import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import skops.io as sio
from jinja2 import Template
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import NotFittedError
from sklearn.feature_extraction.text import HashingVectorizer, TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.utils.validation import check_is_fitted

from whatsthedamage.config.ml_config import MLConfig
from whatsthedamage.models.domain.csv_row import CsvRow
from whatsthedamage.utils.data_loader import load_json_data
from whatsthedamage.utils.logging import get_logger

logger = get_logger(__name__)


def generate_model_card_markdown(model_card: Dict[str, Any]) -> str:
    """Generate Model Card from HuggingFace official template using Jinja2.

    Uses the official HuggingFace Model Card Template (Apache-2.0 licensed).
    All template variables are mapped to our Model Card data structure.

    Args:
        model_card: Model Card dictionary with metadata

    Returns:
        Markdown string for the Model Card
    """
    # Load official HuggingFace template
    template_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "static", "model-card-template.md"
    )

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except FileNotFoundError:
        logger.warning(f"Template not found at {template_path}")
        return f"# Model Card: {model_card.get('model_name', 'Unknown')}"

    # Extract data
    p = model_card.get('privacy', {})
    params = model_card.get('parameters', {})
    training = model_card.get('training_info', {})
    eval_data = model_card.get('evaluation', {})
    env = model_card.get('environment', {})

    # Map to HuggingFace template variables
    use_hashing = params.get('use_hashing_vectorizer', False)

    if use_hashing:
        hashing_n_features = params.get('hashing_n_features', 1024)
        preprocessing_text = f"Text cleaning, HashingVectorizer ({hashing_n_features} features) + FunctionTransformer(np.sign)"
    else:
        preprocessing_text = "Text cleaning, TfidfVectorizer + FunctionTransformer(np.sign)"

    model_name = model_card.get('model_name', 'transaction-classifier')
    model_type = model_card.get('model_type', 'RandomForestClassifier')
    developer = model_card.get('developer', 'whatsthedamage')
    language = model_card.get('language', 'Hungarian')
    license = model_card.get('license', 'GPL-3.0')
    repository = model_card.get('repository', 'https://github.com/abalage/whatsthedamage')
    sklearn_version = env.get('sklearn_version', '1.7.2')

    training_data_size = training.get('training_data_size', 'unknown')
    training_data_period = training.get('training_data_period', 'unknown')
    category_count = training.get('category_count', 'unknown')
    test_data_size = eval_data.get('test_data_size', 'unknown')
    accuracy = eval_data.get('accuracy', 'N/A')
    macro_f1 = eval_data.get('macro_f1', 'N/A')
    n_estimators = params.get('n_estimators', 200)
    max_depth = params.get('max_depth', 'None')
    min_samples_split = params.get('min_samples_split', 10)

    data = {
        'model_id': model_name,
        'model_summary': f"{model_type} for bank transaction categorization",
        'model_description': f"{model_type} model for classifying bank transactions.",
        'developers': developer,
        'language': language,
        'license': license,
        'repo': repository,
        'model_type': model_type,
        'direct_use': "Classify bank transactions into predefined categories (Deposit, Grocery, Loan, etc.)",
        'downstream_use': "Can be used as part of personal finance management applications.",
        'out_of_scope_use': "- Not for financial advice\n- Not for predicting future transactions\n- Not for use with non-Hungarian transaction data",
        'bias_risks_limitations': "- Trained on Hungarian bank transaction data\n- May not generalize to other languages/countries\n- Limited to categories present in training data\n- Uses HashingVectorizer for privacy",
        'training_data': f"Approximately {training_data_size} spanning {training_data_period} with {category_count} categories",
        'preprocessing': preprocessing_text,
        'training_regime': "CPU",
        'testing_data': f"{test_data_size} transactions (stratified by category)",
        'testing_metrics': f"- **Accuracy**: {accuracy}\n- **Macro F1**: {macro_f1}",
        'results_summary': f"Model achieves {accuracy} accuracy (macro F1: {macro_f1}) on test data. Uses HashingVectorizer for privacy.",
        'model_specs': f"Random Forest with {n_estimators} estimators, max_depth={max_depth}, min_samples_split={min_samples_split}",
        'compute_infrastructure': "Training performed on local CPU",
        'hardware_type': "CPU",
        'sklearn_version': f"scikit-learn {sklearn_version}",
        'get_started_code': f'import skops.io as sio\nimport pandas as pd\n\n# Load the model. Only scikit-learn built-in types are required (no\n# whatsthedamage code needed). Calibration internals must be trusted\n# explicitly; omit them if the model was trained without calibration.\ntrusted = [\n    "sklearn.pipeline.Pipeline",\n    "sklearn.compose.ColumnTransformer",\n    "sklearn.feature_extraction.text.HashingVectorizer",\n    "sklearn.ensemble.RandomForestClassifier",\n    "sklearn.preprocessing.FunctionTransformer",\n    "sklearn.calibration.CalibratedClassifierCV",\n    "sklearn.calibration._CalibratedClassifier",\n    "sklearn.calibration._SigmoidCalibration",\n]\nmodel = sio.load("{model_name}.skops", trusted=trusted)\n\n# Predict on new transactions. Apply the documented text-cleaning\n# preprocessing to the "partner" field before prediction (see Model Card).\nX = pd.DataFrame({{\n    "type": ["Payment"],\n    "partner": ["Cleaned Partner Name"],\n    "amount": [-100.0],\n}})\npredictions = model.predict(X)\nprint(predictions)',
        'model_card_contact': f"For questions, please open an issue at: {repository}/issues",
    }

    # Render using Jinja2
    template = Template(template_content)
    return template.render(data)

def save(
    model: Pipeline,
    model_card: Dict[str, Any],
    config: MLConfig,
    test_data_df: Optional[pd.DataFrame] = None
) -> None:
    """Save the trained model, model card, and optionally test data to disk using MLConfig paths.

    Uses skops.io for secure serialization.
    Saves Model Card (HuggingFace standard) instead of custom manifest.
    Conditionally saves test data based on distribution mode.

    Args:
        model: Trained pipeline to save
        model_card: Model Card dictionary (HuggingFace standard)
        config: MLConfig with file paths
        test_data_df: Optional DataFrame containing test data to export
    """
    model_save_path = config.model_path
    model_card_save_path = config.model_card_path
    model_testdata_path = config.test_data_path

    # Ensure output directory exists
    dir_path = os.path.dirname(model_save_path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

    try:
        # Save model using skops.io
        sio.dump(model, model_save_path)
        logger.info(f"Model saved as skops file: {model_save_path}")

        # Save Model Card (JSON format for programmatic access)
        with open(model_card_save_path, "w", encoding="utf-8") as f:
            json.dump(model_card, f, indent=2, ensure_ascii=False)
        logger.info(f"Model Card saved as {model_card_save_path}")

        # Save Model Card markdown for human-readable documentation
        model_card_md_path = model_card_save_path.replace(".json", ".md")
        with open(model_card_md_path, "w", encoding="utf-8") as f:
            f.write(generate_model_card_markdown(model_card))
        logger.info(f"Model Card (markdown) saved as {model_card_md_path}")

        # Save test data only if NOT in distribution mode
        if test_data_df is not None and not config.is_distribution:
            test_data_df.to_json(model_testdata_path, orient="records", indent=2)
            logger.info(f"Test data saved as {model_testdata_path} with {len(test_data_df)} samples")
        elif test_data_df is not None and config.is_distribution:
            logger.info("Test data NOT saved (distribution mode - privacy protection)")

    except Exception as e:
        error_msg = f"Error during save operation: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def load(model_path: str) -> Pipeline:
    """Load a model from disk using skops.io.

    Args:
        model_path: Path to model file (.skops)

    Returns:
        Loaded pipeline model
    """
    try:
        if model_path.endswith('.skops'):
            # Check for untrusted types first
            unknown_types = sio.get_untrusted_types(file=model_path)
            if unknown_types:
                logger.info(f"Model contains untrusted types: {unknown_types}")
                # Trust common sklearn and custom types for our use case
                trusted_types = [
                    'sklearn.pipeline.Pipeline',
                    'sklearn.compose.ColumnTransformer',
                    'sklearn.feature_extraction.text.HashingVectorizer',
                    'sklearn.feature_extraction.text.TfidfVectorizer',
                    'sklearn.ensemble.RandomForestClassifier',
                    'sklearn.calibration.CalibratedClassifierCV',
                    'sklearn.calibration._CalibratedClassifier',
                    'sklearn.calibration._SigmoidCalibration',
                    'sklearn.preprocessing.FunctionTransformer',
                ]
                return sio.load(model_path, trusted=trusted_types)
        return sio.load(model_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load model from '{model_path}': {e}") from e


def validate_model_for_inference(model: Any) -> None:
    """
    Validate that a model is properly fitted and ready for inference.

    This function performs model-specific checks to ensure the classifier
    is fitted and can be used for prediction. It handles both regular
    Pipelines and calibrated Pipelines.

    Args:
        model: The scikit-learn estimator (Pipeline, classifier, etc.) to validate

    Raises:
        RuntimeError: If the model is not fitted or invalid for inference
    """
    try:
        # Get the actual estimator to validate
        if hasattr(model, 'named_steps'):
            # This is a Pipeline - get the classifier step
            if "calibration" in model.named_steps:
                # For calibrated models, get the calibrated classifier
                calibration_step = model.named_steps["calibration"]
                estimator_to_check = calibration_step
            else:
                # For regular pipelines, get the classifier step if it exists
                if "classifier" in model.named_steps:
                    estimator_to_check = model.named_steps["classifier"]
                else:
                    # Fallback to the full pipeline if no classifier step found
                    estimator_to_check = model
        else:
            # Direct estimator
            estimator_to_check = model

        # Use scikit-learn's native approach to check if the estimator is fitted
        check_is_fitted(estimator_to_check)
        logger.debug("Model validation passed: model is properly fitted for inference")
    except NotFittedError as e:
        logger.error(f"Model validation failed: model is not fitted - {e}")
        raise RuntimeError(f"Model is not fitted for inference: {e}") from e
    except Exception as e:
        logger.error(f"Model validation failed: {e}")
        raise RuntimeError(f"Model validation failed: {e}") from e

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

    # Apply ML-specific cleaning to partner field using assign to avoid full copy
    df_cleaned = df.assign(partner=df['partner'].apply(text_service.clean_partner_field))

    logger.info(f"Applied ML-specific text cleaning to {len(df_cleaned)} samples")
    return df_cleaned

class Train:
    """Prepare data and pipeline for model training."""
    def __init__(
        self,
        training_data_path: str,
        config: Optional[MLConfig] = None,
    ) -> None:
        self._training_data_path = training_data_path
        self._config = config or MLConfig()
        self._class_weight: Optional[str] = None

        # Use MLConfig paths for model and testdata files
        self._model_save_path = self._config.model_path
        self._testdata_save_path = self._config.test_data_path

        # Initialize SMOTE service (service layer pattern)
        from whatsthedamage.services.smote_service import SmoteService
        self._smote_service = SmoteService(self._config)

        # Initialize data attributes
        self._df: pd.DataFrame = pd.DataFrame()
        self._y: pd.Series = pd.Series(dtype=object)
        self._df_train: pd.DataFrame = pd.DataFrame()
        self._df_test: pd.DataFrame = pd.DataFrame()
        self._y_train: pd.Series = pd.Series(dtype=object)
        self._y_test: pd.Series = pd.Series(dtype=object)
        self._x_train: pd.DataFrame = pd.DataFrame()
        self._x_test: pd.DataFrame = pd.DataFrame()

        # Create the preprocessor ONCE and use everywhere
        self._preprocessor: ColumnTransformer = self._create_preprocessor()

        # Prepare data through separate methods
        self._load_and_validate_data()
        self._detect_class_imbalance()
        self._prepare_features()

        self._pipe: Pipeline = self._create_pipeline()
        self._model: Any = None

    def _load_and_validate_data(self) -> None:
        """Load, validate, and split training data."""
        # Load raw data
        raw_data = load_json_data(self._training_data_path)
        df = pd.DataFrame(raw_data)

        # Validate and clean data (originally from TrainingData class)
        self._df = self._validate_and_clean_data(df)
        self._y = self._df["category_id"]

        # Validate class sizes for stratified split
        class_counts = self._y.value_counts()
        if (class_counts < 2).any():
            raise ValueError(
                f"Each class must have at least 2 samples for stratified splitting. "
                f"Found class counts: {class_counts.to_dict()}"
            )

        # Always split data to prevent Data Leakage
        self._df_train, self._df_test, self._y_train, self._y_test = train_test_split(
            self._df, self._y, test_size=self._config.test_size, random_state=self._config.random_state, stratify=self._y
        )

    def _validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean training data (moved from TrainingData class)."""
        required_columns = set(self._config.feature_columns)
        missing_columns = [col for col in required_columns if col not in df.columns]
        if df.empty:
            raise ValueError("Loaded DataFrame is empty.")
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        # Use inplace=True to avoid creating a new DataFrame
        df.dropna(subset=list(required_columns), inplace=True)
        if df.empty:
            raise ValueError("All rows were dropped due to missing values.")

        # Apply ML-specific text cleaning to partner field
        df = apply_ml_text_cleaning(df)

        return df

    def _identify_rare_categories(self, y: pd.Series) -> List[str]:
        """Identify categories that need SMOTE oversampling."""
        class_counts = y.value_counts()

        if self._config.smote_target_categories:
            # Use explicitly specified categories
            rare_categories = [cat for cat in self._config.smote_target_categories if cat in class_counts.index]
        else:
            # Use threshold-based approach
            rare_categories = class_counts[class_counts < self._config.smote_min_samples_threshold].index.tolist()

        logger.info(f"Identified rare categories for SMOTE: {rare_categories}")
        return rare_categories

    def _apply_smote_after_preprocessing(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """Apply SMOTE after preprocessing text features to numerical format.

        This method delegates SMOTE operations to the SmoteService, following the service layer
        pattern and separation of concerns principle.
        """
        # Identify rare categories
        rare_categories = self._identify_rare_categories(y)

        # Delegate to SMOTE service
        x_resampled, y_resampled = self._smote_service.apply_smote(
            X, y, self._preprocessor, rare_categories
        )

        # Log results if SMOTE was actually applied
        if hasattr(x_resampled, 'shape') and hasattr(X, 'shape'):
            if x_resampled.shape[0] != X.shape[0]:
                self._log_smote_results(X, x_resampled)

        return x_resampled, y_resampled

    def _log_smote_results(self, X: pd.DataFrame, x_resampled_df: pd.DataFrame) -> None:
        """Log SMOTE results in a consistent format.

        Separates logging concern for better maintainability.
        """
        logger.info("SMOTE synthesis completed:")
        logger.info(f"  Original training samples: {len(X)}")
        logger.info(f"  Synthetic samples generated: {len(x_resampled_df) - len(X)}")
        logger.info(f"  Total training samples after SMOTE: {len(x_resampled_df)}")

    def _detect_class_imbalance(self) -> None:
        """Detect class imbalance and set class weights if needed."""
        # Compute value_counts once and reuse the result
        value_counts = self._y_train.value_counts()
        normalized_counts = value_counts / value_counts.sum()

        if normalized_counts.min() < self._config.classifier_imbalance_threshold:
            logger.info("Class distribution in training set:")
            logger.info(f"{value_counts}")
            self._class_weight = "balanced"
        else:
            self._class_weight = None

    def _prepare_features(self) -> None:
        """Prepare feature columns for training."""
        self._x_train = self._df_train[self._config.feature_columns]
        self._x_test = self._df_test[self._config.feature_columns]

        # Apply SMOTE if enabled (after preprocessing)
        if self._config.enable_smote:
            self._x_train, self._y_train = self._apply_smote_after_preprocessing(
                self._x_train, self._y_train
            )

    def _create_preprocessor(self) -> ColumnTransformer:
        """Create and return the feature engineering pipeline.

        Uses HashingVectorizer for privacy-preserving text features when configured,
        otherwise falls back to TfidfVectorizer for backward compatibility.
        """
        if self._config.use_hashing_vectorizer:
            # Use HashingVectorizer for privacy - no vocabulary storage
            type_vectorizer = HashingVectorizer(
                n_features=self._config.hashing_n_features,
                alternate_sign=self._config.hashing_alternate_sign,
                lowercase=True,
                strip_accents="unicode"
            )
            partner_vectorizer = HashingVectorizer(
                n_features=self._config.hashing_n_features,
                alternate_sign=self._config.hashing_alternate_sign,
                lowercase=True,
                strip_accents="unicode",
                ngram_range=(1, 1)
            )
        else:
            # Use TfidfVectorizer (stores vocabulary - privacy risk)
            type_vectorizer = TfidfVectorizer(
                lowercase=True,
                strip_accents="unicode",
                stop_words=self._config.hungarian_type_stop_words
            )
            partner_vectorizer = TfidfVectorizer(
                lowercase=True,
                strip_accents="unicode",
                ngram_range=(1, 1),
                stop_words=self._config.hungarian_partner_stop_words,
            )

        return ColumnTransformer(
            transformers=[
                ("type_vec", type_vectorizer, "type"),
                ("partner_vec", partner_vectorizer, "partner"),
                ("amount_sign", FunctionTransformer(np.sign, validate=False), ["amount"]),
            ],
            n_jobs=self._config.n_jobs
        )

    def _create_pipeline(self) -> Pipeline:
        """Create and return the full model pipeline using the single preprocessor instance."""
        classifier = RandomForestClassifier(
            random_state=self._config.random_state,
            min_samples_split=self._config.min_samples_split,
            n_estimators=self._config.n_estimators,
            max_depth=self._config.max_depth,
            class_weight=self._class_weight if self._class_weight in ('balanced', 'balanced_subsample', None) else None,
            n_jobs=self._config.n_jobs  # Use configured number of jobs for RandomForest
        )

        # Create base pipeline
        pipeline = Pipeline([("preprocessor", self._preprocessor), ("classifier", classifier)], memory=None)

        # Add calibration if enabled
        if self._config.enable_calibration:
            calibrated_classifier = CalibratedClassifierCV(
                estimator=pipeline,
                method=self._config.calibration_method,
                cv=self._config.calibration_cv,
                n_jobs=self._config.n_jobs  # Use configured number of jobs for calibration
            )
            return Pipeline([("calibration", calibrated_classifier)], memory=None)

        return pipeline

    def _get_preprocessor_from_model(self, model: Pipeline) -> ColumnTransformer:
        """Extract preprocessor from model, handling calibration if present.

        Args:
            model: The trained pipeline model

        Returns:
            The preprocessor from the model pipeline
        """
        if "calibration" in model.named_steps:
            # For calibrated models, access the fitted preprocessor from the calibrated estimators
            calibration_step = model.named_steps["calibration"]
            if hasattr(calibration_step, 'calibrated_classifiers_') and len(calibration_step.calibrated_classifiers_) > 0:
                # Get the fitted estimator from the first calibrated classifier
                fitted_estimator = calibration_step.calibrated_classifiers_[0].estimator
                return fitted_estimator.named_steps["preprocessor"]
            else:
                # Fallback: use the estimator from the calibration step
                return calibration_step.estimator.named_steps["preprocessor"]
        else:
            # For non-calibrated models, access preprocessor directly
            return model.named_steps["preprocessor"]

    def _create_model_card(
        self, model: Pipeline, tuning_method: Optional[str] = None, best_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a Model Card dictionary for the trained model.

        Based on HuggingFace Model Card standard with transaction-classification specific fields.
        Does NOT include private training data paths.

        Args:
            model: The trained pipeline model
            tuning_method: Optional tuning method ("grid" or "random")
            best_params: Optional dictionary of best parameters from tuning

        Returns:
            Model Card dictionary (HuggingFace standard format)
        """
        # Get processed feature matrix shape from the fitted preprocessor
        preprocessor = self._get_preprocessor_from_model(model)
        # Try to get shape from transformer attributes first to avoid re-transforming
        if hasattr(preprocessor, 'transformers_') and len(preprocessor.transformers_) > 0:
            # Transform a small sample to get shape (HashingVectorizer doesn't have shape attribute)
            sample_shape = preprocessor.transform(self._x_train.head(1)).shape
            processed_shape = (len(self._x_train), sample_shape[1])
        else:
            # Final fallback: transform the full data
            logger.warning("Transforming full data to get the shape.")
            processed_shape = preprocessor.transform(self._x_train).shape

        # Get category count
        category_count = len(self._y.unique())

        # Build Model Card with privacy-preserving metadata
        model_card: Dict[str, Any] = {
            "model_name": f"transaction_classifier_{self._config.model_version}",
            "version": self._config.model_version,
            "model_type": "RandomForestClassifier",
            "language": "Hungarian",
            "license": "GPL-3.0",
            "developer": "whatsthedamage",
            "repository": "https://github.com/abalage/whatsthedamage",
            "format": "skops",
            "parameters": {
                "classifier_short_name": self._config.classifier_short_name,
                "random_state": self._config.random_state,
                "min_samples_split": self._config.min_samples_split,
                "n_estimators": self._config.n_estimators,
                "max_depth": self._config.max_depth,
                "calibration_enabled": self._config.enable_calibration,
                "use_hashing_vectorizer": self._config.use_hashing_vectorizer,
                "hashing_n_features": self._config.hashing_n_features if self._config.use_hashing_vectorizer else None,
                "hashing_alternate_sign": self._config.hashing_alternate_sign if self._config.use_hashing_vectorizer else None,
                "n_jobs": self._config.n_jobs,
                "test_size": self._config.test_size,
            },
            "training_info": {
                "training_data_size": f"{len(self._df)} transactions",
                "training_data_period": "14 years",
                "category_count": category_count,
                "feature_columns": self._config.feature_columns,
                "feature_matrix_shape": list(processed_shape),
                "preprocessing": "TextCorrectionService + HashingVectorizer + FunctionTransformer(np.sign)" if self._config.use_hashing_vectorizer
                               else "TextCorrectionService + TfidfVectorizer + FunctionTransformer(np.sign)",
            },
            "evaluation": {
                "test_data_size": f"{len(self._df_test)} transactions",
                "accuracy": None,  # Will be updated after model evaluation
            },
            "privacy": {
                "safe_for_public_use": self._config.use_hashing_vectorizer and self._config.is_distribution,
                "vocabulary_stored": not self._config.use_hashing_vectorizer,
                "test_data_included": False,
                "training_data_paths_exposed": False,
            },
            "environment": {
                "sklearn_version": "1.7.2",
                "python_version": f"{datetime.now().year}.0",
            },
            "created_date": datetime.now().isoformat(),
        }

        # Add tuning-specific information if provided
        if tuning_method:
            model_card["parameters"]["tuning_method"] = tuning_method
            if best_params:
                model_card["parameters"]["best_parameters"] = best_params

        # Add calibration parameters if enabled
        if self._config.enable_calibration:
            model_card["parameters"]["calibration_method"] = self._config.calibration_method
            model_card["parameters"]["calibration_cv"] = self._config.calibration_cv

        logger.info(f"Feature matrix shape after preprocessing: {processed_shape}")
        logger.info(f"Model Card created with privacy settings: vocabulary_stored={not self._config.use_hashing_vectorizer}, safe_for_public_use={self._config.use_hashing_vectorizer and self._config.is_distribution}")

        return model_card

    def _compute_evaluation_metrics(self, model: Pipeline) -> Dict[str, Any]:
        """Compute evaluation metrics on the held-out test set.

        This is computed before the test data is potentially discarded in
        distribution mode, so the public Model Card carries real performance
        numbers without shipping the test data itself.

        Args:
            model: The trained (fitted) pipeline model

        Returns:
            Dictionary with accuracy, macro_f1, and classification_report.
        """
        try:
            y_pred = model.predict(self._x_test)
            accuracy = float(accuracy_score(self._y_test, y_pred))
            report = classification_report(
                self._y_test, y_pred, output_dict=True, zero_division=0
            )
            macro_f1 = float(report.get("macro avg", {}).get("f1-score", 0.0))
            logger.info(
                f"Evaluation metrics on held-out test set: accuracy={accuracy:.4f}, "
                f"macro_f1={macro_f1:.4f}"
            )
            return {
                "accuracy": accuracy,
                "macro_f1": macro_f1,
                "classification_report": report,
            }
        except Exception as e:
            logger.warning(f"Could not compute evaluation metrics: {e}")
            return {
                "accuracy": None,
                "macro_f1": None,
                "classification_report": None,
            }

    def _save_model(
        self, model: Pipeline, tuning_method: Optional[str] = None, best_params: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save the trained model, Model Card, and optionally test data.

        Uses skops.io for secure serialization and Model Card for standardized metadata.
        Test data is excluded when in distribution mode for privacy protection.
        Evaluation metrics are always recorded in the Model Card so that
        distribution-ready cards carry real performance numbers without the
        test data.

        Args:
            model: The trained pipeline model
            tuning_method: Optional tuning method ("grid" or "random")
            best_params: Optional dictionary of best parameters from tuning
        """
        # Create Model Card using new method
        model_card = self._create_model_card(model, tuning_method, best_params)

        # Record evaluation metrics before test data is potentially discarded
        eval_metrics = self._compute_evaluation_metrics(model)
        model_card["evaluation"]["accuracy"] = eval_metrics["accuracy"]
        model_card["evaluation"]["macro_f1"] = eval_metrics["macro_f1"]
        model_card["evaluation"]["classification_report"] = eval_metrics["classification_report"]

        # Prepare test data for saving (add category_id labels)
        test_data_with_labels = self._df_test.copy()
        test_data_with_labels["category_id"] = self._y_test

        # Delegate all file saving to the enhanced save function
        try:
            save(
                model=model,
                model_card=model_card,
                config=self._config,
                test_data_df=test_data_with_labels
            )
        except Exception as e:
            logger.error(f"Model saving has failed: {e}")
            raise e

    def train(self) -> None:
        """Train the model with fixed hyperparameters."""
        if self._x_train is None or self._y_train is None:
            raise ValueError("Training data (X_train or y_train) is None.")
        self._pipe.fit(self._x_train, self._y_train)
        self._model = self._pipe

        # Save the model using the centralized method
        self._save_model(self._model)

    def hyperparameter_tuning(self, method: str) -> Pipeline:
        """Perform hyperparameter tuning and train the best model.

        This method performs hyperparameter tuning using GridSearchCV or RandomizedSearchCV,
        then saves the best model (which is already trained on all training data due to refit=True).

        Args:
            method: Either "grid" for GridSearchCV or "random" for RandomizedSearchCV

        Returns:
            The trained pipeline with best hyperparameters
        """
        # Determine parameter names based on whether calibration is enabled
        if self._config.enable_calibration:
            classifier_prefix = "calibration__classifier__"
        else:
            classifier_prefix = "classifier__"

        cross_validation_params: Dict[str, List[Any]] = {
            f"{classifier_prefix}n_estimators": [50, 100, 200],
            f"{classifier_prefix}max_depth": [None, 10, 20, 30],
            f"{classifier_prefix}min_samples_split": [2, 5, 10],
        }
        grid_search = GridSearchCV(self._pipe, cross_validation_params, cv=3, n_jobs=-1)
        random_search = RandomizedSearchCV(
            self._pipe, cross_validation_params, n_iter=10, cv=3, n_jobs=-1, random_state=self._config.random_state
        )

        if self._x_train is None or self._y_train is None:
            raise ValueError("Training data (X_train or y_train) is None.")

        if method == "grid":
            logger.info("Using GridSearchCV for hyperparameter tuning. This may take a while.")
            grid_search.fit(self._x_train, self._y_train)
            logger.info(f"Best parameters: {grid_search.best_params_}")
            self._model = grid_search.best_estimator_
            best_params = grid_search.best_params_
        elif method == "random":
            logger.info("Using RandomizedSearchCV for hyperparameter tuning. This may take a while.")
            random_search.fit(self._x_train, self._y_train)
            logger.info(f"Best parameters: {random_search.best_params_}")
            self._model = random_search.best_estimator_
            best_params = random_search.best_params_
        else:
            logger.warning("Invalid hyperparameter tuning method selected. No tuning will be performed.")
            # Return the current model (which should be None if not trained)
            return self._model

        # Save the tuned model using the centralized method
        self._save_model(self._model, tuning_method=method, best_params=best_params)

        return self._model

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
        self.x_test = self.test_data[self.config.feature_columns]
        self.y_test = self.test_data["category_id"]

        # Validate model before attempting inference
        validate_model_for_inference(self.model)

        # Get predictions on the entire test set
        try:
            self.y_pred = self.model.predict(self.x_test)
            self.y_proba = self.model.predict_proba(self.x_test)
        except NotFittedError as e:
            logger.error(f"Model is not fitted for inference: {e}")
            raise RuntimeError(f"Model is not fitted for inference: {e}") from e

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
        df_cleaned = df_cleaned.dropna(subset=self.config.feature_columns + ["category_id"])
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
            test_data_subset = self.test_data.loc[self.x_test.index]
        else:
            # If no index, create a subset based on the prediction length
            test_data_subset = self.test_data.iloc[:len(self.y_pred)]

        # Avoid copying the entire DataFrame - use assign to add columns
        results_df = test_data_subset.assign(
            predicted=self.y_pred,
            confidence=self.y_proba.max(axis=1)
        )
        results_df['correct'] = results_df['category_id'] == results_df['predicted']

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
                'actual': row['category_id'],
                'predicted': row['predicted'],
                'confidence': float(row['confidence']),
                'partner': str(row['partner'])
            })

        # High confidence errors
        high_conf = misclassified[misclassified['confidence'] >= 0.9]
        high_conf_errors = []
        for _, row in high_conf.head(20).iterrows():
            high_conf_errors.append({
                'actual': row['category_id'],
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
        results_df = self.test_data[test_indices].assign(
            predicted=self.y_pred,
            correct=lambda x: x['category_id'] == self.y_pred
        )

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
    def __init__(self, model_path: str, new_data: Union[str, List[CsvRow]], config: Optional[MLConfig] = None) -> None:
        self.config = config or MLConfig()
        # self.model: Pipeline = load(self.config.model_path)
        self.model_path = model_path if model_path else self.config.model_path
        self.model: Pipeline = load(self.model_path)
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
        # Validate model before attempting inference
        validate_model_for_inference(self.model)

        try:
            predicted_categories = self.model.predict(df_input)
            proba = self.model.predict_proba(df_input)
        except NotFittedError as e:
            logger.error(f"Model is not fitted for inference: {e}")
            raise RuntimeError(f"Model is not fitted for inference: {e}") from e
        confidence = proba.max(axis=1)
        df_output = df_input.copy()
        df_output["predicted_category_id"] = predicted_categories
        df_output["prediction_confidence"] = confidence
        return df_output

    def get_predictions(self) -> List[CsvRow]:
        """Return predictions as a list of CsvRow objects with 'category_id' overwritten and confidence included."""
        df_filtered = self.df_output.copy()
        df_filtered["category_id"] = df_filtered["predicted_category_id"]

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
                    "category_id": "category_id"
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

        cols = self.config.feature_columns + ["predicted_category_id"]
        if with_confidence:
            cols += ["prediction_confidence"]
        print(self.df_output[cols])
