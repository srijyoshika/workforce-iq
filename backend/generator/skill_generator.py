"""
Skill Taxonomy, Role Requirements, and Employee Competency Profile Generator.
Generates Skill catalog, RoleSkill bridge requirements, and EmployeeSkill profiles
with proficiency distributions (1-5) and verification audit history.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
import numpy as np

from backend.generator.config import GeneratorConfig
from backend.generator.id_generator import (
    employee_skill_id,
    generate_uuid,
    role_skill_id,
    skill_id,
)
from backend.generator.master_data import ROLE_SKILL_ASSOCIATIONS, get_skills


def generate_skills(config: GeneratorConfig) -> List[Dict[str, Any]]:
    """Generate master skill taxonomy records."""
    raw_skills = get_skills(config.scale_config.skill_count)
    skills: List[Dict[str, Any]] = []

    for seq, item in enumerate(raw_skills, start=1):
        biz_id = skill_id(seq)
        pk_id = generate_uuid("Skill", biz_id)

        created_at = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        updated_at = datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 0, 0, 0, tzinfo=timezone.utc)

        skills.append({
            "id": pk_id,
            "business_id": biz_id,
            "name": item["name"],
            "category": item["cat"],
            "description": item["desc"],
            "is_active": True,
            "created_at": created_at,
            "updated_at": updated_at,
        })

    return skills


def generate_role_skills(
    config: GeneratorConfig,
    roles: List[Dict[str, Any]],
    skills: List[Dict[str, Any]],
    rng: np.random.Generator,
) -> List[Dict[str, Any]]:
    """Generate RoleSkill requirement bridge records."""
    role_skills: List[Dict[str, Any]] = []
    skill_name_to_id = {s["name"]: s["id"] for s in skills}
    skill_ids_pool = [s["id"] for s in skills]

    seq = 1
    for role in roles:
        role_code = role["code"]
        role_id = role["id"]

        # Determine target competencies from master association
        associated_skill_names = ROLE_SKILL_ASSOCIATIONS.get(role_code, [])
        target_skill_ids = [skill_name_to_id[name] for name in associated_skill_names if name in skill_name_to_id]

        # Ensure every role has at least 4 required skills from available pool
        while len(target_skill_ids) < 4:
            picked_id = skill_ids_pool[rng.integers(0, len(skill_ids_pool))]
            if picked_id not in target_skill_ids:
                target_skill_ids.append(picked_id)

        for s_id in target_skill_ids:
            biz_id = role_skill_id(seq)
            pk_id = generate_uuid("RoleSkill", biz_id)

            # High-level roles require higher proficiency
            is_senior = any(k in role_code for k in ["SR", "LD", "DIR", "PRN"])
            req_prof = int(rng.integers(4, 6)) if is_senior else int(rng.integers(2, 4))
            is_mandatory = bool(rng.choice([True, False], p=[0.75, 0.25]))
            weight = Decimal(str(round(rng.uniform(0.60, 1.00), 2)))

            created_at = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            updated_at = datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 0, 0, 0, tzinfo=timezone.utc)

            role_skills.append({
                "id": pk_id,
                "business_id": biz_id,
                "role_id": role_id,
                "skill_id": s_id,
                "required_proficiency": req_prof,
                "is_mandatory": is_mandatory,
                "importance_weight": weight,
                "created_at": created_at,
                "updated_at": updated_at,
            })
            seq += 1

    return role_skills


def generate_employee_skills(
    config: GeneratorConfig,
    employees: List[Dict[str, Any]],
    skills: List[Dict[str, Any]],
    role_skills: List[Dict[str, Any]],
    rng: np.random.Generator,
) -> List[Dict[str, Any]]:
    """
    Generate EmployeeSkill profiles with verification audit history.
    Models competency proficiency (1-5), verification states, and historical revisions.
    """
    # Group required skills by role
    role_to_skills: Dict[str, List[str]] = {}
    for rs in role_skills:
        role_to_skills.setdefault(rs["role_id"], []).append(rs["skill_id"])

    all_skill_ids = [s["id"] for s in skills]
    lead_employee_ids = [e["id"] for e in employees if e.get("experience_tier") in ["Senior", "Lead/Principal"]]
    if not lead_employee_ids:
        lead_employee_ids = [employees[0]["id"]]

    employee_skills: List[Dict[str, Any]] = []
    seq = 1

    for emp in employees:
        emp_id = emp["id"]
        role_id = emp["role_id"]
        hire_date = emp["hire_date"]
        exp_tier = emp.get("experience_tier", "Mid-Level")

        # Proficiency base range by experience tier
        if exp_tier == "Junior":
            min_p, max_p = 1, 3
        elif exp_tier == "Mid-Level":
            min_p, max_p = 2, 4
        elif exp_tier == "Senior":
            min_p, max_p = 3, 5
        else:  # Lead/Principal
            min_p, max_p = 4, 5

        # 1. Primary role competencies
        assigned_skills = list(role_to_skills.get(role_id, []))

        # 2. Add 2 to 5 complementary/secondary skills
        extra_count = rng.integers(2, 6)
        for _ in range(extra_count):
            pick = all_skill_ids[rng.integers(0, len(all_skill_ids))]
            if pick not in assigned_skills:
                assigned_skills.append(pick)

        for s_idx, s_id in enumerate(assigned_skills):
            biz_id = employee_skill_id(seq)
            pk_id = generate_uuid("EmployeeSkill", biz_id)

            proficiency = int(rng.integers(min_p, max_p + 1))
            status_pick = rng.choice(
                ["SELF_REPORTED", "MANAGER_VERIFIED", "ASSESSMENT_CERTIFIED"],
                p=[0.35, 0.45, 0.20],
            )

            # Verification metadata
            verified_by = None
            verified_at = None
            eff_start = hire_date + timedelta(days=int(s_idx * 15))

            if status_pick in ["MANAGER_VERIFIED", "ASSESSMENT_CERTIFIED"]:
                verified_by = rng.choice(lead_employee_ids)
                # Baseline verification is fresh (within 730-day validity window)
                days_ago = int(rng.integers(30, 500))
                verified_date = config.as_of_date - timedelta(days=days_ago)
                if verified_date < eff_start:
                    verified_date = eff_start + timedelta(days=int(rng.integers(5, 30)))
                verified_at = datetime(verified_date.year, verified_date.month, verified_date.day, 14, 0, 0, tzinfo=timezone.utc)

            created_at = datetime(eff_start.year, eff_start.month, eff_start.day, 9, 0, 0, tzinfo=timezone.utc)
            updated_at = datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 12, 0, 0, tzinfo=timezone.utc)

            # Add active current record
            employee_skills.append({
                "id": pk_id,
                "business_id": biz_id,
                "employee_id": emp_id,
                "skill_id": s_id,
                "proficiency_level": proficiency,
                "verification_status": status_pick,
                "verified_by_id": verified_by,
                "verified_at": verified_at,
                "effective_start_date": eff_start,
                "effective_end_date": None,
                "is_current": True,
                "notes": f"Proficiency assessed at level {proficiency} under standard evaluation rubric.",
                "created_at": created_at,
                "updated_at": updated_at,
            })
            seq += 1

            # Historical audit preservation: for ~15% of records, create a prior expired assessment
            if s_idx == 0 and exp_tier in ["Senior", "Lead/Principal"] and proficiency > 2:
                hist_biz_id = employee_skill_id(seq)
                hist_pk_id = generate_uuid("EmployeeSkill", hist_biz_id)

                prior_start = hire_date
                prior_end = eff_start - timedelta(days=1)
                prior_prof = max(1, proficiency - 1)

                employee_skills.append({
                    "id": hist_pk_id,
                    "business_id": hist_biz_id,
                    "employee_id": emp_id,
                    "skill_id": s_id,
                    "proficiency_level": prior_prof,
                    "verification_status": "SELF_REPORTED",
                    "verified_by_id": None,
                    "verified_at": None,
                    "effective_start_date": prior_start,
                    "effective_end_date": prior_end,
                    "is_current": False,
                    "notes": f"Initial self-reported entry at level {prior_prof}. Superseded by active certification.",
                    "created_at": datetime(prior_start.year, prior_start.month, prior_start.day, 9, 0, 0, tzinfo=timezone.utc),
                    "updated_at": datetime(prior_end.year, prior_end.month, prior_end.day, 17, 0, 0, tzinfo=timezone.utc),
                })
                seq += 1

    return employee_skills

