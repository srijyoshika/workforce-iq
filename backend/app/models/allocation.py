"""
Allocation Domain Model for WorkforceIQ.
Preserves full allocation version history, modifications, and audit tracking.
"""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import AllocationStatus

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.project import Project, DemandPlan


class Allocation(Base, UUIDMixin, TimestampMixin):
    """
    Project staffing allocation linking an Employee to a Project and optional DemandPlan.
    Supports versioning and supersession to ensure history is never silently overwritten.
    """
    __tablename__ = "allocations"
    __table_args__ = (
        CheckConstraint(
            "end_date >= start_date",
            name="chk_allocation_date_order",
        ),
        CheckConstraint(
            "allocation_percentage >= 0.00 AND allocation_percentage <= 100.00",
            name="chk_allocation_percentage_range",
        ),
        CheckConstraint(
            "allocated_hours_per_week >= 0.00",
            name="chk_allocation_hours_non_negative",
        ),
        CheckConstraint(
            "version >= 1",
            name="chk_allocation_version_positive",
        ),
    )

    # Immutable Business Identifier convention: ALLOC-2026-000001
    business_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Business identifier convention e.g. ALLOC-2026-000001",
    )

    employee_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Allocated employee foreign key",
    )

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Target project foreign key",
    )

    demand_plan_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("demand_plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Satisfied demand plan line item foreign key",
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Allocation effective start date",
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Allocation effective end date",
    )

    allocation_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="FTE allocation percentage e.g. 50.00% or 100.00%",
    )

    allocated_hours_per_week: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        comment="Dedicated weekly hours commitment e.g. 20.00",
    )

    hourly_billing_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Agreed project billing rate per hour in USD",
    )

    status: Mapped[AllocationStatus] = mapped_column(
        SAEnum(AllocationStatus, native_enum=False),
        default=AllocationStatus.PROPOSED,
        nullable=False,
        index=True,
        comment="Status: PROPOSED, CONFIRMED, ACTIVE, COMPLETED, CANCELLED, RELEASED",
    )

    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Sequential revision number for preserving historical allocations",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Flag indicating active record vs superseded historical revision",
    )

    superseded_by_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("allocations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Self-reference to newer allocation revision that replaced this entry",
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Staffing notes, scope changes, or reallocation rationale",
    )

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="allocations",
    )

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="allocations",
    )

    demand_plan: Mapped[Optional["DemandPlan"]] = relationship(
        "DemandPlan",
        back_populates="allocations",
    )

    superseded_by: Mapped[Optional["Allocation"]] = relationship(
        "Allocation",
        remote_side="Allocation.id",
    )

