"""
Training and Upskilling Record Generator.
Generates skill upskilling and certification enrollment records across workforce cohorts.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List
import numpy as np

from backend.generator.config import GeneratorConfig
from backend.generator.id_generator import generate_uuid, training_id

TRAINING_PROVIDERS: List[str] = [
    "AWS Certified Solutions Academy",
    "Coursera Enterprise Campus",
    "DeepLearning.AI Professional Spec",
    "Linux Foundation & CNCF Academy",
    "Internal Engineering Guild",
    "Harvard Management Mentor",
    "Pluralsight Technology Index",
    "Databricks Lakehouse Academy",
]


def generate_trainings(
    config: GeneratorConfig,
    employees: List[Dict[str, Any]],
    skills: List[Dict[str, Any]],
    rng: np.random.Generator,
) -> List[Dict[str, Any]]:
    """
    Generate employee upskilling and certification records.
    """
    trainings: List[Dict[str, Any]] = []
    seq = 1
    year = config.planning_start_date.year

    skill_ids_pool = [s["id"] for s in skills]
    skill_names_pool = {s["id"]: s["name"] for s in skills}

    # Generate training for ~35% of the workforce
    candidate_employees = [e for e in employees if e["employment_status"] in ["ACTIVE", "PROBATION"]]
    sample_size = max(10, int(len(candidate_employees) * 0.35))
    selected_employees = rng.choice(candidate_employees, size=min(sample_size, len(candidate_employees)), replace=False)

    for emp in selected_employees:
        emp_id = emp["id"]
        target_s_id = rng.choice(skill_ids_pool)
        skill_name = skill_names_pool[target_s_id]

        biz_id = training_id(seq, year=year)
        pk_id = generate_uuid("Training", biz_id)
        seq += 1

        provider = rng.choice(TRAINING_PROVIDERS)
        title = f"Advanced {skill_name} Practitioner Certification"

        status_choice = str(rng.choice(["COMPLETED", "IN_PROGRESS", "PLANNED"], p=[0.40, 0.40, 0.20]))
        target_prof = int(rng.choice([3, 4, 5], p=[0.30, 0.50, 0.20]))

        # Scheduling
        start_month = int(rng.integers(1, 10))
        start_day = int(rng.integers(1, 25))
        start_date = date(year, start_month, start_day)

        duration_days = int(rng.integers(30, 90))
        if status_choice == "COMPLETED":
            completion_date = start_date + timedelta(days=duration_days)
            actual_cost = Decimal(str(round(rng.uniform(750.00, 3500.00), 2)))
        elif status_choice == "IN_PROGRESS":
            completion_date = None
            actual_cost = None
        else:  # PLANNED
            start_date = config.as_of_date + timedelta(days=int(rng.integers(15, 60)))
            completion_date = None
            actual_cost = None

        est_cost = Decimal(str(round(rng.uniform(750.00, 3500.00), 2)))

        created_at = datetime(start_date.year, start_date.month, start_date.day, 9, 0, 0, tzinfo=timezone.utc)
        updated_at = datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 12, 0, 0, tzinfo=timezone.utc)

        trainings.append({
            "id": pk_id,
            "business_id": biz_id,
            "title": title,
            "target_skill_id": target_s_id,
            "employee_id": emp_id,
            "provider": provider,
            "status": status_choice,
            "start_date": start_date,
            "completion_date": completion_date,
            "target_proficiency": target_prof,
            "estimated_cost": est_cost,
            "actual_cost": actual_cost,
            "notes": f"Enrolled in {provider} to advance competency in {skill_name}.",
            "created_at": created_at,
            "updated_at": updated_at,
        })

    return trainings

