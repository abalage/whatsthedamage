"""Test ML configuration integration with AppConfig."""
import tempfile
import pytest
from whatsthedamage.config.config import load_config, AppConfig


def test_ml_config_default_values(ml_config):
    """Test that MLConfig has correct default values."""
    # Test using the fixture
    assert ml_config.ml_confidence_threshold == pytest.approx(0.65)
    assert ml_config.enable_calibration
    assert ml_config.calibration_method == "sigmoid"


def test_ml_config_custom_threshold(custom_ml_config):
    """Test that custom ML confidence threshold can be set."""
    # Test using the custom fixture
    assert custom_ml_config.ml_confidence_threshold == pytest.approx(0.7)


def test_appconfig_includes_ml_config(ml_config):
    """Test that AppConfig includes MLConfig with default values."""
    app_config = AppConfig(
        csv={},
        enricher_pattern_sets={}
    )
    assert hasattr(app_config, 'ml_config')
    # Compare against the fixture value, not hardcoded value
    assert app_config.ml_config.ml_confidence_threshold == pytest.approx(ml_config.ml_confidence_threshold)


def test_ml_config_from_yaml():
    """Test loading ML configuration from YAML file."""
    yaml_content = """
csv:
  dialect: excel
  delimiter: ','
  date_attribute_format: '%Y-%m-%d'
enricher_pattern_sets:
  type: {}
  partner: {}
ml_config:
  ml_confidence_threshold: 0.7
  enable_calibration: false
  calibration_method: isotonic
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(yaml_content)
        config_path = f.name
    
    try:
        config = load_config(config_path)
        assert config.ml_config.ml_confidence_threshold == pytest.approx(0.7)
        assert not config.ml_config.enable_calibration
        assert config.ml_config.calibration_method == "isotonic"
    finally:
        import os
        os.unlink(config_path)


def test_ml_config_default_when_not_in_yaml(ml_config):
    """Test that MLConfig uses defaults when not specified in YAML."""
    yaml_content = """
csv:
  dialect: excel
  delimiter: ','
  date_attribute_format: '%Y-%m-%d'
enricher_pattern_sets:
  type: {}
  partner: {}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(yaml_content)
        config_path = f.name
    
    try:
        config = load_config(config_path)
        # Compare against the fixture's default value, not hardcoded 0.5
        assert config.ml_config.ml_confidence_threshold == pytest.approx(ml_config.ml_confidence_threshold)
        assert config.ml_config.enable_calibration
    finally:
        import os
        os.unlink(config_path)
