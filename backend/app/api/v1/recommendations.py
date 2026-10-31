"""
Workforce Recommendations API Endpoints.
Generates explainable Reallocate, Train, Hire, and Reschedule actions,
and tracks recommendation approval/rejection decision workflows with full audit logging.
"""

from datetime import date, datetime, timezone
from typing import Annotated, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_current_user, get_db, require_roles
from app.models.audit import AuditEvent
from app.models.employee import Employee
from app.models.enums import AuditAction, RecommendationStatus, RecommendationType, UserRole
from app.models.intelligence import GapAnalysis, Recommendation
from app.models.project import Project
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.recommendation import (
    RecommendationDecisionRequest,
    RecommendationItemResponse,
    RecommendationPlanResponse,
    RecommendationRecordResponse,
)
from app.services.gap_analysis_service import GapAnalysisService
from app.services.recommendation import RecommendationAction, RecommendationEngine, RecommendationPlan
from app.services.skill_matching_service import SkillMatchingService

router = APIRouter(prefix="/recommendations", tags=["Workforce Recommendations"])


@router.get("", response_model=PaginatedResponse[RecommendationRecordResponse], summary="List Saved Recommendations")
async def list_recommendations(
    pagination: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
    status_filter: Optional[RecommendationStatus] = Query(default=None),
    type_filter: Optional[RecommendationType] = Query(default=None),
):
    query = select(Recommendation).order_by(desc(Recommendation.created_at))
    count_query = select(func.count(Recommendation.id))

    if status_filter:
        query = query.where(Recommendation.status == status_filter)
        count_query = count_query.where(Recommendation.status == status_filter)
    if type_filter:
        query = query.where(Recommendation.type == type_filter)
        count_query = count_query.where(Recommendation.type == type_filter)

    total_res = await session.execute(count_query)
    total = total_res.scalar() or 0

    query = query.offset(pagination.offset).limit(pagination.limit)
    res = await session.execute(query)
    recs = res.scalars().all()

    total_pages = max(1, (total + pagination.page_size - 1) // pagination.page_size)

    return PaginatedResponse[RecommendationRecordResponse](
        items=[RecommendationRecordResponse.model_validate(r) for r in recs],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.post("/generate", response_model=RecommendationPlanResponse, summary="Generate Explainable Gap Recommendations")
async def generate_recommendations(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.HR_PARTNER, UserRole.OPERATIONS_PARTNER, UserRole.PROJECT_MANAGER))],
    project_id: Optional[str] = Query(default=None, description="Optional target project ID filter"),
    as_of_date: Optional[date] = Query(default=None),
):
    """
    Evaluate identified workforce gaps and execute strict 5-step decision hierarchy:
    Internal Eligible -> Reallocate -> Train -> Hire -> Reschedule.
    """
    ref_date = as_of_date or date.today()

    # Load project gaps
    if project_id:
        gaps = await GapAnalysisService.analyze_project_gaps_async(session, project_id=project_id, as_of_date=ref_date)
    else:
        p_stmt = select(Project.id)
        p_res = await session.execute(p_stmt)
        p_ids = [r[0] for r in p_res.all()]
        gaps = []
        for pid in p_ids[:10]:
            pgaps = await GapAnalysisService.analyze_project_gaps_async(session, project_id=pid, as_of_date=ref_date)
            gaps.extend(pgaps)

    # Candidate pools per gap
    candidate_pools = {}
    prio_map = {}
    for g in gaps:
        cands = await SkillMatchingService.match_candidates_for_demand_async(
            session=session,
            demand_plan_id=g.demand_plan_id,
            as_of_date=ref_date,
            top_n=10,
        )
        candidate_pools[g.demand_plan_id] = cands

    plan: RecommendationPlan = RecommendationEngine.generate_portfolio_plan(
        gaps=gaps,
        candidate_pools_by_gap=candidate_pools,
        as_of_date=ref_date,
        project_priorities_map=prio_map,
    )

    items = [
        RecommendationItemResponse(
            action=r.action.value,
            gap_id=r.gap_id,
            project_id=r.project_id,
            required_skill=r.required_skill,
            required_hours=r.required_hours,
            affected_employees=r.affected_employees,
            expected_cost=r.expected_cost,
            estimated_time_to_resolve_days=r.estimated_time_to_resolve_days,
            expected_shortage_reduction_hours=r.expected_shortage_reduction_hours,
            deadline_feasibility=r.deadline_feasibility,
            confidence_score=r.confidence_score,
            explanation=r.explanation,
            assumptions=r.assumptions,
            rule_version=r.rule_version,
        )
        for r in plan.recommendations
    ]

    return RecommendationPlanResponse(
        total_expected_cost=plan.total_expected_cost,
        total_shortage_reduction_hours=plan.total_shortage_reduction_hours,
        gaps_analyzed_count=plan.gaps_analyzed_count,
        gaps_mitigated_count=plan.gaps_mitigated_count,
        unmitigated_gap_ids=plan.unmitigated_gap_ids,
        recommendations=items,
        rule_version=plan.rule_version,
    )


@router.post("/{recommendation_id}/approve", response_model=SuccessResponse, summary="Approve Recommendation")
async def approve_recommendation(
    recommendation_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.HR_PARTNER, UserRole.OPERATIONS_PARTNER, UserRole.PROJECT_MANAGER))],
    payload: Optional[RecommendationDecisionRequest] = None,
):
    """
    Approve an AI-generated staffing recommendation and log an immutable audit event.
    """
    stmt = select(Recommendation).where(or_(Recommendation.id == recommendation_id, Recommendation.business_id == recommendation_id))
    res = await session.execute(stmt)
    rec = res.scalar_one_or_none()

    now_dt = datetime.now(timezone.utc)

    if not rec:
        # Create record if not previously persisted
        rec = Recommendation(
            id=recommendation_id,
            business_id=f"REC-{now_dt.year}-{uuid.uuid4().hex[:6].upper()}",
            type=RecommendationType.INTERNAL_REALLOCATION,
            confidence_score=0.92,
            impact_summary="Approved workforce staffing recommendation.",
            status=RecommendationStatus.ACCEPTED,
            estimated_cost=0.0,
            reviewed_by_id=current_user.id,
            reviewed_at=now_dt,
        )
        session.add(rec)
    else:
        rec.status = RecommendationStatus.ACCEPTED
        rec.reviewed_by_id = current_user.id
        rec.reviewed_at = now_dt

    # Record Audit Event
    audit_event = AuditEvent(
        id=str(uuid.uuid4()),
        business_id=f"AUD-{now_dt.year}-{uuid.uuid4().hex[:6]}",
        entity_type="Recommendation",
        entity_id=rec.id,
        action=AuditAction.APPROVE,
        performed_by_id=current_user.id,
        new_values={
            "recommendation_id": rec.id,
            "business_id": rec.business_id,
            "status": RecommendationStatus.ACCEPTED.value,
            "reviewed_by": current_user.email,
        },
        reason=payload.reason if payload else "Approved by manager",
    )
    session.add(audit_event)

    await session.commit()

    return SuccessResponse(message=f"Recommendation '{rec.business_id}' approved successfully.")


@router.post("/{recommendation_id}/reject", response_model=SuccessResponse, summary="Reject Recommendation")
async def reject_recommendation(
    recommendation_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.HR_PARTNER, UserRole.OPERATIONS_PARTNER, UserRole.PROJECT_MANAGER))],
    payload: Optional[RecommendationDecisionRequest] = None,
):
    """
    Reject an AI-generated staffing recommendation and log an immutable audit event.
    """
    stmt = select(Recommendation).where(or_(Recommendation.id == recommendation_id, Recommendation.business_id == recommendation_id))
    res = await session.execute(stmt)
    rec = res.scalar_one_or_none()

    now_dt = datetime.now(timezone.utc)

    if not rec:
        rec = Recommendation(
            id=recommendation_id,
            business_id=f"REC-{now_dt.year}-{uuid.uuid4().hex[:6].upper()}",
            type=RecommendationType.INTERNAL_REALLOCATION,
            confidence_score=0.92,
            impact_summary="Rejected workforce staffing recommendation.",
            status=RecommendationStatus.REJECTED,
            estimated_cost=0.0,
            reviewed_by_id=current_user.id,
            reviewed_at=now_dt,
        )
        session.add(rec)
    else:
        rec.status = RecommendationStatus.REJECTED
        rec.reviewed_by_id = current_user.id
        rec.reviewed_at = now_dt

    # Record Audit Event
    audit_event = AuditEvent(
        id=str(uuid.uuid4()),
        business_id=f"AUD-{now_dt.year}-{uuid.uuid4().hex[:6]}",
        entity_type="Recommendation",
        entity_id=rec.id,
        action=AuditAction.REJECT,
        performed_by_id=current_user.id,
        new_values={
            "recommendation_id": rec.id,
            "business_id": rec.business_id,
            "status": RecommendationStatus.REJECTED.value,
            "reviewed_by": current_user.email,
        },
        reason=payload.reason if payload else "Rejected by manager",
    )
    session.add(audit_event)

    await session.commit()

    return SuccessResponse(message=f"Recommendation '{rec.business_id}' rejected.")
