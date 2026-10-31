"""
Scenario Simulation and What-If Optimization API Endpoints.
Connects directly to ScenarioEngineService with guaranteed baseline protection.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams, get_current_user, get_db, require_roles
from app.models.employee import Employee
from app.models.enums import UserRole
from app.models.intelligence import ScenarioRun
from app.schemas.common import PaginatedResponse
from app.schemas.scenario import ScenarioRunCreate, ScenarioRunResponse
from app.services.scenario_service import ScenarioEngineService

router = APIRouter(prefix="/scenarios", tags=["Scenario Simulation"])


@router.get("", response_model=PaginatedResponse[ScenarioRunResponse], summary="List Scenario Simulation Runs")
async def list_scenarios(
    pagination: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    query = select(ScenarioRun).order_by(desc(ScenarioRun.created_at))
    query = query.offset(pagination.offset).limit(pagination.limit)
    res = await session.execute(query)
    scenarios = res.scalars().all()

    count_stmt = select(ScenarioRun.id)
    count_res = await session.execute(count_stmt)
    total = len(count_res.scalars().all())
    total_pages = max(1, (total + pagination.page_size - 1) // pagination.page_size)

    return PaginatedResponse[ScenarioRunResponse](
        items=[ScenarioRunResponse.model_validate(s) for s in scenarios],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.get("/{scenario_id}", response_model=ScenarioRunResponse, summary="Get Scenario Run by ID")
async def get_scenario(
    scenario_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(get_current_user)],
):
    stmt = select(ScenarioRun).where(ScenarioRun.id == scenario_id)
    res = await session.execute(stmt)
    scn = res.scalar_one_or_none()
    if not scn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Scenario '{scenario_id}' not found")
    return ScenarioRunResponse.model_validate(scn)


@router.post("", response_model=ScenarioRunResponse, status_code=status.HTTP_201_CREATED, summary="Execute Scenario Optimization Run")
async def create_and_run_scenario(
    payload: ScenarioRunCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Employee, Depends(require_roles(UserRole.ADMIN, UserRole.OPERATIONS_PARTNER, UserRole.PROJECT_MANAGER))],
):
    """
    Launch workforce what-if simulation run using OR-Tools CP-SAT optimizer,
    preserving baseline DB records and recording audit events.
    """
    new_scn = await ScenarioEngineService.run_scenario_simulation(
        session=session,
        name=payload.name,
        description=payload.description,
        parameters=payload.parameters,
        executed_by_id=current_user.id,
    )

    return ScenarioRunResponse.model_validate(new_scn)
