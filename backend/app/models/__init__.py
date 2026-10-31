"""
WorkforceIQ Models Package.
Exports all 15 core entities, audit models, and lifecycle enumerations.
"""

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import (
    AllocationStatus,
    AuditAction,
    AvailabilityType,
    DemandStatus,
    EmploymentStatus,
    GapSeverity,
    GapStatus,
    IssueSeverity,
    IssueStatus,
    IssueType,
    ProjectStatus,
    RecommendationStatus,
    RecommendationType,
    ScenarioStatus,
    SkillCategory,
    TrainingStatus,
    UserRole,
    VerificationStatus,
)
from app.models.role import Role
from app.models.skill import Skill, EmployeeSkill, RoleSkill
from app.models.employee import Employee, Availability
from app.models.project import Project, DemandPlan
from app.models.allocation import Allocation
from app.models.training import Training
from app.models.intelligence import GapAnalysis, Recommendation, ScenarioRun, IssueRecord
from app.models.audit import AuditEvent

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    # Enums
    "EmploymentStatus",
    "SkillCategory",
    "VerificationStatus",
    "ProjectStatus",
    "DemandStatus",
    "AllocationStatus",
    "AvailabilityType",
    "TrainingStatus",
    "UserRole",
    "GapSeverity",
    "GapStatus",
    "RecommendationType",
    "RecommendationStatus",
    "ScenarioStatus",
    "IssueType",
    "IssueSeverity",
    "IssueStatus",
    "AuditAction",
    # Mandatory Entities
    "Employee",
    "Role",
    "Skill",
    "EmployeeSkill",
    "Project",
    "DemandPlan",
    "Allocation",
    "Availability",
    "Training",
    "GapAnalysis",
    # Additional Entities
    "RoleSkill",
    "Recommendation",
    "AuditEvent",
    "IssueRecord",
    "ScenarioRun",
]
