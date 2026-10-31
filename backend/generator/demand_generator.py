"""
Project Demand Plan Generator.
Generates 12 months (52 weeks) of time-phased workforce demand line items with
seasonal quarterly variations, role requirements, and proficiency benchmarks.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List
import numpy as np

from backend.generator.config import GeneratorConfig
from backend.generator.id_generator import demand_plan_id, generate_uuid


def generate_demand_plans(
    config: GeneratorConfig,
    projects: List[Dict[str, Any]],
    roles: List[Dict[str, Any]],
    skills: List[Dict[str, Any]],
    role_skills: List[Dict[str, Any]],
    rng: np.random.Generator,
) -> List[Dict[str, Any]]:
    """
    Generate weekly time-phased demand plans across 12 months.
    Applies seasonal variations across Q1-Q4.
    """
    demand_plans: List[Dict[str, Any]] = []

    # Map role -> required skills
    role_to_skills: Dict[str, List[str]] = {}
    for rs in role_skills:
        role_to_skills.setdefault(rs["role_id"], []).append(rs["skill_id"])

    role_ids = [r["id"] for r in roles]
    skill_ids_all = [s["id"] for s in skills]

    # Pre-calculate 52 weeks of the 2026 planning year
    planning_year = config.planning_start_date.year
    first_monday = config.planning_start_date
    while first_monday.weekday() != 0:
        first_monday += timedelta(days=1)

    # Filter projects that require demand
    eligible_projects = [p for p in projects if p["status"] in ["ACTIVE", "APPROVED", "PIPELINE"]]
    if not eligible_projects:
        eligible_projects = projects[:10]

    for p in eligible_projects:
        p_id = p["id"]
        p_biz_id = p["business_id"]
        p_start = p["start_date"]
        p_end = p["end_date"]

        # 2 to 5 distinct roles demanded on this project
        demanded_role_count = rng.integers(2, 6)
        project_roles = rng.choice(role_ids, size=min(demanded_role_count, len(role_ids)), replace=False)

        for week_idx in range(1, 53):
            week_start = first_monday + timedelta(weeks=week_idx - 1)
            week_end = week_start + timedelta(days=6)
            week_str = f"{planning_year}W{week_idx:02d}"

            # Only generate demand lines if the project is active during this week
            if week_end < p_start or week_start > p_end:
                continue

            # Determine quarter seasonality multiplier
            quarter = ((week_idx - 1) // 13) + 1
            seasonal_factor = config.quarterly_seasonality_multipliers.get(quarter, 1.0)

            for r_idx, r_id in enumerate(project_roles):
                # Unique business ID per project, week, and role slot
                biz_id = f"DEM-{p_biz_id}-{week_str}-R{r_idx + 1}"
                pk_id = generate_uuid("DemandPlan", biz_id)

                # Select primary skill for this role
                candidate_skills = role_to_skills.get(r_id, skill_ids_all)
                primary_skill = rng.choice(candidate_skills) if candidate_skills else skill_ids_all[0]

                min_prof = int(rng.choice([3, 4, 5], p=[0.50, 0.40, 0.10]))
                headcount = int(rng.choice([1, 2], p=[0.85, 0.15]))

                # Base 40 hours per headcount * seasonal factor
                base_hours = 40.0 * headcount * seasonal_factor
                req_hours = Decimal(str(round(base_hours, 2)))

                priority = int(rng.choice([1, 2, 3, 4], p=[0.20, 0.40, 0.30, 0.10]))
                status = "APPROVED" if p["status"] in ["ACTIVE", "APPROVED"] else "DRAFT"

                created_at = datetime(p_start.year, p_start.month, p_start.day, 9, 0, 0, tzinfo=timezone.utc)
                updated_at = datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 12, 0, 0, tzinfo=timezone.utc)

                demand_plans.append({
                    "id": pk_id,
                    "business_id": biz_id,
                    "project_id": p_id,
                    "role_id": r_id,
                    "primary_skill_id": primary_skill,
                    "min_proficiency": min_prof,
                    "start_date": week_start,
                    "end_date": week_end,
                    "week_number": week_str,
                    "required_headcount": headcount,
                    "required_hours": req_hours,
                    "fulfilled_hours": Decimal("0.00"),  # Populated during allocation
                    "status": status,
                    "priority": priority,
                    "created_at": created_at,
                    "updated_at": updated_at,
                })

    return demand_plans

