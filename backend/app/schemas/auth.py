"""
Authentication Request and Response Pydantic Schemas.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.enums import UserRole


class LoginRequest(BaseModel):
    """User credentials for token issuance."""
    email: EmailStr = Field(description="Corporate email address")
    password: str = Field(min_length=4, description="Plaintext user password")


class TokenResponse(BaseModel):
    """JWT bearer token issuance payload."""
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user_id: str
    email: str
    role: str
    first_name: str
    last_name: str


class UserProfileResponse(BaseModel):
    """Authenticated user profile representation."""
    id: str
    business_id: str
    first_name: str
    last_name: str
    email: str
    department: str
    location: str
    role_id: Optional[str] = None
    system_role: str
    standard_hours_per_week: float

    model_config = ConfigDict(from_attributes=True)
