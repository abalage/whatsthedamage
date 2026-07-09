"""Unified Account model for the whatsthedamage application.

This module provides a single Account model that replaces the previous
AccountResponse (domain) and AccountDataResponse (API) models, eliminating
duplication and simplifying the codebase.

The Account model is used throughout the application:
- Processing services (domain layer)
- API endpoints (API layer)
- Frontend TypeScript types (via mirroring)

Previous models that are now consolidated:
- AccountResponse from dt_models.py
- AccountDataResponse from api/responses.py
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from whatsthedamage.models.domain.dt_models import AggregatedRow


class Account(BaseModel):
    """Unified account model used throughout the application.
    
    This model consolidates AccountResponse (domain) and AccountDataResponse (API)
    into a single representation that serves both purposes.
    
    Attributes:
        id: Account identifier (raw account number). Replaces 'account' field from
            AccountResponse and 'id' field from AccountDataResponse.
        name: Account display name. Previously only in AccountDataResponse.
        formatted_id: Formatted account ID for display (e.g., '1234-5678').
            Previously only in AccountDataResponse.
        currency: Account currency code (e.g., 'USD', 'HUF', 'EUR').
        data: Aggregated transaction data for this account as a list of AggregatedRow.
            Replaces dt_response['data'] from AccountDataResponse.
        result_id: Processing result identifier for context.
        metadata: Optional processing metadata.
    
    Example usage::
    
        from whatsthedamage.models.domain.account import Account
        from whatsthedamage.models.domain.dt_models import AggregatedRow
        
        account = Account(
            id='1234567890123456',
            name='Primary Account',
            formatted_id='1234-5678-9012-3456',
            currency='USD',
            data=[...],  # List[AggregatedRow]
            result_id='abc123',
            metadata={'processed_at': '2025-01-01'}
        )
    """
    id: str = Field(description="Account identifier (raw account number)")
    name: str = Field(default="", description="Account display name")
    formatted_id: str = Field(default="", description="Formatted account ID for display")
    currency: str = Field(description="Account currency code")
    data: List["AggregatedRow"] = Field(
        default_factory=list,
        description="Aggregated transaction data for this account"
    )
    result_id: str = Field(default="", description="Processing result identifier")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional processing metadata"
    )
