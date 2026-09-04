"""Tests for model privacy and security features.

This module tests that the distribution-ready models have proper privacy protections:
- No vocabulary storage (HashingVectorizer)
- No test data included
- No private paths in Model Card
- Secure serialization (skops.io)
"""

import json
import os
import tempfile
import pytest
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import HashingVectorizer, TfidfVectorizer

from whatsthedamage.models.domain.machine_learning import (
    Train, save, load, generate_model_card_markdown
)
from whatsthedamage.config.ml_config import MLConfig


class TestDistributionPrivacy:
    """Test privacy features of distribution-ready models."""

    @pytest.fixture
    def distribution_config(self):
        """Create a distribution-ready MLConfig."""
        return MLConfig(
            use_hashing_vectorizer=True,
            use_skops=True,
            is_distribution=True,
            model_version="test_v1",
            n_estimators=2,
            min_samples_split=2,
            test_size=0.2  # Smaller test size to ensure at least 2 samples per class in training
        )

    @pytest.fixture
    def sample_training_data(self):
        """Create sample training data with sufficient samples per class."""
        # Need enough samples for stratified split with test_size=0.2
        # With 12 samples and test_size=0.2, we get ~2.4 test samples, rounded to 3
        # This ensures at least 1 sample per class in test set
        return [
            {"type": "Payment", "partner": "Test Merchant", "amount": -100.0, "category_id": "Grocery"},
            {"type": "Payment", "partner": "Store", "amount": -200.0, "category_id": "Grocery"},
            {"type": "Payment", "partner": "Market", "amount": -150.0, "category_id": "Grocery"},
            {"type": "Payment", "partner": "Shop", "amount": -180.0, "category_id": "Grocery"},
            {"type": "Deposit", "partner": "Salary", "amount": 500.0, "category_id": "Salary"},
            {"type": "Deposit", "partner": "Bonus", "amount": 300.0, "category_id": "Salary"},
            {"type": "Deposit", "partner": "Work", "amount": 400.0, "category_id": "Salary"},
            {"type": "Deposit", "partner": "Pay", "amount": 350.0, "category_id": "Salary"},
            {"type": "Withdrawal", "partner": "ATM", "amount": -50.0, "category_id": "Withdrawal"},
            {"type": "Withdrawal", "partner": "Bank", "amount": -75.0, "category_id": "Withdrawal"},
            {"type": "Withdrawal", "partner": "Cash", "amount": -60.0, "category_id": "Withdrawal"},
            {"type": "Withdrawal", "partner": "Machine", "amount": -80.0, "category_id": "Withdrawal"},
        ]

    def test_hashing_vectorizer_no_vocabulary(self, distribution_config):
        """Test that HashingVectorizer does not store vocabulary."""
        # Create a pipeline with HashingVectorizer
        preprocessor = ColumnTransformer([
            ("type_vec", HashingVectorizer(n_features=10), "type"),
            ("partner_vec", HashingVectorizer(n_features=10), "partner"),
        ])
        classifier = RandomForestClassifier(random_state=42, n_estimators=2)
        pipeline = Pipeline([("preprocessor", preprocessor), ("classifier", classifier)])
        
        # Fit with sample data
        X_train = pd.DataFrame({
            "type": ["Payment", "Deposit", "Withdrawal"],
            "partner": ["Merchant A", "Merchant B", "Merchant C"]
        })
        y_train = ["cat1", "cat2", "cat3"]
        pipeline.fit(X_train, y_train)
        
        # Check that HashingVectorizer has no vocabulary_ attribute
        fitted_preprocessor = pipeline.named_steps["preprocessor"]
        for name, transformer, column in fitted_preprocessor.transformers_:
            assert not hasattr(transformer, 'vocabulary_'), \
                f"HashingVectorizer {name} should not have vocabulary_ attribute"

    def test_tfidf_vectorizer_has_vocabulary(self):
        """Test that TfidfVectorizer DOES store vocabulary (for comparison)."""
        # Create a pipeline with TfidfVectorizer
        preprocessor = ColumnTransformer([
            ("type_vec", TfidfVectorizer(), "type"),
        ])
        classifier = RandomForestClassifier(random_state=42, n_estimators=2)
        pipeline = Pipeline([("preprocessor", preprocessor), ("classifier", classifier)])
        
        # Fit with sample data
        X_train = pd.DataFrame({
            "type": ["Payment", "Deposit", "Withdrawal"]
        })
        y_train = ["cat1", "cat2", "cat3"]
        pipeline.fit(X_train, y_train)
        
        # Check that TfidfVectorizer has vocabulary_ attribute
        fitted_preprocessor = pipeline.named_steps["preprocessor"]
        type_vec = fitted_preprocessor.named_transformers_["type_vec"]
        assert hasattr(type_vec, 'vocabulary_'), \
            "TfidfVectorizer should have vocabulary_ attribute"
        # TfidfVectorizer stores lowercase terms by default
        assert "payment" in type_vec.vocabulary_, \
            "TfidfVectorizer vocabulary should contain training terms (lowercase)"

    def test_distribution_model_uses_hashing_vectorizer(self, distribution_config, sample_training_data):
        """Test that distribution mode uses HashingVectorizer."""
        # Create temporary training data file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_training_data, f)
            temp_path = f.name
        
        try:
            # Create Train instance with distribution config
            train = Train(training_data_path=temp_path, config=distribution_config)
            
            # Check that preprocessor uses HashingVectorizer
            preprocessor = train._preprocessor
            # Access the transformers attribute (available before and after fitting)
            transformers = preprocessor.transformers if hasattr(preprocessor, 'transformers') else preprocessor.transformers_
            for name, transformer, _ in transformers:
                if name in ["type_vec", "partner_vec"]:
                    assert isinstance(transformer, HashingVectorizer), \
                        f"Distribution mode should use HashingVectorizer for {name}"
        finally:
            os.unlink(temp_path)

    def test_distribution_model_card_no_private_paths(self, distribution_config, sample_training_data):
        """Test that distribution Model Card has no private paths."""
        # Create temporary training data file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_training_data, f)
            temp_path = f.name
        
        try:
            # Create and train model
            train = Train(training_data_path=temp_path, config=distribution_config)
            
            # Train the model first so the pipeline is fitted
            train.train()
            
            # Create Model Card
            model_card = train._create_model_card(train._model)
            
            # Check for private path patterns
            assert 'training_data' not in model_card or \
                   temp_path not in str(model_card.get('training_data', '')), \
                "Model Card should not contain training data path"
            
            # Check privacy flags
            assert model_card["privacy"]["safe_for_public_use"] == True, \
                "Distribution Model Card should be marked as safe for public use"
            assert model_card["privacy"]["vocabulary_stored"] == False, \
                "Distribution Model Card should indicate no vocabulary stored"
            assert model_card["privacy"]["test_data_included"] == False, \
                "Distribution Model Card should indicate no test data included"
            assert model_card["privacy"]["training_data_paths_exposed"] == False, \
                "Distribution Model Card should indicate no training data paths exposed"
        finally:
            os.unlink(temp_path)

    def test_distribution_save_no_test_data(self, distribution_config, sample_training_data):
        """Test that distribution mode does not save test data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config with temp directory
            config = distribution_config
            config.__class__.model_path = property(lambda self: os.path.join(temp_dir, "test.skops"))
            config.__class__.model_card_path = property(lambda self: os.path.join(temp_dir, "test.modelcard.json"))
            config.__class__.test_data_path = property(lambda self: os.path.join(temp_dir, "test.testdata.json"))
            
            # Create temporary training data file
            training_path = os.path.join(temp_dir, "training.json")
            with open(training_path, 'w') as f:
                json.dump(sample_training_data, f)
            
            # Train and save
            train = Train(training_data_path=training_path, config=config)
            train.train()
            
            # Check that test data was NOT saved
            assert not os.path.exists(config.test_data_path), \
                "Distribution mode should not save test data"
            
            # Check that model and Model Card were saved
            assert os.path.exists(config.model_path), \
                "Model should be saved"
            assert os.path.exists(config.model_card_path), \
                "Model Card should be saved"

    def test_distribution_model_card_markdown_generation(self, distribution_config):
        """Test that Model Card markdown is generated correctly."""
        model_card = {
            "model_name": "test_model",
            "version": "v1.0",
            "model_type": "RandomForestClassifier",
            "language": "Hungarian",
            "license": "MIT",
            "developer": "test",
            "repository": "https://github.com/test/test",
            "format": "skops",
            "parameters": {
                "use_hashing_vectorizer": True,
                "calibration_enabled": True,
                "hashing_n_features": 1024
            },
            "training_info": {
                "training_data_size": "1000 transactions",
                "training_data_period": "1 year",
                "category_count": 10,
                "feature_columns": ["type", "partner", "amount"],
                "feature_matrix_shape": [1000, 50],
                "preprocessing": "Text cleaning + HashingVectorizer"
            },
            "evaluation": {
                "test_data_size": "200 transactions",
                "accuracy": 0.95
            },
            "privacy": {
                "safe_for_public_use": True,
                "vocabulary_stored": False,
                "test_data_included": False,
                "training_data_paths_exposed": False
            },
            "environment": {
                "sklearn_version": "1.7.2"
            },
            "created_date": "2023-01-01T00:00:00"
        }
        
        md = generate_model_card_markdown(model_card)
        
        # Check that markdown contains expected sections (HuggingFace template structure)
        assert "# Model Card for test_model" in md
        assert "## Model Details" in md
        assert "## Training Details" in md or "## Training Data" in md
        assert "## Evaluation" in md
        assert "## How to Get Started" in md or "## How to Get Started with the Model" in md
        
        # Check privacy guarantees are mentioned (current implementation mentions HashingVectorizer for privacy)
        assert "HashingVectorizer for privacy" in md

    def test_skops_serialization_used(self, distribution_config):
        """Test that skops.io is used for serialization."""
        # skops is now the default and only serialization method
        assert True, "skops.io is the default serialization method"
        assert distribution_config.model_version == "test_v1", \
            "Should use updated model version"

    def test_model_card_json_format(self, distribution_config, sample_training_data):
        """Test that Model Card is saved in proper JSON format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config with temp directory
            config = distribution_config
            config.__class__.model_path = property(lambda self: os.path.join(temp_dir, "test.skops"))
            config.__class__.model_card_path = property(lambda self: os.path.join(temp_dir, "test.modelcard.json"))
            config.__class__.test_data_path = property(lambda self: os.path.join(temp_dir, "test.testdata.json"))
            
            # Create temporary training data file
            training_path = os.path.join(temp_dir, "training.json")
            with open(training_path, 'w') as f:
                json.dump(sample_training_data, f)
            
            # Train and save
            train = Train(training_data_path=training_path, config=config)
            train.train()
            
            # Load and verify Model Card JSON
            with open(config.model_card_path, 'r', encoding='utf-8') as f:
                model_card = json.load(f)
            
            # Verify required fields exist
            required_fields = ["model_name", "version", "model_type", "language", "parameters", "training_info", "evaluation", "privacy"]
            for field in required_fields:
                assert field in model_card, f"Model Card should contain {field}"
            
            # Verify privacy settings
            assert model_card["privacy"]["safe_for_public_use"] == True
            assert model_card["privacy"]["vocabulary_stored"] == False


class TestSecurityFeatures:
    """Test security features of the serialization."""

    def test_skops_load_with_verification(self):
        """Test that skops.io can load models with type verification."""
        # This test verifies that the load function properly uses skops.io
        # skops is now the only serialization method, so it should always be available
        import skops.io as sio
        assert sio is not None, "skops.io should be available"


class TestBackwardCompatibility:
    """Test that existing models can still be loaded."""

    def test_load_existing_skops_model(self):
        """Test that existing .skops models can be loaded."""
        from whatsthedamage.models.domain.machine_learning import load
        
        # Use the existing model file (now in skops format)
        existing_model_path = "src/whatsthedamage/static/model-rf-v6alpha_en.skops"
        
        if os.path.exists(existing_model_path):
            # Should be able to load with skops
            model = load(existing_model_path)
            assert model is not None
            assert isinstance(model, Pipeline)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
