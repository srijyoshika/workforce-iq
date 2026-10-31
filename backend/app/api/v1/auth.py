"""
Authentication and Authorization API Endpoints.
Provides login, token issuance, logout, and current user profile inspection.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.config import get_settings
from app.core.security import create_access_token, hash_password, revoke_token, verify_password
from app.models.employee import Employee
from app.models.enums import UserRole
from app.schemas.auth import LoginRequest, TokenResponse, UserProfileResponse
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/login", response_model=TokenResponse, summary="User Authentication & Token Issuance")
async def login(
    payload: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Authenticate user credentials (email & password) and issue signed JWT bearer token.
    For seeded/synthetic employees without an explicit password, verifies against the default development password.
    """
    stmt = select(Employee).where(Employee.email == payload.email)
    res = await session.execute(stmt)
    employee = res.scalar_one_or_none()

    if not employee:
        # Check if email is a standard seed administrative account
        if payload.email == "admin@workforceiq.com" and payload.password == "Workforce2026!":
            # Create or return admin user token
            token = create_access_token(
                subject="EMP-ADMIN",
                role=UserRole.ADMIN.value,
                email=payload.email,
                employee_id="ADMIN-001",
            )
            return TokenResponse(
                access_token=token,
                token_type="bearer",
                expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user_id="ADMIN-001",
                email=payload.email,
                role=UserRole.ADMIN.value,
                first_name="System",
                last_name="Administrator",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials: user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Password validation:
    # If employee has hashed_password, verify it; otherwise fallback to default development credential
    is_valid_pwd = False
    if employee.hashed_password:
        is_valid_pwd = verify_password(payload.password, employee.hashed_password)
    else:
        # Default development password
        is_valid_pwd = (payload.password == "Workforce2026!")

    if not is_valid_pwd:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_val = (
        employee.system_role.value
        if hasattr(employee.system_role, "value")
        else str(employee.system_role)
    )

    token = create_access_token(
        subject=employee.id,
        role=role_val,
        email=employee.email,
        employee_id=employee.id,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=employee.id,
        email=employee.email,
        role=role_val,
        first_name=employee.first_name,
        last_name=employee.last_name,
    )


@router.post("/logout", response_model=SuccessResponse, summary="Invalidate Current Access Token")
async def logout(
    request: Request,
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    """
    Revoke the current caller's JWT access token, adding it to the revocation blacklist.
    """
    token = getattr(request.state, "access_token", None)
    if token:
        revoke_token(token)
    return SuccessResponse(message="Successfully logged out and revoked access token")


@router.get("/me", response_model=UserProfileResponse, summary="Get Current Authenticated User Profile")
async def get_my_profile(
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    """
    Return identity, role, and department metadata for the currently authenticated employee.
    """
    return UserProfileResponse(
        id=current_user.id,
        business_id=current_user.business_id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        department=current_user.department,
        location=current_user.location,
        role_id=current_user.role_id,
        system_role=current_user.system_role.value if hasattr(current_user.system_role, "value") else str(current_user.system_role),
        standard_hours_per_week=float(current_user.standard_hours_per_week),
    )
