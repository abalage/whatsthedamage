# src/whatsthedamage/models/test_machine_learning.py
import pytest
import pandas as pd
import numpy as np
import os
import json
from unittest import mock

from whatsthedamage.models.machine_learning import (
    load_json_data,
    save,
    load,
    MLConfig,
    TrainingData,
    Train,
    Inference
)


@pytest.fixture
def valid_json(tmp_path):
    data = [
        {"type": "A", "partner": "B", "currency": "EUR", "amount": 10, "category": "X"},
        {"type": "C", "partner": "D", "currency": "USD", "amount": 20, "category": "Y"},
        {"type": "E", "partner": "F", "currency": "GBP", "amount": 30, "category": "Z"}
    ]
    file = tmp_path / "data.json"
    file.write_text(json.dumps(data), encoding="utf-8")
    return str(file), data


@pytest.fixture
def train_obj_not_enough_data(tmp_path):
    # Only one sample per class
    data = [
        {"type": "A", "partner": "B", "currency": "EUR", "amount": 10, "category": "X"},
        {"type": "C", "partner": "D", "currency": "USD", "amount": 20, "category": "Y"}
    ]
    config = MLConfig()
    config.feature_columns = ["type", "partner", "currency", "amount"]
    with mock.patch.object(TrainingData, "__init__", lambda self, p, config: None), \
         mock.patch.object(TrainingData, "get_training_data", return_value=pd.DataFrame(data)):
        yield lambda: Train("dummy_path", config)


@pytest.fixture
def train_obj_enough_data(tmp_path):
    # At least five samples per class, with non-empty, non-stopword text fields
    data = [
        {"type": "Alpha", "partner": "Bravo", "currency": "EUR", "amount": 10, "category": "X"},
        {"type": "Charlie", "partner": "Delta", "currency": "USD", "amount": 20, "category": "Y"},
        {"type": "Echo", "partner": "Foxtrot", "currency": "EUR", "amount": 30, "category": "X"},
        {"type": "Golf", "partner": "Hotel", "currency": "USD", "amount": 40, "category": "Y"},
        {"type": "India", "partner": "Juliet", "currency": "EUR", "amount": 50, "category": "X"},
        {"type": "Kilo", "partner": "Lima", "currency": "USD", "amount": 60, "category": "Y"},
        {"type": "Mike", "partner": "November", "currency": "EUR", "amount": 70, "category": "X"},
        {"type": "Oscar", "partner": "Papa", "currency": "USD", "amount": 80, "category": "Y"},
        {"type": "Quebec", "partner": "Romeo", "currency": "EUR", "amount": 90, "category": "X"},
        {"type": "Sierra", "partner": "Tango", "currency": "USD", "amount": 100, "category": "Y"},
    ]
    config = MLConfig()
    config.feature_columns = ["type", "partner", "currency", "amount"]
    with mock.patch.object(TrainingData, "__init__", lambda self, p, config: None), \
         mock.patch.object(TrainingData, "get_training_data", return_value=pd.DataFrame(data)):
        yield Train("dummy_path", config)


@pytest.fixture
def inference_obj(tmp_path):
    # Create test data that matches the expected input format
    data = [
        {"type": "Alpha", "partner": "Bravo", "currency": "EUR", "amount": 10},
        {"type": "Charlie", "partner": "Delta", "currency": "USD", "amount": 20}
    ]
    file = tmp_path / "input.json"
    file.write_text(json.dumps(data), encoding="utf-8")
    config = MLConfig()
    config.feature_columns = ["type", "partner", "currency", "amount"]

    # Mock model with predict and predict_proba
    dummy_model = mock.Mock()
    dummy_model.predict.return_value = ["X", "Y"]
    dummy_model.predict_proba.return_value = np.array([[0.99, 0.01], [0.95, 0.05]])

    # Patch the model loading
    with mock.patch("whatsthedamage.models.machine_learning.load", return_value=dummy_model):
        obj = Inference(str(file), config)
        return obj


@pytest.fixture
def prediction_data():
    data = [
        {"type": "Alpha", "partner": "Bravo", "currency": "EUR", "amount": 10, "category": "X"},
        {"type": "Charlie", "partner": "Delta", "currency": "USD", "amount": 20, "category": "Y"}
    ]
    return data


def test_load_json_data_valid(valid_json):
    path, expected = valid_json
    result = load_json_data(path)
    assert result == expected


def test_load_json_data_file_not_found(tmp_path):
    non_existent_file = tmp_path / "nonexistent.json"
    result = load_json_data(str(non_existent_file))
    assert result is None


def test_load_json_data_invalid_json(tmp_path):
    invalid_json_file = tmp_path / "invalid.json"
    invalid_json_file.write_text("{invalid json}", encoding="utf-8")
    result = load_json_data(str(invalid_json_file))
    assert result is None


def test_load_json_data_unexpected_error(tmp_path):
    # Simulate a permission error by creating a file and removing read permissions
    restricted_file = tmp_path / "restricted.json"
    restricted_file.write_text("{}", encoding="utf-8")
    restricted_file.chmod(0o000)  # Remove all permissions

    try:
        result = load_json_data(str(restricted_file))
        assert result is None
    finally:
        # Restore permissions to clean up the file
        restricted_file.chmod(0o644)


def test_save_and_load(tmp_path):
    dummy_model = mock.Mock()  # Use a mock object to simulate a Pipeline
    manifest = {"foo": "bar"}
    output_dir = str(tmp_path)
    classifier_short_name = "rf"
    model_version = "v1"
    model_filename = f"model-{classifier_short_name}-{model_version}.joblib"

    with mock.patch("joblib.dump") as mock_dump, \
         mock.patch("builtins.open", mock.mock_open()) as mock_file:
        save(dummy_model, output_dir, manifest, classifier_short_name, model_version)
        mock_dump.assert_called_once()
        handle = mock_file()
        handle.write.assert_called()

    # Test load
    with mock.patch("joblib.load", return_value="loaded_model"):
        result = load(os.path.join(output_dir, model_filename))
        assert result == "loaded_model"


def test_mlconfig_defaults():
    config = MLConfig()
    assert config.classifier_short_name == "rf"
    assert "type" in config.feature_columns


def test_mlconfig_custom():
    config = MLConfig(classifier_short_name="abc", feature_columns=["foo", "bar"])
    assert config.classifier_short_name == "abc"
    assert config.feature_columns == ["foo", "bar"]


def test_trainingdata_valid(valid_json):
    path, data = valid_json
    config = MLConfig()
    config.feature_columns = ["type", "partner", "currency", "amount"]
    td = TrainingData(path, config)
    df = td.get_training_data()
    assert not df.empty
    assert set(config.feature_columns).issubset(df.columns)


def test_trainingdata_missing_columns(tmp_path):
    data = [{"type": "A", "partner": "B"}]
    file = tmp_path / "data.json"
    file.write_text(json.dumps(data), encoding="utf-8")
    config = MLConfig()
    config.feature_columns = ["type", "partner", "currency", "amount"]
    with pytest.raises(ValueError, match="Missing required columns.*"):
        TrainingData(str(file), config)


def test_trainingdata_empty(tmp_path):
    file = tmp_path / "data.json"
    file.write_text(json.dumps([]), encoding="utf-8")
    config = MLConfig()
    config.feature_columns = ["type", "partner", "currency", "amount"]
    with pytest.raises(ValueError, match="Loaded DataFrame is empty."):
        TrainingData(str(file), config)


def test_trainingdata_missing_values(tmp_path):
    data = [{"type": "A", "partner": None, "currency": "EUR", "amount": 10, "category": "X"}]
    file = tmp_path / "data.json"
    file.write_text(json.dumps(data), encoding="utf-8")
    config = MLConfig()
    config.feature_columns = ["type", "partner", "currency", "amount"]
    with pytest.raises(ValueError, match="All rows were dropped due to missing values."):
        TrainingData(str(file), config)


def test_train_pipeline_creation(train_obj_enough_data):
    pipe = train_obj_enough_data._create_pipeline()
    assert hasattr(pipe, "fit")


def test_train_train_method(train_obj_enough_data):
    with mock.patch.object(train_obj_enough_data.pipe, "fit") as mock_fit, \
         mock.patch.object(train_obj_enough_data, "evaluate") as mock_eval, \
         mock.patch("joblib.dump"), \
         mock.patch("builtins.open", mock.mock_open()), \
         mock.patch.object(
            train_obj_enough_data.pipe.named_steps["preprocessor"], "transform",
            return_value=np.zeros(
                (len(train_obj_enough_data.X_train), len(train_obj_enough_data.config.feature_columns))
            )
         ) as mock_transform:
        train_obj_enough_data.train()
        mock_fit.assert_called()
        mock_eval.assert_called()
        mock_transform.assert_called()


def test_train_hyperparameter_tuning(train_obj_enough_data):
    with mock.patch("sklearn.model_selection.GridSearchCV") as mock_grid, \
         mock.patch("sklearn.model_selection.RandomizedSearchCV") as mock_rand, \
         mock.patch.object(train_obj_enough_data, "evaluate"), \
         mock.patch.object(train_obj_enough_data.pipe, "fit", return_value=None):
        mock_grid.return_value.fit.return_value = None
        mock_grid.return_value.best_params_ = {"foo": "bar"}
        mock_grid.return_value.best_estimator_ = train_obj_enough_data.pipe
        train_obj_enough_data.hyperparameter_tuning("grid")
        mock_rand.return_value.fit.return_value = None
        mock_rand.return_value.best_params_ = {"foo": "bar"}
        mock_rand.return_value.best_estimator_ = train_obj_enough_data.pipe
        train_obj_enough_data.hyperparameter_tuning("random")
        train_obj_enough_data.hyperparameter_tuning("none")


def test_train_evaluate(train_obj_enough_data):
    train_obj_enough_data.model = mock.Mock()
    train_obj_enough_data.y_test = pd.Series(["X"])
    train_obj_enough_data.X_test = pd.DataFrame([{"type": "A", "partner": "B", "currency": "EUR", "amount": 10}])
    train_obj_enough_data.model.predict.return_value = ["X"]
    with mock.patch("sklearn.metrics.accuracy_score", return_value=1.0), \
         mock.patch("sklearn.metrics.classification_report", return_value="report"):
        train_obj_enough_data.evaluate()


def test_train_not_enough_class_samples(train_obj_not_enough_data):
    with pytest.raises(ValueError, match="Each class must have at least 2 samples"):
        train_obj_not_enough_data()


def test_inference_get_predictions(inference_obj):
    predictions = inference_obj.get_predictions()
    assert isinstance(predictions, list)
    assert len(predictions) == 2  # We expect 2 predictions based on our test data
    assert all(hasattr(row, 'category') for row in predictions)  # Check that category attribute exists
    cats = [row.category for row in predictions]
    assert cats == ["X", "Y"]


def test_inference_print_inference_data(capsys, inference_obj):
    inference_obj.print_inference_data(with_confidence=True)
    captured = capsys.readouterr()
    assert "predicted_category" in captured.out
    assert "prediction_confidence" in captured.out


def test_prepare_input_data_empty_json(tmp_path):
    file = tmp_path / "empty.json"
    file.write_text(json.dumps([]), encoding="utf-8")
    with pytest.raises(ValueError, match="Input DataFrame is empty."):
        Inference(new_data=str(file))


def test_prepare_input_data_empty_list():
    data = []
    with pytest.raises(ValueError, match="Input DataFrame is empty."):
        Inference(new_data=data)


def test_prepare_input_data_invalid_type():
    with pytest.raises(ValueError, match="Input must be a JSON file path or a List\\[dict\\]."):
        Inference(new_data=12345)


def test_prepare_input_data_partial_data(tmp_path):
    data = [{"type": "A", "partner": "B"}]  # Missing required columns
    file = tmp_path / "partial.json"
    file.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="columns are missing:.*"):
        Inference(new_data=str(file))
