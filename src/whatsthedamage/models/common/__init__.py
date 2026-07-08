"""Common models shared across domain and API layers.

This module provides shared base models that both domain and API layers can import,
eliminating duplication of fundamental data structures.
"""

from whatsthedamage.models.common.display_fields import DisplayRawField, DateField
from whatsthedamage.models.common.error_models import ErrorResponse
from whatsthedamage.models.common.processing_metadata import ProcessingMetadata

__all__ = [
    'DisplayRawField',
    'DateField',
    'ErrorResponse',
    'ProcessingMetadata',
]
