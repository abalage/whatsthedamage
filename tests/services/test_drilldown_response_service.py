"""Test DrilldownResponseService highlights handling.

This module tests the highlight aggregation logic in DrilldownResponseService,
specifically the _get_highlights_lookup method which was fixed to merge
highlight types for the same row_id instead of overwriting them.
"""
import pytest
from unittest.mock import MagicMock
from whatsthedamage.models.dt_models import CellHighlight, ProcessingResponse, StatisticalMetadata
from whatsthedamage.services.drilldown_response_service import DrilldownResponseService


@pytest.fixture
def drilldown_service():
    """Create DrilldownResponseService with mock dependencies."""
    return DrilldownResponseService(
        id_mapping_service=MagicMock(),
        cache_service=MagicMock()
    )


def create_processing_response_with_highlights(highlight_list):
    """Create a ProcessingResponse with specified CellHighlight entries."""
    statistical_metadata = StatisticalMetadata(highlights=highlight_list)
    return ProcessingResponse(
        result_id='test-result',
        data={},
        metadata={},
        statistical_metadata=statistical_metadata
    )


class TestGetHighlightsLookup:
    """Test _get_highlights_lookup method."""

    def test_merges_highlight_types_for_same_row_id(self, drilldown_service):
        """Test that multiple CellHighlight entries for same row_id are merged."""
        # Create highlights with same row_id but different types
        highlight_list = [
            CellHighlight(row_id='row1', highlight_types=['iqr']),
            CellHighlight(row_id='row1', highlight_types=['pareto']),
            CellHighlight(row_id='row2', highlight_types=['iqr']),
        ]
        
        processing_response = create_processing_response_with_highlights(highlight_list)
        
        result = drilldown_service._get_highlights_lookup(processing_response)
        
        # row1 should have both 'iqr' and 'pareto'
        assert 'row1' in result
        assert set(result['row1']) == {'iqr', 'pareto'}
        
        # row2 should have 'iqr'
        assert 'row2' in result
        assert result['row2'] == ['iqr']

    def test_handles_empty_highlights(self, drilldown_service):
        """Test that empty highlights list returns empty dict."""
        processing_response = create_processing_response_with_highlights([])
        
        result = drilldown_service._get_highlights_lookup(processing_response)
        
        assert result == {}

    def test_handles_no_statistical_metadata(self, drilldown_service):
        """Test that missing statistical_metadata returns empty dict."""
        # Create ProcessingResponse without statistical_metadata
        processing_response = ProcessingResponse(
            result_id='test-result',
            data={},
            metadata={},
            statistical_metadata=None  # type: ignore
        )
        
        result = drilldown_service._get_highlights_lookup(processing_response)
        
        assert result == {}

    def test_handles_no_highlights_in_metadata(self, drilldown_service):
        """Test that statistical_metadata without highlights returns empty dict."""
        processing_response = ProcessingResponse(
            result_id='test-result',
            data={},
            metadata={},
            statistical_metadata=StatisticalMetadata(highlights=[])  # type: ignore
        )
        
        result = drilldown_service._get_highlights_lookup(processing_response)
        
        assert result == {}

    def test_merges_multiple_highlights_for_same_row(self, drilldown_service):
        """Test merging more than 2 highlight entries for same row."""
        highlight_list = [
            CellHighlight(row_id='row1', highlight_types=['iqr']),
            CellHighlight(row_id='row1', highlight_types=['pareto']),
            CellHighlight(row_id='row1', highlight_types=['outlier']),
        ]
        
        processing_response = create_processing_response_with_highlights(highlight_list)
        
        result = drilldown_service._get_highlights_lookup(processing_response)
        
        assert 'row1' in result
        assert set(result['row1']) == {'iqr', 'pareto', 'outlier'}
        assert len(result['row1']) == 3

    def test_preserves_order_of_first_occurrence(self, drilldown_service):
        """Test that highlight types are added in order of first occurrence."""
        highlight_list = [
            CellHighlight(row_id='row1', highlight_types=['pareto']),
            CellHighlight(row_id='row1', highlight_types=['iqr']),
            CellHighlight(row_id='row1', highlight_types=['outlier']),
        ]
        
        processing_response = create_processing_response_with_highlights(highlight_list)
        
        result = drilldown_service._get_highlights_lookup(processing_response)
        
        # Order should be: pareto (first), iqr (second), outlier (third)
        assert result['row1'] == ['pareto', 'iqr', 'outlier']

    def test_handles_duplicate_highlight_types(self, drilldown_service):
        """Test that duplicate highlight types are preserved (extend behavior)."""
        highlight_list = [
            CellHighlight(row_id='row1', highlight_types=['iqr', 'pareto']),
            CellHighlight(row_id='row1', highlight_types=['pareto', 'iqr']),
        ]
        
        processing_response = create_processing_response_with_highlights(highlight_list)
        
        result = drilldown_service._get_highlights_lookup(processing_response)
        
        # Both lists are extended, so we get ['iqr', 'pareto', 'pareto', 'iqr']
        assert 'row1' in result
        assert result['row1'] == ['iqr', 'pareto', 'pareto', 'iqr']

    def test_returns_copy_of_highlight_types(self, drilldown_service):
        """Test that we return a copy, not the original list."""
        original_list = ['iqr', 'pareto']
        highlight_list = [
            CellHighlight(row_id='row1', highlight_types=original_list),
        ]
        
        processing_response = create_processing_response_with_highlights(highlight_list)
        
        result = drilldown_service._get_highlights_lookup(processing_response)
        
        # Modify the returned list
        result['row1'].append('modified')
        
        # Original should not be modified
        assert original_list == ['iqr', 'pareto']
