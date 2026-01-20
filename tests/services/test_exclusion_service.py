"""Tests for the ExclusionService."""
import pytest
import json
import tempfile
import os
from whatsthedamage.services.exclusion_service import ExclusionService

def test_exclusion_service_initialization():
    """Test that ExclusionService initializes correctly."""
    service = ExclusionService()
    assert service is not None
    assert isinstance(service.default_exclusions, dict)
    assert isinstance(service.user_exclusions, dict)

def test_exclusion_service_with_custom_path():
    """Test ExclusionService with custom configuration path."""
    # Create a temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "default": ["Test1", "Test2"],
            "iqr": ["Test1"],
            "pareto": ["Test2"]
        }, f)
        temp_path = f.name

    try:
        service = ExclusionService(exclusions_path=temp_path)
        assert "Test1" in service.get_exclusions("default")
        assert "Test2" in service.get_exclusions("default")
        assert "Test1" in service.get_exclusions("iqr")
        assert "Test2" in service.get_exclusions("pareto")
    finally:
        os.unlink(temp_path)

def test_get_exclusions_no_algorithm():
    """Test getting all exclusions when no algorithm specified."""
    service = ExclusionService()
    # Create a temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "default": ["Category1", "Category2"],
            "iqr": ["Category3"],
            "pareto": ["Category4"]
        }, f)
        temp_path = f.name

    try:
        service = ExclusionService(exclusions_path=temp_path)
        all_exclusions = service.get_exclusions()
        assert "Category1" in all_exclusions
        assert "Category2" in all_exclusions
        assert "Category3" in all_exclusions
        assert "Category4" in all_exclusions
    finally:
        os.unlink(temp_path)

def test_get_exclusions_specific_algorithm():
    """Test getting exclusions for specific algorithm."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "default": ["Category1", "Category2"],
            "iqr": ["Category3"],
            "pareto": ["Category4"]
        }, f)
        temp_path = f.name

    try:
        service = ExclusionService(exclusions_path=temp_path)

        # Test IQR algorithm
        iqr_exclusions = service.get_exclusions("iqr")
        assert "Category3" in iqr_exclusions
        assert "Category1" not in iqr_exclusions  # Should not include default

        # Test Pareto algorithm
        pareto_exclusions = service.get_exclusions("pareto")
        assert "Category4" in pareto_exclusions
        assert "Category2" not in pareto_exclusions  # Should not include default
    finally:
        os.unlink(temp_path)

def test_set_user_exclusions():
    """Test setting user exclusions."""
    service = ExclusionService()

    # Set user exclusions for default algorithm
    service.set_user_exclusions("default", ["UserCat1", "UserCat2"])
    assert "UserCat1" in service.get_exclusions("default")
    assert "UserCat2" in service.get_exclusions("default")

    # Set user exclusions for IQR algorithm
    service.set_user_exclusions("iqr", ["UserIQR1"])
    assert "UserIQR1" in service.get_exclusions("iqr")

def test_set_user_exclusions_invalid():
    """Test setting user exclusions with invalid input."""
    service = ExclusionService()

    with pytest.raises(ValueError):
        service.set_user_exclusions("default", "not a list")  # type: ignore

def test_clear_user_exclusions():
    """Test clearing user exclusions."""
    service = ExclusionService()

    # Set some user exclusions
    service.set_user_exclusions("default", ["UserCat1"])
    service.set_user_exclusions("iqr", ["UserIQR1"])

    # Clear specific algorithm
    service.clear_user_exclusions("default")
    assert "UserCat1" not in service.get_exclusions("default")
    assert "UserIQR1" in service.get_exclusions("iqr")  # Should still be there

    # Clear all
    service.clear_user_exclusions()
    assert "UserIQR1" not in service.get_exclusions("iqr")

def test_is_excluded():
    """Test the is_excluded method."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "default": ["Deposit", "Transfer"],
            "iqr": ["Bonus"]
        }, f)
        temp_path = f.name

    try:
        service = ExclusionService(exclusions_path=temp_path)

        # Test default exclusions
        assert service.is_excluded("Deposit") is True
        assert service.is_excluded("Transfer") is True
        assert service.is_excluded("Grocery") is False

        # Test algorithm-specific exclusions
        assert service.is_excluded("Bonus", "iqr") is True
        assert service.is_excluded("Bonus", "pareto") is False  # Not in pareto exclusions

    finally:
        os.unlink(temp_path)

def test_get_exclusion_config():
    """Test getting exclusion configuration for frontend."""
    service = ExclusionService()

    # Set some user exclusions
    service.set_user_exclusions("default", ["UserDefault"])
    service.set_user_exclusions("iqr", ["UserIQR"])

    config = service.get_exclusion_config()
    assert "default" in config
    assert "user" in config
    assert "UserDefault" in config["user"]["default"]
    assert "UserIQR" in config["user"]["iqr"]

def test_empty_config_file():
    """Test with empty configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({}, f)
        temp_path = f.name

    try:
        service = ExclusionService(exclusions_path=temp_path)
        assert service.get_exclusions() == []
        assert service.get_exclusions("default") == []
        assert service.get_exclusions("iqr") == []
    finally:
        os.unlink(temp_path)

def test_invalid_config_file():
    """Test with invalid configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json content")
        temp_path = f.name

    try:
        service = ExclusionService(exclusions_path=temp_path)
        # Should handle gracefully and return empty exclusions
        assert service.get_exclusions() == []
    finally:
        os.unlink(temp_path)

def test_nonexistent_config_file():
    """Test with non-existent configuration file."""
    service = ExclusionService(exclusions_path="/nonexistent/path.json")
    # Should handle gracefully and return empty exclusions
    assert service.get_exclusions() == []
