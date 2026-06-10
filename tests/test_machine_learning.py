# tests/test_machine_learning.py
"""
Unit tests for machine_learning.py module.

Tests cover all major components while ensuring existing joblib models
are never overwritten by using temporary directories and files.
"""

import pytest
import tempfile
import os
import json
import pandas as pd
import numpy as np
from unittest.mock import patch
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

from whatsthedamage.models.domain.machine_learning import (
    AmountSignTransformer, Train, Metrics, Inference,
    save, load, validate_model_for_inference, apply_ml_text_cleaning
)
from whatsthedamage.config.ml_config import MLConfig
from whatsthedamage.models.domain.csv_row import CsvRow


# Fixtures Section
@pytest.fixture
def ml_config_temp():
    """MLConfig with temporary file paths to avoid overwriting existing models."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a custom MLConfig with temporary paths
        config = MLConfig(test_size=0.3)  # Test size that ensures at least 2 samples per class
        # Override the properties to use temp directory
        config.__class__.model_path = property(lambda self: os.path.join(temp_dir, "test-model.joblib"))
        config.__class__.manifest_path = property(lambda self: os.path.join(temp_dir, "test-model.manifest.json"))
        config.__class__.test_data_path = property(lambda self: os.path.join(temp_dir, "test-model.testdata.json"))
        yield config


@pytest.fixture
def sample_training_data():
    """Sample training dataset for testing with sufficient samples per class."""
    return [
        {
            "amount": -100.0,
            "category": "Grocery",
            "currency": "EUR",
            "date": "2023-01-01",
            "partner": "Test Grocery Store",
            "type": "Payment"
        },
        {
            "amount": -50.0,
            "category": "Grocery",
            "currency": "EUR",
            "date": "2023-01-02",
            "partner": "Test Market",
            "type": "Payment"
        },
        {
            "amount": -75.0,
            "category": "Grocery",
            "currency": "EUR",
            "date": "2023-01-03",
            "partner": "Test Supermarket",
            "type": "Payment"
        },
        {
            "amount": -30.0,
            "category": "Transportation",
            "currency": "EUR",
            "date": "2023-01-04",
            "partner": "Test Taxi Service",
            "type": "Payment"
        },
        {
            "amount": -20.0,
            "category": "Transportation",
            "currency": "EUR",
            "date": "2023-01-05",
            "partner": "Test Bus Company",
            "type": "Payment"
        },
        {
            "amount": -40.0,
            "category": "Transportation",
            "currency": "EUR",
            "date": "2023-01-06",
            "partner": "Test Train Company",
            "type": "Payment"
        },
        {
            "amount": 200.0,
            "category": "Salary",
            "currency": "EUR",
            "date": "2023-01-07",
            "partner": "Test Employer",
            "type": "Deposit"
        },
        {
            "amount": 150.0,
            "category": "Salary",
            "currency": "EUR",
            "date": "2023-01-08",
            "partner": "Test Company",
            "type": "Deposit"
        },
        {
            "amount": 180.0,
            "category": "Salary",
            "currency": "EUR",
            "date": "2023-01-09",
            "partner": "Test Corporation",
            "type": "Deposit"
        }
    ]


@pytest.fixture
def sample_test_data():
    """Sample test data for metrics testing."""
    return [
        {
            "amount": -75.0,
            "category": "Grocery",
            "currency": "EUR",
            "date": "2023-02-01",
            "partner": "Test Supermarket",
            "type": "Payment"
        },
        {
            "amount": -30.0,
            "category": "Transportation",
            "currency": "EUR",
            "date": "2023-02-02",
            "partner": "Test Bus Company",
            "type": "Payment"
        }
    ]


# Test Classes
class TestAmountSignTransformer:
    """Test the AmountSignTransformer class."""

    def test_fit_returns_self(self):
        """Test that fit() method returns self."""
        transformer = AmountSignTransformer()
        result = transformer.fit(None)
        assert result is transformer

    def test_transform_positive_values(self):
        """Test transform with positive values."""
        transformer = AmountSignTransformer()
        transformer.fit(None)

        # Test with numpy array
        result = transformer.transform(np.array([100.0, 50.0, 25.0]))
        expected = np.array([[1.0], [1.0], [1.0]])
        np.testing.assert_array_equal(result, expected)

    def test_transform_negative_values(self):
        """Test transform with negative values."""
        transformer = AmountSignTransformer()
        transformer.fit(None)

        result = transformer.transform(np.array([-100.0, -50.0, -25.0]))
        expected = np.array([[-1.0], [-1.0], [-1.0]])
        np.testing.assert_array_equal(result, expected)

    def test_transform_mixed_values(self):
        """Test transform with mixed positive, negative, and zero values."""
        transformer = AmountSignTransformer()
        transformer.fit(None)

        result = transformer.transform(np.array([100.0, -50.0, 0.0, 25.0, -10.0]))
        expected = np.array([[1.0], [-1.0], [0.0], [1.0], [-1.0]])
        np.testing.assert_array_equal(result, expected)

    def test_transform_with_pandas_series(self):
        """Test transform with pandas Series input."""
        transformer = AmountSignTransformer()
        transformer.fit(None)

        series = pd.Series([100.0, -50.0, 0.0])
        result = transformer.transform(series)
        expected = np.array([[1.0], [-1.0], [0.0]])
        np.testing.assert_array_equal(result, expected)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_save_and_load_with_temp_file(self, ml_config_temp):
        """Test save and load functions with temporary file."""
        # Create a simple real pipeline that can be pickled
        preprocessor = ColumnTransformer([
            ("test", TfidfVectorizer(), "test_col")
        ])
        classifier = RandomForestClassifier(random_state=42, n_estimators=2)
        pipeline = Pipeline([("preprocessor", preprocessor), ("classifier", classifier)], memory=None)

        # Fit with minimal data to make it picklable
        X_train = pd.DataFrame({"test_col": ["test1", "test2"]})
        y_train = ["cat1", "cat2"]
        pipeline.fit(X_train, y_train)

        manifest = {
            "model_version": "test_v1",
            "training_date": "2023-01-01"
        }

        # Test save
        save(pipeline, manifest, ml_config_temp)

        # Verify files were created
        assert os.path.exists(ml_config_temp.model_path)
        assert os.path.exists(ml_config_temp.manifest_path)

        # Test load
        loaded_manifest = json.load(open(ml_config_temp.manifest_path, 'r', encoding='utf-8'))
        assert loaded_manifest["model_version"] == "test_v1"

    def test_validate_model_for_inference_with_fitted_model(self):
        """Test validation with a properly fitted model."""
        # Create a simple fitted pipeline
        preprocessor = ColumnTransformer([
            ("test", TfidfVectorizer(), "test_col")
        ])
        classifier = RandomForestClassifier(random_state=42, n_estimators=2)
        pipeline = Pipeline([("preprocessor", preprocessor), ("classifier", classifier)], memory=None)

        # Fit with minimal data
        X_train = pd.DataFrame({"test_col": ["test1", "test2"]})
        y_train = ["cat1", "cat2"]
        pipeline.fit(X_train, y_train)

        # Should not raise exception
        validate_model_for_inference(pipeline)

    def test_validate_model_for_inference_with_unfitted_model(self):
        """Test validation with an unfitted model should raise RuntimeError."""
        # Create an unfitted pipeline
        pipeline = Pipeline([
            ("preprocessor", ColumnTransformer([("test", TfidfVectorizer(), "test_col")])),
            ("classifier", RandomForestClassifier())
        ], memory=None)

        with pytest.raises(RuntimeError, match="Model is not fitted for inference"):
            validate_model_for_inference(pipeline)

    def test_apply_ml_text_cleaning(self):
        """Test ML text cleaning function."""
        df = pd.DataFrame({
            "partner": ["Test Partner Ltd.", "Another Company Kft.", "Simple Name"]
        })

        cleaned_df = apply_ml_text_cleaning(df)

        # Should not raise exceptions and return DataFrame
        assert isinstance(cleaned_df, pd.DataFrame)
        assert len(cleaned_df) == 3
        assert "partner" in cleaned_df.columns


class TestTrainClass:
    """Test the Train class."""

    def test_initialization_with_custom_config(self, ml_config_temp, sample_training_data):
        """Test Train class initialization with custom config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_training_data, f)
            temp_training_path = f.name

        try:
            train_instance = Train(temp_training_path, ml_config_temp)

            # Verify attributes are set
            assert train_instance._config == ml_config_temp
            assert len(train_instance._df) == 9  # Should have loaded 9 samples
            assert not train_instance._df.empty

            # Verify data was split
            assert len(train_instance._df_train) > 0
            assert len(train_instance._df_test) > 0

        finally:
            os.unlink(temp_training_path)

    def test_validate_and_clean_data(self, ml_config_temp):
        """Test data validation and cleaning."""
        train_instance = Train.__new__(Train)  # Create without calling __init__
        train_instance._config = ml_config_temp

        # Test with valid data
        df = pd.DataFrame({
            "type": ["Payment", "Deposit"],
            "partner": ["Test Partner", "Another Partner"],
            "amount": [-100.0, 200.0],
            "category": ["Grocery", "Salary"]
        })

        cleaned_df = train_instance._validate_and_clean_data(df)
        assert len(cleaned_df) == 2
        assert not cleaned_df.isna().any().any()

    def test_validate_and_clean_data_missing_columns(self, ml_config_temp):
        """Test data validation with missing required columns."""
        train_instance = Train.__new__(Train)
        train_instance._config = ml_config_temp

        # Test with missing columns
        df = pd.DataFrame({
            "type": ["Payment"],
            "amount": [-100.0],
            "category": ["Grocery"]
            # Missing 'partner' column
        })

        with pytest.raises(ValueError, match="Missing required columns"):
            train_instance._validate_and_clean_data(df)

    def test_create_preprocessor(self, ml_config_temp):
        """Test preprocessor creation."""
        train_instance = Train.__new__(Train)
        train_instance._config = ml_config_temp

        preprocessor = train_instance._create_preprocessor()

        # Verify it's a ColumnTransformer
        assert isinstance(preprocessor, ColumnTransformer)

        # Verify expected transformers are present
        transformer_names = [name for name, _, _ in preprocessor.transformers]
        assert "type_tfidf" in transformer_names
        assert "partner_tfidf" in transformer_names
        assert "amount_sign" in transformer_names

    def test_create_pipeline(self, ml_config_temp):
        """Test pipeline creation."""
        train_instance = Train.__new__(Train)
        train_instance._config = ml_config_temp
        train_instance._preprocessor = train_instance._create_preprocessor()
        train_instance._class_weight = None  # Set required attribute

        # Temporarily disable calibration to simplify test
        original_calibration = train_instance._config.enable_calibration
        train_instance._config.enable_calibration = False

        try:
            pipeline = train_instance._create_pipeline()

            # Verify it's a Pipeline
            assert isinstance(pipeline, Pipeline)

            # Verify expected steps are present
            step_names = list(pipeline.named_steps.keys())
            assert "preprocessor" in step_names
            assert "classifier" in step_names
        finally:
            train_instance._config.enable_calibration = original_calibration

    def test_create_manifest(self, ml_config_temp):
        """Test manifest creation."""
        train_instance = Train.__new__(Train)
        train_instance._config = ml_config_temp
        train_instance._training_data_path = "test_data.json"
        train_instance._model_save_path = ml_config_temp.model_path
        train_instance._testdata_save_path = ml_config_temp.test_data_path

        # Create a simple pipeline
        preprocessor = train_instance._create_preprocessor()

        # Temporarily disable calibration to simplify test
        original_calibration = train_instance._config.enable_calibration
        train_instance._config.enable_calibration = False

        try:
            # Fit the preprocessor first to avoid NotFittedError
            train_instance._x_train = pd.DataFrame({
                "type": ["Payment"],
                "partner": ["Test"],
                "amount": [-100.0]
            })
            preprocessor.fit(train_instance._x_train)

            # Add required attributes
            train_instance._df = train_instance._x_train.copy()
            train_instance._df["category"] = "TestCategory"

            pipeline = Pipeline([("preprocessor", preprocessor), ("classifier", RandomForestClassifier())], memory=None)

            manifest = train_instance._create_manifest(pipeline)

            # Verify manifest structure
            assert "model_file" in manifest
            assert "model_version" in manifest
            assert "training_data" in manifest
            assert "training_date" in manifest
            assert "data_info" in manifest
            assert "parameters" in manifest
        finally:
            train_instance._config.enable_calibration = original_calibration

    def test_train_method_with_mock(self, ml_config_temp, sample_training_data):
        """Test train method with mocked pipeline fitting."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_training_data, f)
            temp_training_path = f.name

        try:
            train_instance = Train(temp_training_path, ml_config_temp)

            # Fit the preprocessor first to avoid NotFittedError in manifest creation
            train_instance._preprocessor.fit(train_instance._x_train)

            # Mock the pipeline fit method to avoid actual training
            with patch.object(train_instance._pipe, 'fit') as mock_fit:
                mock_fit.return_value = train_instance._pipe

                # Mock the save function to avoid file operations
                with patch('whatsthedamage.models.domain.machine_learning.save') as mock_save:
                    train_instance.train()

                    # Verify fit was called
                    mock_fit.assert_called_once()

                    # Verify save was called
                    mock_save.assert_called_once()

        finally:
            os.unlink(temp_training_path)


class TestMetricsClass:
    """Test the Metrics class."""

    def test_initialization_with_existing_model(self):
        """Test Metrics initialization with existing model file."""
        # Use the existing model file
        existing_model_path = "src/whatsthedamage/static/model-rf-v6alpha_en.joblib"
        existing_test_data_path = "src/whatsthedamage/static/model-rf-v6alpha_en.testdata.json"

        if os.path.exists(existing_model_path) and os.path.exists(existing_test_data_path):
            metrics = Metrics(existing_model_path, existing_test_data_path)

            # Verify attributes are set
            assert hasattr(metrics, 'model')
            assert hasattr(metrics, 'test_data')
            assert hasattr(metrics, 'x_test')
            assert hasattr(metrics, 'y_test')
            assert hasattr(metrics, 'y_pred')
            assert hasattr(metrics, 'y_proba')

            # Verify predictions were made
            assert len(metrics.y_pred) > 0
            assert len(metrics.y_proba) > 0
        else:
            pytest.skip("Existing model files not found")

    def test_get_metrics_data(self):
        """Test metrics data retrieval."""
        existing_model_path = "src/whatsthedamage/static/model-rf-v6alpha_en.joblib"
        existing_test_data_path = "src/whatsthedamage/static/model-rf-v6alpha_en.testdata.json"

        if os.path.exists(existing_model_path) and os.path.exists(existing_test_data_path):
            metrics = Metrics(existing_model_path, existing_test_data_path)
            metrics_data = metrics.get_metrics_data()

            # Verify expected keys are present
            expected_keys = [
                'accuracy', 'confusion_matrix', 'confusion_matrix_content',
                'classification_report', 'confused_pairs', 'confidence_analysis',
                'merchant_analysis', 'predictions', 'probabilities', 'test_samples'
            ]

            for key in expected_keys:
                assert key in metrics_data

            # Verify accuracy is a float between 0 and 1
            assert 0.0 <= metrics_data['accuracy'] <= 1.0

        else:
            pytest.skip("Existing model files not found")


class TestInferenceClass:
    """Test the Inference class."""

    def test_initialization_with_existing_model(self):
        """Test Inference initialization with existing model."""
        existing_model_path = "src/whatsthedamage/static/model-rf-v6alpha_en.joblib"

        if os.path.exists(existing_model_path):
            # Sample input data as JSON string (file path)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                input_data = [
                    {
                        "date": "2023-04-01",
                        "type": "Payment",
                        "partner": "Test Grocery Store",
                        "amount": -75.0,
                        "currency": "EUR"
                    }
                ]
                json.dump(input_data, f)
                temp_input_path = f.name

            try:
                inference = Inference(existing_model_path, temp_input_path)
            finally:
                os.unlink(temp_input_path)

            # Verify attributes are set
            assert hasattr(inference, 'model')
            assert hasattr(inference, 'df_input')
            assert hasattr(inference, 'df_output')

            # Verify predictions were made
            assert 'predicted_category' in inference.df_output.columns
            assert 'prediction_confidence' in inference.df_output.columns

        else:
            pytest.skip("Existing model file not found")

    def test_get_predictions(self):
        """Test get_predictions method."""
        existing_model_path = "src/whatsthedamage/static/model-rf-v6alpha_en.joblib"

        if os.path.exists(existing_model_path):
            # Sample input data as JSON string (file path)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                input_data = [
                    {
                        "date": "2023-04-01",
                        "type": "Payment",
                        "partner": "Test Grocery Store",
                        "amount": -75.0,
                        "currency": "EUR"
                    }
                ]
                json.dump(input_data, f)
                temp_input_path = f.name

            try:
                inference = Inference(existing_model_path, temp_input_path)
            finally:
                os.unlink(temp_input_path)
            predictions = inference.get_predictions()

            # Verify predictions are returned as CsvRow objects
            assert len(predictions) == 1
            assert all(isinstance(pred, CsvRow) for pred in predictions)

            # Verify each prediction has required attributes
            for pred in predictions:
                assert hasattr(pred, 'confidence')
                assert 0.0 <= pred.confidence <= 1.0

        else:
            pytest.skip("Existing model file not found")

    def test_prepare_input_data_with_csv_rows(self, csv_rows):
        """Test input data preparation with CsvRow objects."""
        existing_model_path = "src/whatsthedamage/static/model-rf-v6alpha_en.joblib"

        if os.path.exists(existing_model_path):
            # Inference expects either file path or List[CsvRow] - use the CsvRow list directly
            inference = Inference(existing_model_path, csv_rows)

            # Verify input data was prepared correctly
            assert len(inference.df_input) == 2
            assert 'type' in inference.df_input.columns
            assert 'partner' in inference.df_input.columns
            assert 'amount' in inference.df_input.columns

        else:
            pytest.skip("Existing model file not found")


# Integration Tests
class TestIntegration:
    """Integration tests for the ML workflow."""

    def test_end_to_end_workflow_with_temp_files(self, ml_config_temp, sample_training_data):
        """Test complete workflow from training to inference."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_training_data, f)
            temp_training_path = f.name

        try:
            # Train model
            train_instance = Train(temp_training_path, ml_config_temp)

            # Fit the preprocessor first to avoid NotFittedError in manifest creation
            train_instance._preprocessor.fit(train_instance._x_train)

            # Mock the save function to avoid file operations and pickling issues
            with patch('whatsthedamage.models.domain.machine_learning.save') as mock_save:
                # Mock training to avoid long execution
                with patch.object(train_instance._pipe, 'fit') as mock_fit:
                    mock_fit.return_value = train_instance._pipe
                    train_instance.train()

                    # Verify fit was called
                    mock_fit.assert_called_once()

                    # Verify save was called
                    mock_save.assert_called_once()

            # Test inference with trained model (using existing model since we mocked save)
            test_data = [
                {
                    "date": "2023-05-01",
                    "type": "Payment",
                    "partner": "Test Store",
                    "amount": -50.0,
                    "currency": "EUR"
                }
            ]

            # Use existing model for inference test
            existing_model_path = "src/whatsthedamage/static/model-rf-v6alpha_en.joblib"
            if os.path.exists(existing_model_path):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
                    json.dump(test_data, f2)
                    temp_test_path = f2.name

                try:
                    inference = Inference(existing_model_path, temp_test_path)
                    predictions = inference.get_predictions()

                    assert len(predictions) == 1
                    assert isinstance(predictions[0], CsvRow)
                finally:
                    os.unlink(temp_test_path)
            else:
                pytest.skip("Existing model file not found")

        finally:
            os.unlink(temp_training_path)

    def test_model_saving_loading_cycle(self, ml_config_temp):
        """Test model saving and loading cycle."""
        # Create a simple pipeline
        preprocessor = ColumnTransformer([
            ("test", TfidfVectorizer(), "test_col")
        ])
        classifier = RandomForestClassifier(random_state=42, n_estimators=2)
        pipeline = Pipeline([("preprocessor", preprocessor), ("classifier", classifier)], memory=None)

        # Fit with minimal data
        X_train = pd.DataFrame({"test_col": ["test1", "test2"]})
        y_train = ["cat1", "cat2"]
        pipeline.fit(X_train, y_train)

        # Save the model
        manifest = {"model_version": "test_v1", "training_date": "2023-01-01"}
        save(pipeline, manifest, ml_config_temp)

        # Load the model
        loaded_pipeline = load(ml_config_temp.model_path)

        # Verify loaded model works
        predictions = loaded_pipeline.predict(X_train)
        assert len(predictions) == 2

        # Verify manifest was saved correctly
        with open(ml_config_temp.manifest_path, 'r', encoding='utf-8') as f:
            loaded_manifest = json.load(f)
        assert loaded_manifest["model_version"] == "test_v1"


# Error Handling Tests
class TestErrorHandling:
    """Test error handling scenarios."""

    def test_train_with_invalid_data(self, ml_config_temp):
        """Test training with invalid/empty data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)  # Empty dataset
            temp_training_path = f.name

        try:
            with pytest.raises(ValueError, match="Loaded DataFrame is empty"):
                Train(temp_training_path, ml_config_temp)
        finally:
            os.unlink(temp_training_path)

    def test_metrics_with_missing_columns(self, ml_config_temp):
        """Test metrics with missing required columns."""
        existing_model_path = "src/whatsthedamage/static/model-rf-v6alpha_en.joblib"

        if os.path.exists(existing_model_path):
            # Create test data with missing columns
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                test_data = [{"amount": -50.0, "category": "Grocery"}]  # Missing type, partner
                json.dump(test_data, f)
                temp_test_path = f.name

            try:
                with pytest.raises(ValueError, match="Missing required columns"):
                    Metrics(existing_model_path, temp_test_path)
            finally:
                os.unlink(temp_test_path)
        else:
            pytest.skip("Existing model file not found")

    def test_inference_with_empty_data(self, ml_config_temp):
        """Test inference with empty input data."""
        existing_model_path = "src/whatsthedamage/static/model-rf-v6alpha_en.joblib"

        if os.path.exists(existing_model_path):
            with pytest.raises(ValueError, match="Input DataFrame is empty"):
                Inference(existing_model_path, [])
        else:
            pytest.skip("Existing model file not found")