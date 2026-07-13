"""API common models for request/response metadata.

These Pydantic models define common structures used across API endpoints.
"""
from whatsthedamage.models.common.error_models import ErrorResponse
from whatsthedamage.models.common.processing_metadata import ProcessingMetadata

__all__ = ['ErrorResponse', 'ProcessingMetadata']
