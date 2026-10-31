"""WorkforceIQ Pydantic Schemas Package."""

from app.schemas.allocation import AllocationCreate, AllocationResponse, AllocationUpdate
from app.schemas.audit import AuditEventResponse
from app.schemas.analytics import (
    CapacityCalculationRequest,
    CapacityResponse,
    DepartmentUtilizationResponse,
    GapAnalysisResponse,
    UtilizationCalculationRequest,
    UtilizationResponse,
)
from app.schemas.auth import LoginRequest, TokenResponse, UserProfileResponse
from app.schemas.availability import AvailabilityCreate, AvailabilityResponse, AvailabilityUpdate
from app.schemas.common import ErrorResponse, PaginatedResponse, SuccessResponse
from app.schemas.demand import DemandPlanCreate, DemandPlanResponse, DemandPlanUpdate
from app.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from app.schemas.forecasting import (
    ForecastExecutionRequest,
    ForecastResponse,
    ProjectDemandAggregateResponse,
)
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.quality import EvaluationMetricsResponse, ReproducibilityResponse, ValidationReportResponse
from app.schemas.recommendation import RecommendationItemResponse, RecommendationPlanResponse
from app.schemas.risk import IssueRecordCreate, IssueRecordResponse, IssueRecordUpdate, RiskScanResponse
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate
from app.schemas.scenario import ScenarioRunCreate, ScenarioRunResponse
from app.schemas.skill import (
    EmployeeSkillCreate,
    EmployeeSkillResponse,
    EmployeeSkillUpdate,
    SkillCreate,
    SkillResponse,
    SkillUpdate,
)

__all__ = [
    "PaginatedResponse",
    "SuccessResponse",
    "ErrorResponse",
    "LoginRequest",
    "TokenResponse",
    "UserProfileResponse",
    "EmployeeCreate",
    "EmployeeUpdate",
    "EmployeeResponse",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "SkillCreate",
    "SkillUpdate",
    "SkillResponse",
    "EmployeeSkillCreate",
    "EmployeeSkillUpdate",
    "EmployeeSkillResponse",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "DemandPlanCreate",
    "DemandPlanUpdate",
    "DemandPlanResponse",
    "AllocationCreate",
    "AllocationUpdate",
    "AllocationResponse",
    "AvailabilityCreate",
    "AvailabilityUpdate",
    "AvailabilityResponse",
    "CapacityCalculationRequest",
    "CapacityResponse",
    "UtilizationCalculationRequest",
    "UtilizationResponse",
    "DepartmentUtilizationResponse",
    "GapAnalysisResponse",
    "ForecastExecutionRequest",
    "ForecastResponse",
    "ProjectDemandAggregateResponse",
    "RecommendationItemResponse",
    "RecommendationPlanResponse",
    "ScenarioRunCreate",
    "ScenarioRunResponse",
    "IssueRecordCreate",
    "IssueRecordUpdate",
    "IssueRecordResponse",
    "RiskScanResponse",
    "ValidationReportResponse",
    "EvaluationMetricsResponse",
    "ReproducibilityResponse",
]
