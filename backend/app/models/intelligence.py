"""
Intelligence and Optimization Models for WorkforceIQ:
- GapAnalysis: Identified capability deficit across project demand vs employee skills.
- Recommendation: AI-generated actionable staffing, training, or hiring recommendations.
- ScenarioRun: Simulation runs evaluating 'what-if' workforce supply/demand allocations.
- IssueRecord: Detected operational risks, capacity overloads, and skill shortages.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import (
    GapSeverity,
    GapStatus,
    IssueSeverity,
    IssueStatus,
    IssueType,
    RecommendationStatus,
    RecommendationType,
    ScenarioStatus,
)

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.project import Project, DemandPlan
    from app.models.skill import Skill


class GapAnalysis(Base, UUIDMixin, TimestampMixin):
    """
    Identified competency or capacity deficit between project demand and supply.
    Drives hiring plans, training roadmaps, and reallocation recommendations.
    """
    __tablename__ = "gap_analyses"
    __table_args__ = (
        CheckConstraint(
            "required_proficiency >= 1 AND required_proficiency <= 5",
            name="chk_gap_proficiency_range",
        ),
        CheckConstraint(
            "required_headcount > 0",
            name="chk_gap_req_headcount_positive",
        ),
        CheckConstraint(
            "available_headcount >= 0",
            name="chk_gap_avail_headcount_non_negative",
        ),
        CheckConstraint(
            "deficit_headcount >= 0",
            name="chk_gap_deficit_headcount_non_negative",
        ),
    )

    # Immutable Business Identifier convention: GAP-2026-000001
    business_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Business identifier convention e.g. GAP-2026-000001",
    )

    project_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Associated project if gap is project-specific",
    )

    demand_plan_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("demand_plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Associated demand line item if tied to specific demand plan",
    )

    skill_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skills.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Competency experiencing deficit",
    )

    required_proficiency: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Benchmark required proficiency level (1 to 5)",
    )

    required_headcount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Total individuals demanded with this skill profile",
    )

    available_headcount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Current qualified individuals available",
    )

    deficit_headcount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Net deficit headcount requiring fulfillment",
    )

    severity: Mapped[GapSeverity] = mapped_column(
        SAEnum(GapSeverity, native_enum=False),
        default=GapSeverity.MEDIUM,
        nullable=False,
        index=True,
        comment="Risk rating: LOW, MEDIUM, HIGH, CRITICAL",
    )

    status: Mapped[GapStatus] = mapped_column(
        SAEnum(GapStatus, native_enum=False),
        default=GapStatus.IDENTIFIED,
        nullable=False,
        index=True,
        comment="Status: IDENTIFIED, UNDER_REVIEW, MITIGATION_PLANNED, RESOLVED, ACCEPTED_RISK",
    )

    target_fulfillment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Deadline date by which gap must be resolved",
    )

    analysis_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date calculation engine recorded this gap snapshot",
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        back_populates="gap_analyses",
    )

    demand_plan: Mapped[Optional["DemandPlan"]] = relationship(
        "DemandPlan",
        back_populates="gap_analyses",
    )

    skill: Mapped["Skill"] = relationship(
        "Skill",
        back_populates="gap_analyses",
    )

    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="gap_analysis",
        cascade="all, delete-orphan",
    )


class Recommendation(Base, UUIDMixin, TimestampMixin):
    """
    AI-generated recommendation to resolve a skill deficit or capacity constraint.
    Can recommend reallocation, training enrollment, contingent labor, or hiring.
    """
    __tablename__ = "recommendations"
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0.000 AND confidence_score <= 1.000",
            name="chk_rec_confidence_range",
        ),
        CheckConstraint(
            "estimated_cost >= 0.00",
            name="chk_rec_est_cost_non_negative",
        ),
        CheckConstraint(
            "time_to_impact_days IS NULL OR time_to_impact_days >= 0",
            name="chk_rec_time_to_impact_non_negative",
        ),
    )

    # Immutable Business Identifier convention: REC-2026-000001
    business_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Business identifier convention e.g. REC-2026-000001",
    )

    gap_analysis_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("gap_analyses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Target gap this recommendation aims to mitigate",
    )

    target_employee_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Suggested employee for upskilling or reallocation",
    )

    target_project_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Target project requiring workforce support",
    )

    type: Mapped[RecommendationType] = mapped_column(
        SAEnum(RecommendationType, native_enum=False),
        nullable=False,
        index=True,
        comment="Type: INTERNAL_REALLOCATION, TRAINING_UPSKILL, EXTERNAL_HIRE, CONTRACTOR_CONTINGENT, PROJECT_TIMELINE_SHIFT",
    )

    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 3),
        nullable=False,
        comment="Machine learning model confidence score (0.000 to 1.000)",
    )

    impact_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Narrative justification and forecasted outcome of recommendation",
    )

    status: Mapped[RecommendationStatus] = mapped_column(
        SAEnum(RecommendationStatus, native_enum=False),
        default=RecommendationStatus.GENERATED,
        nullable=False,
        index=True,
        comment="Status: GENERATED, UNDER_REVIEW, ACCEPTED, REJECTED, IMPLEMENTED, EXPIRED",
    )

    estimated_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Projected financial investment in USD",
    )

    time_to_impact_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Expected days until capability is operational",
    )

    reviewed_by_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        comment="Decision-maker who approved or rejected this advice",
    )

    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Review timestamp",
    )

    # Relationships
    gap_analysis: Mapped[Optional["GapAnalysis"]] = relationship(
        "GapAnalysis",
        back_populates="recommendations",
    )

    target_employee: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        foreign_keys=[target_employee_id],
    )

    target_project: Mapped[Optional["Project"]] = relationship(
        "Project",
        foreign_keys=[target_project_id],
    )

    reviewer: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        foreign_keys=[reviewed_by_id],
    )


class ScenarioRun(Base, UUIDMixin, TimestampMixin):
    """
    Simulation scenario run for predictive workforce planning.
    Records input parameters, constraints, and optimization outcomes.
    """
    __tablename__ = "scenario_runs"

    # Immutable Business Identifier convention: SCN-2026-000001
    business_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Business identifier convention e.g. SCN-2026-000001",
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
        comment="Scenario title e.g. 'Q3 Cloud Expansion - Hiring Freeze'",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Executive hypothesis, assumptions, and constraints tested",
    )

    status: Mapped[ScenarioStatus] = mapped_column(
        SAEnum(ScenarioStatus, native_enum=False),
        default=ScenarioStatus.DRAFT,
        nullable=False,
        index=True,
        comment="Status: DRAFT, RUNNING, COMPLETED, FAILED, ARCHIVED",
    )

    parameters: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Structured input variables (budget caps, attrition rates, start shifts)",
    )

    simulation_results: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Structured optimization outputs (headcount gaps, cost projections)",
    )

    executed_by_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who launched the simulation run",
    )

    execution_duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Computation runtime in milliseconds",
    )

    # Relationships
    executed_by: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        foreign_keys=[executed_by_id],
    )


class IssueRecord(Base, UUIDMixin, TimestampMixin):
    """
    Workforce risk or operational conflict record.
    Tracks capacity overloads, allocation collisions, and unfulfilled demands.
    """
    __tablename__ = "issue_records"

    # Immutable Business Identifier convention: ISS-2026-000001
    business_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Business identifier convention e.g. ISS-2026-000001",
    )

    project_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Project affected by the issue",
    )

    employee_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Employee affected by the issue",
    )

    issue_type: Mapped[IssueType] = mapped_column(
        SAEnum(IssueType, native_enum=False),
        nullable=False,
        index=True,
        comment="Issue classification e.g. CAPACITY_OVERLOAD, ALLOCATION_CONFLICT",
    )

    severity: Mapped[IssueSeverity] = mapped_column(
        SAEnum(IssueSeverity, native_enum=False),
        default=IssueSeverity.MEDIUM,
        nullable=False,
        index=True,
        comment="Severity rating: LOW, MEDIUM, HIGH, CRITICAL",
    )

    status: Mapped[IssueStatus] = mapped_column(
        SAEnum(IssueStatus, native_enum=False),
        default=IssueStatus.OPEN,
        nullable=False,
        index=True,
        comment="Resolution status: OPEN, IN_PROGRESS, MITIGATED, RESOLVED, IGNORED",
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Concise issue summary",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Detailed breakdown of conflict conditions or root cause",
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Detection timestamp",
    )

    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Resolution timestamp",
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        back_populates="issues",
    )

    employee: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        foreign_keys=[employee_id],
    )

