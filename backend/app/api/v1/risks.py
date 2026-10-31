"""
Workforce Risk Detection and Issue Tracking API Endpoints.
"""

from datetime import datetime, timezone
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_current_user, get_db, require_roles
from app.models.employee import Employee
from app.models.enums import IssueSeverity, IssueStatus, IssueType, UserRole
from app.models.intelligence import IssueRecord
from app.schemas.common import PaginatedResponse
from app.schemas.risk import IssueRecordResponse, IssueRecordUpdate, RiskScanResponse
from app.services.risk_service import RiskService

router = APIRouter(prefix="/risks", tags=["Workforce Risks"])


@router.get("/issues", response_model=PaginatedResponse[IssueRecordResponse], summary="List Detected Workforce Issues")
async def list_issues(
    pagination: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
    status_filter: Optional[IssueStatus] = Query(default=None, alias="status", description="Filter by resolution status"),
    severity: Optional[IssueSeverity] = Query(default=None, description="Filter by severity rating"),
    issue_type: Optional[IssueType] = Query(default=None, description="Filter by issue classification"),
):
    query = select(IssueRecord)
    count_query = select(func.count(IssueRecord.id))

    if status_filter:
        query = query.where(IssueRecord.status == status_filter)
        count_query = count_query.where(IssueRecord.status == status_filter)
    if severity:
        query = query.where(IssueRecord.severity == severity)
        count_query = count_query.where(IssueRecord.severity == severity)
    if issue_type:
        query = query.where(IssueRecord.issue_type == issue_type)
        count_query = count_query.where(IssueRecord.issue_type == issue_type)

    total_res = await session.execute(count_query)
    total = total_res.scalar() or 0

    query = query.order_by(desc(IssueRecord.detected_at)).offset(pagination.offset).limit(pagination.limit)
    res = await session.execute(query)
    issues = res.scalars().all()

    total_pages = max(1, (total + pagination.page_size - 1) // pagination.page_size)

    return PaginatedResponse[IssueRecordResponse](
        items=[IssueRecordResponse.model_validate(i) for i in issues],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.get("/issues/{issue_id}", response_model=IssueRecordResponse, summary="Get Issue by ID")
async def get_issue(
    issue_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    stmt = select(IssueRecord).where(IssueRecord.id == issue_id)
    res = await session.execute(stmt)
    issue = res.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Issue '{issue_id}' not found")
    return IssueRecordResponse.model_validate(issue)


@router.put("/issues/{issue_id}", response_model=IssueRecordResponse, summary="Update Issue Resolution Status")
async def update_issue(
    issue_id: str,
    payload: IssueRecordUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.OPERATIONS_PARTNER, UserRole.PROJECT_MANAGER))],
):
    stmt = select(IssueRecord).where(IssueRecord.id == issue_id)
    res = await session.execute(stmt)
    issue = res.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Issue '{issue_id}' not found")

    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(issue, f, v)

    if payload.status == IssueStatus.RESOLVED and not issue.resolved_at:
        issue.resolved_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(issue)
    return IssueRecordResponse.model_validate(issue)


@router.post("/scan", response_model=RiskScanResponse, summary="Trigger Global Workforce Risk Scan")
async def trigger_risk_scan(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.OPERATIONS_PARTNER))],
    project_id: Optional[str] = Query(default=None, description="Optional target project ID"),
):
    """
    Execute real database risk scan detecting overallocation, stale skills, duplicate demands,
    schedule overlaps, and staffing shortages. Automatically synchronizes new IssueRecord rows.
    """
    risks = await RiskService.detect_workforce_risks_async(session=session, project_id=project_id)
    persisted_count = await RiskService.sync_issue_records_async(session=session, risks=risks)

    overalloc = sum(1 for r in risks if r.issue_type == IssueType.CAPACITY_OVERLOAD.value)
    stale = sum(1 for r in risks if r.issue_type == IssueType.SKILL_SHORTAGE.value)
    dup = sum(1 for r in risks if r.action == "DE_DUPLICATE_DEMAND_LINE")
    overlap = sum(1 for r in risks if r.issue_type == IssueType.ALLOCATION_CONFLICT.value)
    shortage = sum(1 for r in risks if r.action == "ALLOCATE_RESOURCES_OR_HIRE")

    return RiskScanResponse(
        total_risks_detected=len(risks),
        overallocations_count=overalloc,
        stale_skills_count=stale,
        duplicate_demands_count=dup,
        overlapping_allocations_count=overlap,
        staffing_shortages_count=shortage,
        new_issues_persisted=persisted_count,
        scanned_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/anomalies", summary="Get Detected Anomalies and Exceptions Summary")
async def get_anomalies_summary(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    """Returns detected issues and anomalies summary."""
    stmt = select(IssueRecord).order_by(desc(IssueRecord.detected_at)).limit(100)
    res = await session.execute(stmt)
    issues = res.scalars().all()
    return {
        "total_anomalies": len(issues),
        "anomalies": [IssueRecordResponse.model_validate(i).model_dump() for i in issues],
    }
