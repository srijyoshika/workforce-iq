"""
Workforce Analytics and Calculation Engine API Endpoints.
Connects directly to real database services:
- CapacityService
- UtilizationService
- GapAnalysisService
"""

from datetime import date, timedelta
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.models.employee import Employee
from app.models.enums import UserRole
from app.schemas.analytics import (
    CapacityCalculationRequest,
    CapacityResponse,
    DepartmentUtilizationResponse,
    GapAnalysisResponse,
    UtilizationCalculationRequest,
    UtilizationResponse,
)
from app.schemas.common import SuccessResponse
from app.services.capacity_service import CapacityService
from app.services.gap_analysis_service import GapAnalysisService
from app.services.utilization_service import UtilizationService

router = APIRouter(prefix="/analytics", tags=["Workforce Analytics"])


@router.post("/capacity", response_model=CapacityResponse, summary="Calculate Employee Net Working Capacity")
async def calculate_capacity(
    payload: CapacityCalculationRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    """
    Execute canonical capacity calculation on real database records for specified employee.
    Considers contract hours, part-time split, lifecycle status, and approved leaves.
    """
    res = await CapacityService.get_employee_capacity_async(
        session=session,
        employee_id=payload.employee_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{payload.employee_id}' not found",
        )
    return CapacityResponse(
        employee_id=res.employee_id,
        business_id=res.business_id,
        start_date=res.start_date.isoformat(),
        end_date=res.end_date.isoformat(),
        contract_hours_per_week=res.contract_hours_per_week,
        base_period_hours=res.base_period_hours,
        leave_hours_deducted=res.leave_hours_deducted,
        lifecycle_status=res.lifecycle_status,
        is_active_in_period=res.is_active_in_period,
        net_available_hours=res.net_available_hours,
        calculated_at=res.calculated_at,
        rule_version=res.rule_version,
    )


@router.post("/utilization", response_model=UtilizationResponse, summary="Calculate Employee Workload Utilization")
async def calculate_utilization(
    payload: UtilizationCalculationRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    """
    Execute canonical workload utilization calculation against real database records.
    Calculates allocated hours, remaining capacity, utilization %, and governance classification.
    """
    res = await UtilizationService.get_employee_utilization_async(
        session=session,
        employee_id=payload.employee_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{payload.employee_id}' not found",
        )
    return UtilizationResponse(
        employee_id=res.employee_id,
        business_id=res.business_id,
        start_date=res.start_date.isoformat(),
        end_date=res.end_date.isoformat(),
        available_hours=res.available_hours,
        allocated_hours=res.allocated_hours,
        remaining_hours=res.remaining_hours,
        utilization_percentage=res.utilization_percentage,
        category=res.category,
        is_overallocated=res.is_overallocated,
        allocation_count=res.allocation_count,
        calculated_at=res.calculated_at,
        rule_version=res.rule_version,
    )


@router.get("/department-utilization", response_model=List[DepartmentUtilizationResponse], summary="Department Utilization Summary")
async def get_department_utilization(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
):
    """
    Aggregate capacity and workload across all enterprise departments using SQL batch queries.
    """
    ref_start = start_date or date.today()
    ref_end = end_date or (ref_start + timedelta(days=30))

    from sqlalchemy import select
    dept_stmt = select(Employee.department).distinct().where(Employee.department != None)
    dept_res = await session.execute(dept_stmt)
    departments = [d[0] for d in dept_res.all() if d[0]]
    if not departments:
        departments = ["Engineering", "Data & AI", "Product", "Operations"]

    summaries = []
    for dept in departments:
        summary = await UtilizationService.get_department_utilization_summary_async(
            session=session,
            department=dept,
            start_date=ref_start,
            end_date=ref_end,
        )
        summaries.append(summary)
    return [
        DepartmentUtilizationResponse(
            department=s.department,
            headcount=s.headcount,
            total_available_hours=s.total_available_hours,
            total_allocated_hours=s.total_allocated_hours,
            average_utilization_percentage=s.average_utilization_percentage,
            underutilized_count=s.underutilized_count,
            normal_count=s.normal_count,
            high_count=s.high_count,
            overallocated_count=s.overallocated_count,
            calculated_at=s.calculated_at,
        )
        for s in summaries
    ]


@router.get("/gaps", response_model=List[GapAnalysisResponse], summary="Analyze Project Capability Deficits")
async def analyze_project_gaps(
    project_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
    as_of_date: Optional[date] = Query(default=None),
):
    """
    Perform quantitative gap analysis on specified project demand versus available qualified supply.
    """
    gaps = await GapAnalysisService.analyze_project_gaps_async(
        session=session,
        project_id=project_id,
        as_of_date=as_of_date,
    )
    return [
        GapAnalysisResponse(
            demand_plan_id=g.demand_plan_id,
            project_id=g.project_id,
            project_name=g.project_name,
            skill_id=g.skill_id,
            skill_name=g.skill_name,
            role_id=g.role_id,
            start_date=str(g.start_date),
            end_date=str(g.end_date),
            required_proficiency=g.required_proficiency,
            required_headcount=g.required_headcount,
            available_qualified_headcount=g.available_qualified_headcount,
            headcount_deficit=g.headcount_deficit,
            required_demand_hours=g.required_demand_hours,
            qualified_supply_hours=g.qualified_supply_hours,
            unfilled_demand_hours=g.unfilled_demand_hours,
            capacity_gap_hours=g.capacity_gap_hours,
            fulfillment_percentage=g.fulfillment_percentage,
            severity=g.severity,
            status=g.status,
            calculated_at=g.calculated_at,
            rule_version=g.rule_version,
        )
        for g in gaps
    ]


@router.post("/sync-gaps", response_model=SuccessResponse, summary="Synchronize Database Gap Analysis Records")
async def sync_gaps(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.OPERATIONS_PARTNER))],
    project_ids: Optional[List[str]] = None,
    as_of_date: Optional[date] = None,
):
    """
    Synchronize and persist GapAnalysis records across active project demands.
    """
    count = await GapAnalysisService.sync_gap_analyses_async(
        session=session,
        project_ids=project_ids,
        as_of_date=as_of_date,
    )
    return SuccessResponse(message=f"Successfully synchronized {count} project gap record(s)")
