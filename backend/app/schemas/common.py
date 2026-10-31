"""
Common Reusable Pydantic Schemas for API Requests and Responses.
"""

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized wrapper for paginated collections."""
    items: List[T]
    total: int = Field(description="Total count of matching records across all pages")
    page: int = Field(description="Current page index (1-based)")
    page_size: int = Field(description="Maximum items per page")
    total_pages: int = Field(description="Total number of available pages")

    model_config = ConfigDict(from_attributes=True)


class SuccessResponse(BaseModel):
    """Standard generic success acknowledgment."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard structured error format."""
    detail: str
    error_code: Optional[str] = None
