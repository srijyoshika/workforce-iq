"""
Employee and Availability Domain Models for WorkforceIQ:
- Employee: Core individual personnel record with role assignment and standard capacity.
- Availability: Calendar availability, planned leaves, and capacity tracking.
"""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import AvailabilityType, EmploymentStatus, UserRole

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.skill import EmployeeSkill
    from app.models.allocation import Allocation
    from app.models.training import Training
    from app.models.audit import AuditEvent


class Employee(Base, UUIDMixin, TimestampMixin):
    """
    Enterprise employee entity.
    Maintains employment attributes, contractual hours, and role mappings.
    """
    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint(
            "exit_date IS NULL OR exit_date >= hire_date",
            name="chk_emp_hire_exit_dates",
        ),
        CheckConstraint(
            "standard_hours_per_week > 0.00 AND standard_hours_per_week <= 80.00",
            name="chk_emp_standard_hours_range",
        ),
        CheckConstraint(
            "cost_rate_per_hour IS NULL OR cost_rate_per_hour >= 0.00",
            name="chk_emp_cost_rate_non_negative",
        ),
    )

    # Immutable Business Identifier (e.g., EMP-000001)
    business_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Immutable enterprise business ID e.g. EMP-000001",
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Legal first name",
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Legal last name",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Corporate email address",
    )

    role_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Primary assigned job role foreign key",
    )

    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Department e.g. Engineering, Product, Consulting",
    )

    location: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Geographic work office or region e.g. New York, London, Remote",
    )

    employment_status: Mapped[EmploymentStatus] = mapped_column(
        SAEnum(EmploymentStatus, native_enum=False),
        default=EmploymentStatus.ACTIVE,
        nullable=False,
        index=True,
        comment="Employment lifecycle state",
    )

    hire_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Official employment start date",
    )

    exit_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Employment termination or contract completion date",
    )

    standard_hours_per_week: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("40.00"),
        nullable=False,
        comment="Contracted weekly capacity hours (typically 40.00)",
    )

    cost_rate_per_hour: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Fully-burdened internal hourly cost in USD",
    )

    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Bcrypt hashed authentication password",
    )

    system_role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, native_enum=False),
        default=UserRole.EMPLOYEE,
        nullable=False,
        index=True,
        comment="System access role: ADMIN, HR_PARTNER, PROJECT_MANAGER, OPERATIONS_PARTNER, EMPLOYEE",
    )

    years_of_experience: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(4, 1),
        default=Decimal("0.0"),
        nullable=True,
        comment="Total years of professional industry experience",
    )

    experience_level: Mapped[Optional[str]] = mapped_column(
        String(50),
        default="Mid-Level",
        nullable=True,
        comment="Seniority / experience level e.g. Junior, Mid-Level, Senior, Lead, Principal",
    )

    previous_company: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Previous company or organization name",
    )

    experience_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Professional background summary, domain expertise, and achievements",
    )

    # Relationships
    role: Mapped[Optional["Role"]] = relationship(
        "Role",
        back_populates="employees",
    )

    employee_skills: Mapped[List["EmployeeSkill"]] = relationship(
        "EmployeeSkill",
        foreign_keys="EmployeeSkill.employee_id",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    allocations: Mapped[List["Allocation"]] = relationship(
        "Allocation",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    availabilities: Mapped[List["Availability"]] = relationship(
        "Availability",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    trainings: Mapped[List["Training"]] = relationship(
        "Training",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    audit_events: Mapped[List["AuditEvent"]] = relationship(
        "AuditEvent",
        back_populates="performed_by",
    )


class Availability(Base, UUIDMixin, TimestampMixin):
    """
    Employee availability schedule, leave events, and capacity overrides.
    Used for project allocation feasibility and utilization calculations.
    """
    __tablename__ = "availabilities"
    __table_args__ = (
        CheckConstraint(
            "end_date >= start_date",
            name="chk_availability_date_order",
        ),
        CheckConstraint(
            "capacity_percentage >= 0.00 AND capacity_percentage <= 100.00",
            name="chk_availability_capacity_range",
        ),
        CheckConstraint(
            "available_hours_per_day >= 0.00 AND available_hours_per_day <= 24.00",
            name="chk_availability_hours_range",
        ),
    )

    # Business Identifier (e.g., AVL-2026-000001)
    business_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Immutable business identifier e.g. AVL-2026-000001",
    )

    employee_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Target employee",
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Start date of availability or leave block",
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="End date of availability or leave block",
    )

    availability_type: Mapped[AvailabilityType] = mapped_column(
        SAEnum(AvailabilityType, native_enum=False),
        default=AvailabilityType.AVAILABLE,
        nullable=False,
        index=True,
        comment="Status: AVAILABLE, PTO, SICK_LEAVE, TRAINING, BENCH, RESERVED",
    )

    available_hours_per_day: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        default=Decimal("8.00"),
        nullable=False,
        comment="Effective daily working hours during this span",
    )

    capacity_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("100.00"),
        nullable=False,
        comment="Percent of full capacity available (0.00% to 100.00%)",
    )

    reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Leave explanation or booking note",
    )

    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Governance approval status for leave",
    )

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="availabilities",
    )

