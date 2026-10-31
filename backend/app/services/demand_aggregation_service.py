"""
Demand Aggregation Service for WorkforceIQ.

Performs SQL and in-memory aggregation of time-phased workforce demand line items across:
1. Project portfolio
2. Job Role architecture
3. Skill Competency taxonomy
4. Enterprise Department
5. Planning Periods (Week, Month, Quarter)
6. Priority tiers (1 Urgent to 5 Backlog)

Calculates total required hours, fulfilled hours, unfilled hours, headcount, and fulfillment rates.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Union
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import DemandStatus
from app.models.project import DemandPlan, Project
from app.models.role import Role
from app.models.skill import Skill
from app.services.thresholds import DEFAULT_THRESHOLDS, PlanningThresholds


@dataclass(frozen=True)
class DemandAggregateItem:
    """Consolidated demand metrics for a specific dimension grouping."""
    dimension_type: str
    dimension_id: str
    dimension_name: str
    demand_lines_count: int
    total_required_headcount: int
    total_required_hours: float
    total_fulfilled_hours: float
    total_unfilled_hours: float
    fulfillment_percentage: float
    is_fully_fulfilled: bool
    calculated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension_type": self.dimension_type,
            "dimension_id": self.dimension_id,
            "dimension_name": self.dimension_name,
            "demand_lines_count": self.demand_lines_count,
            "total_required_headcount": self.total_required_headcount,
            "total_required_hours": self.total_required_hours,
            "total_fulfilled_hours": self.total_fulfilled_hours,
            "total_unfilled_hours": self.total_unfilled_hours,
            "fulfillment_percentage": self.fulfillment_percentage,
            "is_fully_fulfilled": self.is_fully_fulfilled,
            "calculated_at": self.calculated_at,
        }


class DemandAggregationService:
    """Canonical engine for all workforce demand aggregation and portfolio rollups."""

    @classmethod
    def aggregate_records(
        cls,
        demand_plans: Sequence[Union[DemandPlan, Dict[str, Any]]],
        dimension: str,
        dimension_names_map: Optional[Dict[str, str]] = None,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> List[DemandAggregateItem]:
        """
        Aggregate demand plans by target dimension in-memory.
        Dimension options: 'project_id', 'role_id', 'primary_skill_id', 'priority', 'week_number'.
        """
        names_map = dimension_names_map or {}
        groups: Dict[str, Dict[str, Any]] = {}

        for d in demand_plans:
            # Dimension grouping key
            dim_val = getattr(d, dimension, None) if not isinstance(d, dict) else d.get(dimension)
            dim_key = str(dim_val or "UNSPECIFIED")

            if dim_key not in groups:
                groups[dim_key] = {
                    "count": 0,
                    "headcount": 0,
                    "required_hours": 0.0,
                    "fulfilled_hours": 0.0,
                }

            req_headcount = int(getattr(d, "required_headcount", None) or d.get("required_headcount", 1))
            req_hours = float(getattr(d, "required_hours", None) or d.get("required_hours", 0.0))
            ful_hours = float(getattr(d, "fulfilled_hours", None) or d.get("fulfilled_hours", 0.0))

            groups[dim_key]["count"] += 1
            groups[dim_key]["headcount"] += req_headcount
            groups[dim_key]["required_hours"] += req_hours
            groups[dim_key]["fulfilled_hours"] += ful_hours

        now_str = datetime.now(timezone.utc).isoformat()
        results: List[DemandAggregateItem] = []

        for dim_key, data in sorted(groups.items()):
            req_h = round(data["required_hours"], 2)
            ful_h = round(data["fulfilled_hours"], 2)
            unfil_h = round(max(0.0, req_h - ful_h), 2)
            pct = round((ful_h / req_h * 100.0), 2) if req_h > 0.0 else 100.0

            dim_name = names_map.get(dim_key, dim_key)

            results.append(
                DemandAggregateItem(
                    dimension_type=dimension,
                    dimension_id=dim_key,
                    dimension_name=dim_name,
                    demand_lines_count=data["count"],
                    total_required_headcount=data["headcount"],
                    total_required_hours=req_h,
                    total_fulfilled_hours=ful_h,
                    total_unfilled_hours=unfil_h,
                    fulfillment_percentage=min(100.0, pct),
                    is_fully_fulfilled=(unfil_h == 0.0),
                    calculated_at=now_str,
                )
            )

        return results

    @classmethod
    async def aggregate_by_project_async(
        cls,
        session: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> List[DemandAggregateItem]:
        """SQL-level aggregation of demand plans grouped by Project."""
        stmt = (
            select(
                Project.id.label("project_id"),
                Project.name.label("project_name"),
                func.count(DemandPlan.id).label("line_count"),
                func.sum(DemandPlan.required_headcount).label("total_headcount"),
                func.sum(DemandPlan.required_hours).label("total_req_hours"),
                func.sum(DemandPlan.fulfilled_hours).label("total_ful_hours"),
            )
            .join(Project, Project.id == DemandPlan.project_id)
            .group_by(Project.id, Project.name)
        )

        if start_date and end_date:
            stmt = stmt.where(
                and_(DemandPlan.start_date <= end_date, DemandPlan.end_date >= start_date)
            )

        res = await session.execute(stmt)
        rows = res.all()
        now_str = datetime.now(timezone.utc).isoformat()
        results = []

        for row in rows:
            req_h = float(row.total_req_hours or 0.0)
            ful_h = float(row.total_ful_hours or 0.0)
            unfil_h = round(max(0.0, req_h - ful_h), 2)
            pct = round((ful_h / req_h * 100.0), 2) if req_h > 0.0 else 100.0

            results.append(
                DemandAggregateItem(
                    dimension_type="project",
                    dimension_id=row.project_id,
                    dimension_name=row.project_name,
                    demand_lines_count=row.line_count,
                    total_required_headcount=int(row.total_headcount or 0),
                    total_required_hours=round(req_h, 2),
                    total_fulfilled_hours=round(ful_h, 2),
                    total_unfilled_hours=unfil_h,
                    fulfillment_percentage=min(100.0, pct),
                    is_fully_fulfilled=(unfil_h == 0.0),
                    calculated_at=now_str,
                )
            )
        return results

    @classmethod
    async def aggregate_by_role_async(
        cls,
        session: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> List[DemandAggregateItem]:
        """SQL-level aggregation of demand plans grouped by Job Role."""
        stmt = (
            select(
                Role.id.label("role_id"),
                Role.title.label("role_title"),
                func.count(DemandPlan.id).label("line_count"),
                func.sum(DemandPlan.required_headcount).label("total_headcount"),
                func.sum(DemandPlan.required_hours).label("total_req_hours"),
                func.sum(DemandPlan.fulfilled_hours).label("total_ful_hours"),
            )
            .join(Role, Role.id == DemandPlan.role_id)
            .group_by(Role.id, Role.title)
        )

        if start_date and end_date:
            stmt = stmt.where(
                and_(DemandPlan.start_date <= end_date, DemandPlan.end_date >= start_date)
            )

        res = await session.execute(stmt)
        rows = res.all()
        now_str = datetime.now(timezone.utc).isoformat()
        results = []

        for row in rows:
            req_h = float(row.total_req_hours or 0.0)
            ful_h = float(row.total_ful_hours or 0.0)
            unfil_h = round(max(0.0, req_h - ful_h), 2)
            pct = round((ful_h / req_h * 100.0), 2) if req_h > 0.0 else 100.0

            results.append(
                DemandAggregateItem(
                    dimension_type="role",
                    dimension_id=row.role_id,
                    dimension_name=row.role_title,
                    demand_lines_count=row.line_count,
                    total_required_headcount=int(row.total_headcount or 0),
                    total_required_hours=round(req_h, 2),
                    total_fulfilled_hours=round(ful_h, 2),
                    total_unfilled_hours=unfil_h,
                    fulfillment_percentage=min(100.0, pct),
                    is_fully_fulfilled=(unfil_h == 0.0),
                    calculated_at=now_str,
                )
            )
        return results

    @classmethod
    async def aggregate_by_skill_async(
        cls,
        session: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> List[DemandAggregateItem]:
        """SQL-level aggregation of demand plans grouped by Primary Skill."""
        stmt = (
            select(
                Skill.id.label("skill_id"),
                Skill.name.label("skill_name"),
                func.count(DemandPlan.id).label("line_count"),
                func.sum(DemandPlan.required_headcount).label("total_headcount"),
                func.sum(DemandPlan.required_hours).label("total_req_hours"),
                func.sum(DemandPlan.fulfilled_hours).label("total_ful_hours"),
            )
            .join(Skill, Skill.id == DemandPlan.primary_skill_id)
            .group_by(Skill.id, Skill.name)
        )

        if start_date and end_date:
            stmt = stmt.where(
                and_(DemandPlan.start_date <= end_date, DemandPlan.end_date >= start_date)
            )

        res = await session.execute(stmt)
        rows = res.all()
        now_str = datetime.now(timezone.utc).isoformat()
        results = []

        for row in rows:
            req_h = float(row.total_req_hours or 0.0)
            ful_h = float(row.total_ful_hours or 0.0)
            unfil_h = round(max(0.0, req_h - ful_h), 2)
            pct = round((ful_h / req_h * 100.0), 2) if req_h > 0.0 else 100.0

            results.append(
                DemandAggregateItem(
                    dimension_type="skill",
                    dimension_id=row.skill_id,
                    dimension_name=row.skill_name,
                    demand_lines_count=row.line_count,
                    total_required_headcount=int(row.total_headcount or 0),
                    total_required_hours=round(req_h, 2),
                    total_fulfilled_hours=round(ful_h, 2),
                    total_unfilled_hours=unfil_h,
                    fulfillment_percentage=min(100.0, pct),
                    is_fully_fulfilled=(unfil_h == 0.0),
                    calculated_at=now_str,
                )
            )
        return results

    @classmethod
    async def aggregate_by_priority_async(
        cls,
        session: AsyncSession,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> List[DemandAggregateItem]:
        """SQL-level aggregation of demand plans grouped by Staffing Priority (1 to 5)."""
        stmt = (
            select(
                DemandPlan.priority.label("priority"),
                func.count(DemandPlan.id).label("line_count"),
                func.sum(DemandPlan.required_headcount).label("total_headcount"),
                func.sum(DemandPlan.required_hours).label("total_req_hours"),
                func.sum(DemandPlan.fulfilled_hours).label("total_ful_hours"),
            )
            .group_by(DemandPlan.priority)
            .order_by(DemandPlan.priority)
        )
        res = await session.execute(stmt)
        rows = res.all()
        now_str = datetime.now(timezone.utc).isoformat()
        results = []

        priority_labels = {
            1: "Priority 1 (Critical / Executive)",
            2: "Priority 2 (High Strategic)",
            3: "Priority 3 (Standard Operational)",
            4: "Priority 4 (Low / Nice-to-have)",
            5: "Priority 5 (Backlog / Opportunistic)",
        }

        for row in rows:
            p_val = int(row.priority)
            req_h = float(row.total_req_hours or 0.0)
            ful_h = float(row.total_ful_hours or 0.0)
            unfil_h = round(max(0.0, req_h - ful_h), 2)
            pct = round((ful_h / req_h * 100.0), 2) if req_h > 0.0 else 100.0

            results.append(
                DemandAggregateItem(
                    dimension_type="priority",
                    dimension_id=str(p_val),
                    dimension_name=priority_labels.get(p_val, f"Priority {p_val}"),
                    demand_lines_count=row.line_count,
                    total_required_headcount=int(row.total_headcount or 0),
                    total_required_hours=round(req_h, 2),
                    total_fulfilled_hours=round(ful_h, 2),
                    total_unfilled_hours=unfil_h,
                    fulfillment_percentage=min(100.0, pct),
                    is_fully_fulfilled=(unfil_h == 0.0),
                    calculated_at=now_str,
                )
            )
        return results

