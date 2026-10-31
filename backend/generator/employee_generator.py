"""
Employee Master Record Generator.
Generates realistic workforce personnel with diverse employment types, experience tiers,
contractual capacity, and deterministic attributes.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import random
from typing import Any, Dict, List
from faker import Faker
import numpy as np

from backend.generator.config import GeneratorConfig
from backend.generator.id_generator import employee_id, generate_uuid


def generate_employees(
    config: GeneratorConfig,
    roles: List[Dict[str, Any]],
    faker: Faker,
    rng: np.random.Generator,
) -> List[Dict[str, Any]]:
    """
    Generate employee master records.
    Deterministic, parameterized by GeneratorConfig scale and seed.
    """
    total_count = config.scale_config.employee_count
    employees: List[Dict[str, Any]] = []

    # Map roles by department for realistic assignment
    role_dept_map = {r["id"]: r["department"] for r in roles}
    role_ids = [r["id"] for r in roles]
    role_rates = {r["id"]: float(r.get("standard_hourly_rate") or 100.0) for r in roles}

    # Extract weights
    status_keys = list(config.employment_status_weights.keys())
    status_probs = list(config.employment_status_weights.values())

    capacity_keys = list(config.work_capacity_distribution.keys())
    capacity_probs = list(config.work_capacity_distribution.values())

    exp_keys = list(config.experience_level_weights.keys())
    exp_probs = list(config.experience_level_weights.values())

    for seq in range(1, total_count + 1):
        biz_id = employee_id(seq)
        pk_id = generate_uuid("Employee", biz_id)

        # Deterministic role assignment
        assigned_role_id = role_ids[(seq - 1) % len(role_ids)]
        department = role_dept_map[assigned_role_id]
        base_rate = role_rates[assigned_role_id]

        # Name from Faker
        first_name = faker.first_name()
        last_name = faker.last_name()
        # Clean special chars for deterministic email
        clean_first = "".join(c for c in first_name.lower() if c.isalnum())
        clean_last = "".join(c for c in last_name.lower() if c.isalnum())
        email = f"{clean_first}.{clean_last}.{seq:05d}@workforceiq.synthetic"

        # Demographics
        location = rng.choice(config.locations)
        employment_status = rng.choice(status_keys, p=status_probs)
        standard_hours = Decimal(str(rng.choice(capacity_keys, p=capacity_probs)))
        experience_tier = rng.choice(exp_keys, p=exp_probs)

        # Hire date based on experience tier
        as_of = config.as_of_date
        if experience_tier == "Junior":
            tenure_days = rng.integers(180, 730)
            rate_multiplier = rng.uniform(0.70, 0.85)
        elif experience_tier == "Mid-Level":
            tenure_days = rng.integers(731, 1825)
            rate_multiplier = rng.uniform(0.90, 1.05)
        elif experience_tier == "Senior":
            tenure_days = rng.integers(1826, 3285)
            rate_multiplier = rng.uniform(1.10, 1.30)
        else:  # Lead/Principal
            tenure_days = rng.integers(3286, 5475)
            rate_multiplier = rng.uniform(1.35, 1.65)

        hire_date = as_of - timedelta(days=int(tenure_days))
        exit_date = None

        if employment_status == "TERMINATED":
            employed_days = rng.integers(90, tenure_days)
            exit_date = hire_date + timedelta(days=int(employed_days))

        # Hourly cost calculation
        cost_rate = Decimal(str(round(base_rate * rate_multiplier, 2)))

        created_at = datetime(hire_date.year, hire_date.month, hire_date.day, 8, 0, 0, tzinfo=timezone.utc)
        updated_at = datetime(as_of.year, as_of.month, as_of.day, 12, 0, 0, tzinfo=timezone.utc)

        employees.append({
            "id": pk_id,
            "business_id": biz_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "role_id": assigned_role_id,
            "department": department,
            "location": location,
            "employment_status": employment_status,
            "hire_date": hire_date,
            "exit_date": exit_date,
            "standard_hours_per_week": standard_hours,
            "cost_rate_per_hour": cost_rate,
            "experience_tier": experience_tier,  # Synthetic generator metadata
            "created_at": created_at,
            "updated_at": updated_at,
        })

    return employees

