"""
Role Domain Model for WorkforceIQ.
"""

from typing import TYPE_CHECKING, List, Optional
from decimal import Decimal
from sqlalchemy import Boolean, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.skill import RoleSkill
    from app.models.project import DemandPlan


class Role(Base, UUIDMixin, TimestampMixin):
    """
    Standard job role / title definition within the organization.
    Maps to competency profiles and demand requirements.
    """
    __tablename__ = "roles"

    # Immutable Business Identifier (e.g., ROL-000001)
    business_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Immutable business identifier e.g. ROL-000001",
    )

    title: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
        comment="Official job role title",
    )

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Enterprise job code e.g. ENG-SWE-SR",
    )

    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Organizational department or business unit",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed role description and scope of responsibilities",
    )

    standard_hourly_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Standard benchmark internal hourly billing/cost rate in USD",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Active flag for role availability",
    )

    # Relationships
    employees: Mapped[List["Employee"]] = relationship(
        "Employee",
        back_populates="role",
    )

    role_skills: Mapped[List["RoleSkill"]] = relationship(
        "RoleSkill",
        back_populates="role",
        cascade="all, delete-orphan",
    )

    demand_plans: Mapped[List["DemandPlan"]] = relationship(
        "DemandPlan",
        back_populates="role",
    )

    @property
    def name(self) -> str:
        """Alias for title to maintain schema and API consistency."""
        return self.title

    @name.setter
    def name(self, value: str) -> None:
        self.title = value

    @property
    def level(self) -> int:
        """Default seniority tier level benchmark."""
        return 1

