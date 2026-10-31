"""
Skill Domain Models for WorkforceIQ:
- Skill: Core organizational competency definition.
- EmployeeSkill: Employee competency bridge with historical verification audit.
- RoleSkill: Role requirements bridge with required proficiency levels.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import SkillCategory, VerificationStatus

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.role import Role
    from app.models.project import DemandPlan
    from app.models.training import Training
    from app.models.intelligence import GapAnalysis


class Skill(Base, UUIDMixin, TimestampMixin):
    """Core taxonomy skill/competency definition."""
    __tablename__ = "skills"

    # Immutable Business Identifier (e.g., SKL-000001)
    business_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Immutable business identifier e.g. SKL-000001",
    )

    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique official competency or technology name",
    )

    category: Mapped[SkillCategory] = mapped_column(
        SAEnum(SkillCategory, native_enum=False),
        nullable=False,
        index=True,
        comment="Classification category e.g. TECHNICAL, DOMAIN, LEADERSHIP",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed competency syllabus and scope",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Active flag for competency catalog",
    )

    # Relationships
    employee_skills: Mapped[List["EmployeeSkill"]] = relationship(
        "EmployeeSkill",
        back_populates="skill",
        cascade="all, delete-orphan",
    )

    role_skills: Mapped[List["RoleSkill"]] = relationship(
        "RoleSkill",
        back_populates="skill",
        cascade="all, delete-orphan",
    )

    demand_plans: Mapped[List["DemandPlan"]] = relationship(
        "DemandPlan",
        back_populates="primary_skill",
    )

    trainings: Mapped[List["Training"]] = relationship(
        "Training",
        back_populates="target_skill",
    )

    gap_analyses: Mapped[List["GapAnalysis"]] = relationship(
        "GapAnalysis",
        back_populates="skill",
    )


class EmployeeSkill(Base, UUIDMixin, TimestampMixin):
    """
    Bridge table linking Employee and Skill.
    Preserves competency proficiency progression and verification history.
    """
    __tablename__ = "employee_skills"
    __table_args__ = (
        CheckConstraint(
            "proficiency_level >= 1 AND proficiency_level <= 5",
            name="chk_emp_skill_proficiency_range",
        ),
        CheckConstraint(
            "effective_end_date IS NULL OR effective_end_date >= effective_start_date",
            name="chk_emp_skill_date_order",
        ),
        # Unique constraint per active version to prevent duplicate concurrent records
        UniqueConstraint(
            "employee_id",
            "skill_id",
            "effective_start_date",
            name="uq_emp_skill_version",
        ),
    )

    # Business Identifier (e.g., EMPSKL-000001)
    business_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique identifier for the skill profile entry",
    )

    employee_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to employee",
    )

    skill_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skills.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Foreign key to skill competency",
    )

    proficiency_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Assessed skill level: 1 (Beginner) to 5 (Expert)",
    )

    verification_status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(VerificationStatus, native_enum=False),
        default=VerificationStatus.SELF_REPORTED,
        nullable=False,
        index=True,
        comment="Audit state: SELF_REPORTED, MANAGER_VERIFIED, ASSESSMENT_CERTIFIED",
    )

    verified_by_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        comment="Auditor employee who verified this proficiency claim",
    )

    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when verification occurred",
    )

    effective_start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Effective date when this skill assessment became valid",
    )

    effective_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Expiry or supersession date for historical tracking",
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Flag indicating if this is the active assessment record",
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Evaluation commentary, certification references, or context",
    )

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee",
        foreign_keys=[employee_id],
        back_populates="employee_skills",
    )

    skill: Mapped["Skill"] = relationship(
        "Skill",
        back_populates="employee_skills",
    )

    verifier: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        foreign_keys=[verified_by_id],
    )


class RoleSkill(Base, UUIDMixin, TimestampMixin):
    """
    Bridge table defining skills required by a Role.
    Specifies benchmark minimum proficiencies and weights for gap scoring.
    """
    __tablename__ = "role_skills"
    __table_args__ = (
        CheckConstraint(
            "required_proficiency >= 1 AND required_proficiency <= 5",
            name="chk_role_skill_proficiency_range",
        ),
        CheckConstraint(
            "importance_weight >= 0.00 AND importance_weight <= 1.00",
            name="chk_role_skill_weight_range",
        ),
        UniqueConstraint(
            "role_id",
            "skill_id",
            name="uq_role_skill_pair",
        ),
    )

    # Business Identifier (e.g., ROLSKL-000001)
    business_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Business identifier e.g. ROLSKL-000001",
    )

    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to target role",
    )

    skill_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skills.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Foreign key to competency",
    )

    required_proficiency: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Target benchmark proficiency level: 1 (Beginner) to 5 (Expert)",
    )

    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="If true, lack of this skill flags critical gap",
    )

    importance_weight: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        default=Decimal("1.00"),
        nullable=False,
        comment="Relative weight in capability calculations (0.00 to 1.00)",
    )

    # Relationships
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="role_skills",
    )

    skill: Mapped["Skill"] = relationship(
        "Skill",
        back_populates="role_skills",
    )

