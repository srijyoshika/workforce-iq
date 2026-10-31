"""
Project-Based Demand Aggregation and Forward Forecasting Service.

Aggregates planned project demand lines across:
1. Role (`role_id`)
2. Skill (`primary_skill_id`)
3. Department
4. Week (`start_date` / calendar week)
5. Project Priority (Tiers 1 to 4)

Produces structured forward project commitments for portfolio capacity planning.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import DemandStatus, ProjectStatus
from app.models.project import DemandPlan, Project
from app.services.forecasting.types import ProjectDemandAggregate


class ProjectDemandAggregator:
    """Aggregates and formats time-phased project demand from plans and portfolio pipelines."""

    @classmethod
    def aggregate_project_demands(
        cls,
        demand_plans: Sequence[Union[DemandPlan, Dict[str, Any]]],
        projects: Optional[Sequence[Union[Project, Dict[str, Any]]]] = None,
        roles_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[ProjectDemandAggregate]:
        """
        Aggregate planned demand items across (role, skill, department, week, priority).
        Accepts either SQLAlchemy models or serializable dictionaries.
        """
        # Build lookup for project attributes (e.g. department, priority, name)
        proj_dict: Dict[str, Dict[str, Any]] = {}
        if projects:
            for p in projects:
                p_id = p["id"] if isinstance(p, dict) else p.id
                proj_dict[p_id] = {
                    "id": p_id,
                    "name": p.get("name", p_id) if isinstance(p, dict) else p.name,
                    "priority": p.get("priority", 2) if isinstance(p, dict) else getattr(p, "priority", 2),
                    "department": p.get("department", "Engineering") if isinstance(p, dict) else getattr(p, "department", "Engineering"),
                }

        roles_dict = roles_map or {}

        # Grouping accumulator: key = (role_id, skill_id, department, week_label, priority)
        grouped: Dict[Tuple, Dict[str, Any]] = {}

        for d in demand_plans:
            # Filter only active/planned demands
            status = d.get("status") if isinstance(d, dict) else (d.status.value if hasattr(d.status, "value") else str(d.status))
            if status in ("CANCELLED", "FULFILLED", DemandStatus.CANCELLED.value, DemandStatus.FULFILLED.value):
                continue

            p_id = d["project_id"] if isinstance(d, dict) else d.project_id
            r_id = d["role_id"] if isinstance(d, dict) else d.role_id
            s_id = (d.get("primary_skill_id") if isinstance(d, dict) else d.primary_skill_id) or "SKL-GENERAL"
            s_date = d["start_date"] if isinstance(d, dict) else d.start_date
            e_date = d["end_date"] if isinstance(d, dict) else d.end_date

            if isinstance(s_date, str):
                s_date = date.fromisoformat(s_date)
            if isinstance(e_date, str):
                e_date = date.fromisoformat(e_date)

            week_label = f"{s_date.year}W{s_date.isocalendar()[1]:02d}"

            # Department derivation
            p_info = proj_dict.get(p_id, {})
            dept = p_info.get("department")
            if not dept:
                r_info = roles_dict.get(r_id, {})
                dept = r_info.get("department", "Engineering")

            # Priority derivation
            prio = int(d.get("priority", p_info.get("priority", 2)) if isinstance(d, dict) else getattr(d, "priority", p_info.get("priority", 2)))

            hc = int(d["required_headcount"] if isinstance(d, dict) else d.required_headcount)
            hrs = float(d.get("required_hours", hc * 40.0) if isinstance(d, dict) else (getattr(d, "required_hours", None) or (hc * 40.0)))

            group_key = (r_id, s_id, dept, week_label, prio)

            if group_key not in grouped:
                grouped[group_key] = {
                    "role_id": r_id,
                    "skill_id": s_id,
                    "department": dept,
                    "week_label": week_label,
                    "start_date": str(s_date),
                    "end_date": str(e_date),
                    "priority_level": prio,
                    "total_required_headcount": 0,
                    "total_required_hours": 0.0,
                    "project_ids": set(),
                }

            grouped[group_key]["total_required_headcount"] += hc
            grouped[group_key]["total_required_hours"] += hrs
            grouped[group_key]["project_ids"].add(p_id)

        aggregates: List[ProjectDemandAggregate] = []
        # Sort chronologically by week, then priority
        for k in sorted(grouped.keys(), key=lambda x: (x[3], x[4], x[0])):
            item = grouped[k]
            aggregates.append(
                ProjectDemandAggregate(
                    role_id=item["role_id"],
                    skill_id=item["skill_id"],
                    department=item["department"],
                    week_label=item["week_label"],
                    start_date=item["start_date"],
                    end_date=item["end_date"],
                    priority_level=item["priority_level"],
                    total_required_headcount=item["total_required_headcount"],
                    total_required_hours=round(item["total_required_hours"], 2),
                    active_projects_count=len(item["project_ids"]),
                    project_ids=sorted(list(item["project_ids"])),
                )
            )

        return aggregates

    @classmethod
    async def aggregate_project_demands_async(
        cls,
        session: AsyncSession,
        department: Optional[str] = None,
        min_priority: Optional[int] = None,
    ) -> List[ProjectDemandAggregate]:
        """
        Asynchronously load and aggregate active project demand plans from the database.
        """
        stmt_proj = select(Project)
        res_proj = await session.execute(stmt_proj)
        projects = res_proj.scalars().all()

        stmt_dem = select(DemandPlan).where(
            DemandPlan.status.in_([DemandStatus.DRAFT, DemandStatus.SUBMITTED, DemandStatus.APPROVED, DemandStatus.PARTIALLY_FULFILLED])
        )
        res_dem = await session.execute(stmt_dem)
        demand_plans = res_dem.scalars().all()

        aggregates = cls.aggregate_project_demands(
            demand_plans=demand_plans,
            projects=projects,
        )

        if department:
            aggregates = [a for a in aggregates if a.department.lower() == department.lower()]
        if min_priority is not None:
            aggregates = [a for a in aggregates if a.priority_level <= min_priority]

        return aggregates
