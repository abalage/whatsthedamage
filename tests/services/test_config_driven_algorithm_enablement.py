"""Tests for config-driven algorithm enablement functionality."""

import pytest
import yaml
import tempfile
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService
from whatsthedamage.services.configuration_service import ConfigurationService

class TestConfigDrivenAlgorithmEnablement:
    """Tests for config-driven algorithm enablement."""

    @pytest.fixture
    def config_service(self):
        """Create ConfigurationService instance."""
        return ConfigurationService()

    @pytest.fixture
    def sample_config_data(self):
        """Sample configuration data with algorithm settings."""
        return {
            "csv": {
                "dialect": "excel",
                "delimiter": ",",
                "date_attribute_format": "%Y-%m-%d",
                "attribute_mapping": {
                    "date": "date",
                    "amount": "amount"
                }
            },
            "enricher_pattern_sets": {
                "type": {},
                "partner": {}
            },
            "enabled_statistical_algorithms": ["iqr", "pareto"],
            "cache_ttl": 600
        }

    def test_config_loading_with_algorithms_enabled(self, config_service, sample_config_data):
        """Test loading config with algorithms enabled."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as config_file:
            yaml.dump(sample_config_data, config_file)
            config_file_path = config_file.name

        try:
            # Load config
            result = config_service.load_config(config_file_path)

            # Verify config loaded successfully
            assert result.config is not None
            assert result.validation_result.is_valid is True

            # Verify algorithm configuration
            config = result.config
            assert hasattr(config, 'enabled_statistical_algorithms')
            assert config.enabled_statistical_algorithms == ["iqr", "pareto"]

        finally:
            # Clean up temp file
            import os
            os.unlink(config_file_path)

    def test_config_loading_with_partial_algorithms(self, config_service, sample_config_data):
        """Test loading config with only some algorithms enabled."""
        # Modify to enable only IQR
        sample_config_data["enabled_statistical_algorithms"] = ["iqr"]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as config_file:
            yaml.dump(sample_config_data, config_file)
            config_file_path = config_file.name

        try:
            # Load config
            result = config_service.load_config(config_file_path)

            # Verify config loaded successfully
            assert result.config is not None
            assert result.validation_result.is_valid is True

            # Verify algorithm configuration
            config = result.config
            assert config.enabled_statistical_algorithms == ["iqr"]

        finally:
            # Clean up temp file
            import os
            os.unlink(config_file_path)

    def test_config_loading_with_empty_algorithms(self, config_service, sample_config_data):
        """Test loading config with empty algorithm list."""
        # Modify to have empty algorithm list
        sample_config_data["enabled_statistical_algorithms"] = []

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as config_file:
            yaml.dump(sample_config_data, config_file)
            config_file_path = config_file.name

        try:
            # Load config
            result = config_service.load_config(config_file_path)

            # Verify config loaded successfully
            assert result.config is not None
            assert result.validation_result.is_valid is True

            # Verify algorithm configuration
            config = result.config
            assert config.enabled_statistical_algorithms == []

        finally:
            # Clean up temp file
            import os
            os.unlink(config_file_path)

    def test_config_loading_with_missing_algorithms_key(self, config_service, sample_config_data):
        """Test loading config without algorithms key (should use default)."""
        # Remove the algorithms key
        if "enabled_statistical_algorithms" in sample_config_data:
            del sample_config_data["enabled_statistical_algorithms"]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as config_file:
            yaml.dump(sample_config_data, config_file)
            config_file_path = config_file.name

        try:
            # Load config
            result = config_service.load_config(config_file_path)

            # Verify config loaded successfully
            assert result.config is not None
            assert result.validation_result.is_valid is True

            # Verify default algorithm configuration
            config = result.config
            assert config.enabled_statistical_algorithms == ["iqr", "pareto"]  # Default

        finally:
            # Clean up temp file
            import os
            os.unlink(config_file_path)

    def test_statistical_service_integration_with_config(self, config_service):
        """Test StatisticalAnalysisService integration with config-driven enablement."""
        # Create config with specific algorithms
        config_data = {
            "csv": {"dialect": "excel", "delimiter": ",", "date_attribute_format": "%Y-%m-%d", "attribute_mapping": {}},
            "enricher_pattern_sets": {"type": {}, "partner": {}},
            "enabled_statistical_algorithms": ["iqr"],  # Only IQR enabled
            "cache_ttl": 600
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as config_file:
            yaml.dump(config_data, config_file)
            config_file_path = config_file.name

        try:
            # Load config
            result = config_service.load_config(config_file_path)
            config = result.config

            # Create statistical service with config-driven algorithms
            service = StatisticalAnalysisService(enabled_algorithms=config.enabled_statistical_algorithms)

            # Verify service is configured correctly
            assert service.enabled_algorithms == ["iqr"]
            assert "pareto" not in service.enabled_algorithms

            # Test that only IQR algorithm is used
            test_data = {
                "outlier": 1000.0,  # Should be detected by IQR
                "normal1": 10.0,
                "normal2": 20.0,
                "pareto_candidate": 50.0  # Would be pareto but algorithm is disabled
            }

            highlights = service.analyze(test_data)

            # Should only have IQR highlights, no pareto
            assert "outlier" in highlights
            assert highlights["outlier"] == "outlier"
            assert "pareto_candidate" not in highlights

        finally:
            # Clean up temp file
            import os
            os.unlink(config_file_path)

    def test_statistical_service_with_all_algorithms_disabled(self, config_service):
        """Test StatisticalAnalysisService with all algorithms disabled."""
        # Create config with empty algorithm list
        config_data = {
            "csv": {"dialect": "excel", "delimiter": ",", "date_attribute_format": "%Y-%m-%d", "attribute_mapping": {}},
            "enricher_pattern_sets": {"type": {}, "partner": {}},
            "enabled_statistical_algorithms": [],  # No algorithms enabled
            "cache_ttl": 600
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as config_file:
            yaml.dump(config_data, config_file)
            config_file_path = config_file.name

        try:
            # Load config
            result = config_service.load_config(config_file_path)
            config = result.config

            # Create statistical service with no algorithms
            service = StatisticalAnalysisService(enabled_algorithms=config.enabled_statistical_algorithms)

            # Verify service has no algorithms enabled
            assert len(service.enabled_algorithms) == 0

            # Test that no highlights are generated
            test_data = {
                "outlier": 1000.0,
                "pareto_candidate": 50.0,
                "normal": 10.0
            }

            highlights = service.analyze(test_data)
            assert highlights == {}  # No highlights when no algorithms enabled

        finally:
            # Clean up temp file
            import os
            os.unlink(config_file_path)

    def test_config_validation_with_invalid_algorithm_names(self, config_service):
        """Test config loading with invalid algorithm names."""
        # Create config with invalid algorithm names
        config_data = {
            "csv": {"dialect": "excel", "delimiter": ",", "date_attribute_format": "%Y-%m-%d", "attribute_mapping": {}},
            "enricher_pattern_sets": {"type": {}, "partner": {}},
            "enabled_statistical_algorithms": ["iqr", "invalid_algo", "pareto"],  # Contains invalid
            "cache_ttl": 600
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as config_file:
            yaml.dump(config_data, config_file)
            config_file_path = config_file.name

        try:
            # Load config - should still succeed (validation happens at service level)
            result = config_service.load_config(config_file_path)

            # Verify config loaded successfully
            assert result.config is not None
            assert result.validation_result.is_valid is True

            # Verify algorithm configuration includes invalid names
            config = result.config
            assert "invalid_algo" in config.enabled_statistical_algorithms

            # Test that service gracefully handles invalid algorithm names
            service = StatisticalAnalysisService(enabled_algorithms=config.enabled_statistical_algorithms)

            test_data = {"item1": 10.0, "item2": 20.0}
            highlights = service.analyze(test_data)

            # Should only process valid algorithms, ignore invalid ones
            # In this case, pareto should work with this data (both items contribute to 80%)
            assert len(highlights) == 2  # Both items should be pareto
            assert "item1" in highlights
            assert "item2" in highlights
            assert highlights["item1"] == "pareto"
            assert highlights["item2"] == "pareto"

        finally:
            # Clean up temp file
            import os
            os.unlink(config_file_path)

    def test_default_config_algorithms(self, config_service):
        """Test that default config has expected algorithm settings."""
        # Get default config
        config = config_service.get_default_config()

        # Verify default algorithm configuration
        assert hasattr(config, 'enabled_statistical_algorithms')
        assert config.enabled_statistical_algorithms == ["iqr", "pareto"]

        # Test service with default config
        service = StatisticalAnalysisService(enabled_algorithms=config.enabled_statistical_algorithms)

        # Verify both algorithms are enabled
        assert len(service.enabled_algorithms) == 2
        assert "iqr" in service.enabled_algorithms
        assert "pareto" in service.enabled_algorithms

    def test_config_integration_with_service_creation(self, config_service):
        """Test full integration from config loading to service creation."""
        # Create a comprehensive config
        config_data = {
            "csv": {
                "dialect": "excel",
                "delimiter": ",",
                "date_attribute_format": "%Y-%m-%d",
                "attribute_mapping": {
                    "date": "transaction_date",
                    "amount": "transaction_amount"
                }
            },
            "enricher_pattern_sets": {
                "type": {"food": ["grocery", "restaurant"]},
                "partner": {"grocery": ["WALMART", "TESCO"]}
            },
            "enabled_statistical_algorithms": ["pareto"],  # Only pareto
            "cache_ttl": 300
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as config_file:
            yaml.dump(config_data, config_file)
            config_file_path = config_file.name

        try:
            # Load config
            result = config_service.load_config(config_file_path)
            config = result.config

            # Create service with config-driven algorithms
            service = StatisticalAnalysisService(enabled_algorithms=config.enabled_statistical_algorithms)

            # Test with data that would trigger both algorithms if both were enabled
            # Use data where pareto items will actually be detected
            test_data = {
                "item1": 600.0,    # Should be pareto
                "item2": 400.0,    # Should be pareto
                "item3": 100.0,    # Should not be pareto
                "item4": 50.0      # Normal
            }

            highlights = service.analyze(test_data)

            # Should only have pareto highlights (IQR disabled)
            assert "item1" in highlights
            assert "item2" in highlights
            assert highlights["item1"] == "pareto"
            assert highlights["item2"] == "pareto"
            assert "item3" not in highlights  # Not in top 80%

        finally:
            # Clean up temp file
            import os
            os.unlink(config_file_path)

class TestAlgorithmEnablementEdgeCases:
    """Tests for edge cases in algorithm enablement."""

    def test_service_with_none_algorithms(self):
        """Test service initialization with None algorithms."""
        # Should use default algorithms when None is passed
        service = StatisticalAnalysisService(enabled_algorithms=None)

        assert len(service.enabled_algorithms) == 2
        assert "iqr" in service.enabled_algorithms
        assert "pareto" in service.enabled_algorithms

    def test_service_with_duplicate_algorithms(self):
        """Test service with duplicate algorithm names."""
        service = StatisticalAnalysisService(enabled_algorithms=["iqr", "iqr", "pareto"])

        # Should handle duplicates (though not ideal)
        assert "iqr" in service.enabled_algorithms
        assert "pareto" in service.enabled_algorithms

    def test_service_with_case_sensitive_algorithms(self):
        """Test service with case-sensitive algorithm names."""
        service = StatisticalAnalysisService(enabled_algorithms=["IQR", "PARETO"])

        # Algorithm names are case-sensitive, so these won't match
        test_data = {"outlier": 1000.0, "pareto_candidate": 50.0}
        highlights = service.analyze(test_data)

        # Should not find any highlights due to case mismatch
        assert highlights == {}
