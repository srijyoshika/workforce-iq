"""
Project and DemandPlan Domain Models for WorkforceIQ:
- Project: Client engagement, initiative, or internal program.
- DemandPlan: Role, skill, and time-phased capacity demand lines per project.
"""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
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
from app.models.enums import DemandStatus, ProjectStatus

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.role import Role
    from app.models.skill import Skill
    from app.models.allocation import Allocation
    from app.models.intelligence import GapAnalysis, IssueRecord


class Project(Base, UUIDMixin, TimestampMixin):
    """
    Project / initiative entity.
    Drives workforce demand, project budgets, and delivery timelines.
    """
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint(
            "end_date >= start_date",
            name="chk_project_date_order",
        ),
        CheckConstraint(
            "budget IS NULL OR budget >= 0.00",
            name="chk_project_budget_non_negative",
        ),
    )

    # Immutable Business Identifier (e.g., PRJ-2026-000001)
    business_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Immutable business identifier e.g. PRJ-2026-000001",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Official project or initiative name",
    )

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Project code or billing billing reference e.g. PRJ-CLOUD-MIG",
    )

    client_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        index=True,
        comment="Customer or internal sponsor organization",
    )

    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Owner business unit or department",
    )

    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus, native_enum=False),
        default=ProjectStatus.PIPELINE,
        nullable=False,
        index=True,
        comment="Lifecycle phase: PIPELINE, DRAFT, APPROVED, ACTIVE, COMPLETED, CANCELLED",
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Planned project kickoff date",
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Planned completion date",
    )

    budget: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 2),
        nullable=True,
        comment="Total allocated project financial budget in USD",
    )

    manager_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Project manager / delivery lead foreign key",
    )

    # Relationships
    manager: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        foreign_keys=[manager_id],
    )

    demand_plans: Mapped[List["DemandPlan"]] = relationship(
        "DemandPlan",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    allocations: Mapped[List["Allocation"]] = relationship(
        "Allocation",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    gap_analyses: Mapped[List["GapAnalysis"]] = relationship(
        "GapAnalysis",
        back_populates="project",
    )

    issues: Mapped[List["IssueRecord"]] = relationship(
        "IssueRecord",
        back_populates="project",
    )

    @property
    def priority(self) -> int:
        """Benchmark project priority tier (default 2)."""
        return 2

    @priority.setter
    def priority(self, val: int) -> None:
        pass

    @property
    def description(self) -> Optional[str]:
        """Project description summary."""
        return f"{self.name} engagement"

    @description.setter
    def description(self, val: Optional[str]) -> None:
        pass


class DemandPlan(Base, UUIDMixin, TimestampMixin):
    """
    Time-phased workforce demand line item for a project.
    Specifies requested role, required skills, and hour/headcount capacity.
    """
    __tablename__ = "demand_plans"
    __table_args__ = (
        CheckConstraint(
            "end_date >= start_date",
            name="chk_demand_date_order",
        ),
        CheckConstraint(
            "min_proficiency >= 1 AND min_proficiency <= 5",
            name="chk_demand_min_proficiency_range",
        ),
        CheckConstraint(
            "required_headcount > 0",
            name="chk_demand_headcount_positive",
        ),
        CheckConstraint(
            "required_hours > 0.00",
            name="chk_demand_required_hours_positive",
        ),
        CheckConstraint(
            "fulfilled_hours >= 0.00",
            name="chk_demand_fulfilled_hours_non_negative",
        ),
        CheckConstraint(
            "priority >= 1 AND priority <= 5",
            name="chk_demand_priority_range",
        ),
    )

    # Immutable Business Identifier convention: DEM-<project-id>-2026W01
    business_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="Business identifier convention e.g. DEM-PRJ-2026-000001-2026W01",
    )

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Target project foreign key",
    )

    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Demanded role foreign key",
    )

    primary_skill_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("skills.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Primary required skill competency foreign key",
    )

    min_proficiency: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        comment="Minimum acceptable skill proficiency: 1 to 5",
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Start date of the required staffing demand period",
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="End date of the required staffing demand period",
    )

    week_number: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        index=True,
        comment="ISO planning week e.g. 2026W01",
    )

    required_headcount: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Number of individuals required simultaneously",
    )

    required_hours: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
        comment="Total work hours required across the demand duration",
    )

    fulfilled_hours: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Hours fulfilled via confirmed allocations",
    )

    status: Mapped[DemandStatus] = mapped_column(
        SAEnum(DemandStatus, native_enum=False),
        default=DemandStatus.DRAFT,
        nullable=False,
        index=True,
        comment="Fulfillment state: DRAFT, SUBMITTED, APPROVED, FULFILLED, PARTIALLY_FULFILLED, CANCELLED",
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        comment="Staffing priority rating: 1 (Urgent/Executive) to 5 (Backlog)",
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="demand_plans",
    )

    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="demand_plans",
    )

    primary_skill: Mapped[Optional["Skill"]] = relationship(
        "Skill",
        back_populates="demand_plans",
    )

    allocations: Mapped[List["Allocation"]] = relationship(
        "Allocation",
        back_populates="demand_plan",
    )

    gap_analyses: Mapped[List["GapAnalysis"]] = relationship(
        "GapAnalysis",
        back_populates="demand_plan",
    )

