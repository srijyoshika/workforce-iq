"""
Training Domain Model for WorkforceIQ.
Tracks upskilling initiatives designed to close identified skill gaps.
"""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
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
from app.models.enums import TrainingStatus

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.skill import Skill


class Training(Base, UUIDMixin, TimestampMixin):
    """
    Skill development / training enrollment for an employee.
    Tied to upskilling pathways and capability growth.
    """
    __tablename__ = "trainings"
    __table_args__ = (
        CheckConstraint(
            "completion_date IS NULL OR completion_date >= start_date",
            name="chk_training_date_order",
        ),
        CheckConstraint(
            "target_proficiency >= 1 AND target_proficiency <= 5",
            name="chk_training_target_proficiency_range",
        ),
        CheckConstraint(
            "estimated_cost >= 0.00",
            name="chk_training_est_cost_non_negative",
        ),
        CheckConstraint(
            "actual_cost IS NULL OR actual_cost >= 0.00",
            name="chk_training_act_cost_non_negative",
        ),
    )

    # Immutable Business Identifier convention: TRN-2026-000001
    business_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Business identifier convention e.g. TRN-2026-000001",
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Training course or certification title",
    )

    target_skill_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skills.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Target skill competency foreign key",
    )

    employee_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Enrolled employee foreign key",
    )

    provider: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="Training vendor or academy e.g. Coursera, AWS, Internal Academy",
    )

    status: Mapped[TrainingStatus] = mapped_column(
        SAEnum(TrainingStatus, native_enum=False),
        default=TrainingStatus.PLANNED,
        nullable=False,
        index=True,
        comment="Status: PLANNED, ENROLLED, IN_PROGRESS, COMPLETED, FAILED, CANCELLED",
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Scheduled training commencement date",
    )

    completion_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Actual completion or graduation date",
    )

    target_proficiency: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Target competency proficiency level upon completion (1 to 5)",
    )

    estimated_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Budgeted course and exam fee in USD",
    )

    actual_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Final incurred training expenditure in USD",
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Curriculum syllabus or assessment outcome notes",
    )

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="trainings",
    )

    target_skill: Mapped["Skill"] = relationship(
        "Skill",
        back_populates="trainings",
    )

