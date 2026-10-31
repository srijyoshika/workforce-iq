"""
WorkforceIQ Lifecycle States and Domain Enumerations.
Defines strongly-typed domain values across employee, skill, project, and intelligence entities.
"""

from enum import Enum


class EmploymentStatus(str, Enum):
    """Lifecycle employment status for workforce members."""
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    TERMINATED = "TERMINATED"
    CONTRACTOR = "CONTRACTOR"
    PROBATION = "PROBATION"


class SkillCategory(str, Enum):
    """Taxonomy category for organizational capabilities."""
    TECHNICAL = "TECHNICAL"
    DOMAIN = "DOMAIN"
    LEADERSHIP = "LEADERSHIP"
    METHODOLOGY = "METHODOLOGY"
    TOOL = "TOOL"
    COMPLIANCE = "COMPLIANCE"


class VerificationStatus(str, Enum):
    """Audit verification lifecycle for employee skill competencies."""
    SELF_REPORTED = "SELF_REPORTED"
    PEER_REVIEWED = "PEER_REVIEWED"
    MANAGER_VERIFIED = "MANAGER_VERIFIED"
    ASSESSMENT_CERTIFIED = "ASSESSMENT_CERTIFIED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class ProjectStatus(str, Enum):
    """Lifecycle phase of business initiatives and engagements."""
    PIPELINE = "PIPELINE"
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class DemandStatus(str, Enum):
    """Fulfillment lifecycle of planned project workforce demand."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    FULFILLED = "FULFILLED"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    CANCELLED = "CANCELLED"


class AllocationStatus(str, Enum):
    """Lifecycle status of employee staffing allocations."""
    PROPOSED = "PROPOSED"
    CONFIRMED = "CONFIRMED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RELEASED = "RELEASED"


class AvailabilityType(str, Enum):
    """Categorization of workforce availability and leave periods."""
    AVAILABLE = "AVAILABLE"
    HOLIDAY = "HOLIDAY"
    PTO = "PTO"
    SICK_LEAVE = "SICK_LEAVE"
    TRAINING = "TRAINING"
    BENCH = "BENCH"
    RESERVED = "RESERVED"


class TrainingStatus(str, Enum):
    """Lifecycle status of skill upskilling and training tracks."""
    PLANNED = "PLANNED"
    ENROLLED = "ENROLLED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class GapSeverity(str, Enum):
    """Risk severity rating for unfulfilled project skill requirements."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GapStatus(str, Enum):
    """Operational status of an identified capability deficit."""
    IDENTIFIED = "IDENTIFIED"
    UNDER_REVIEW = "UNDER_REVIEW"
    MITIGATION_PLANNED = "MITIGATION_PLANNED"
    RESOLVED = "RESOLVED"
    ACCEPTED_RISK = "ACCEPTED_RISK"


class RecommendationType(str, Enum):
    """Actionable intelligence recommendation categories."""
    INTERNAL_REALLOCATION = "INTERNAL_REALLOCATION"
    TRAINING_UPSKILL = "TRAINING_UPSKILL"
    EXTERNAL_HIRE = "EXTERNAL_HIRE"
    CONTRACTOR_CONTINGENT = "CONTRACTOR_CONTINGENT"
    PROJECT_TIMELINE_SHIFT = "PROJECT_TIMELINE_SHIFT"


class RecommendationStatus(str, Enum):
    """Governance lifecycle of system-generated recommendations."""
    GENERATED = "GENERATED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    IMPLEMENTED = "IMPLEMENTED"
    EXPIRED = "EXPIRED"


class ScenarioStatus(str, Enum):
    """Execution status of simulation scenario runs."""
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class IssueType(str, Enum):
    """Classification of detected workforce or allocation issues."""
    CAPACITY_OVERLOAD = "CAPACITY_OVERLOAD"
    SKILL_SHORTAGE = "SKILL_SHORTAGE"
    ALLOCATION_CONFLICT = "ALLOCATION_CONFLICT"
    ATTRITION_RISK = "ATTRITION_RISK"
    UNFULFILLED_DEMAND = "UNFULFILLED_DEMAND"


class IssueSeverity(str, Enum):
    """Severity classification of recorded issues."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IssueStatus(str, Enum):
    """Resolution state of recorded workforce issues."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    MITIGATED = "MITIGATED"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"


class UserRole(str, Enum):
    """System authorization roles for WorkforceIQ access control."""
    ADMIN = "ADMIN"
    HR_PARTNER = "HR_PARTNER"
    PROJECT_MANAGER = "PROJECT_MANAGER"
    OPERATIONS_PARTNER = "OPERATIONS_PARTNER"
    EMPLOYEE = "EMPLOYEE"


class AuditAction(str, Enum):
    """Audited mutation types."""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VERIFY = "VERIFY"
    ALLOCATE = "ALLOCATE"
    SIMULATE = "SIMULATE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"

