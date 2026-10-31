"""
Employee Availability and Leave Record Generator.
Models standard working capacity, PTO vacations, corporate public holidays,
sick leave, and bench availability periods.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List
import numpy as np

from backend.generator.config import GeneratorConfig
from backend.generator.id_generator import availability_id, generate_uuid

# Standard Corporate Holidays in 2026
CORPORATE_HOLIDAYS_2026: List[Dict[str, Any]] = [
    {"name": "New Year's Day", "date": date(2026, 1, 1)},
    {"name": "Martin Luther King Jr. Day", "date": date(2026, 1, 19)},
    {"name": "Memorial Day", "date": date(2026, 5, 25)},
    {"name": "Juneteenth", "date": date(2026, 6, 19)},
    {"name": "Independence Day", "date": date(2026, 7, 3)},
    {"name": "Labor Day", "date": date(2026, 9, 7)},
    {"name": "Thanksgiving Day", "date": date(2026, 11, 26)},
    {"name": "Day After Thanksgiving", "date": date(2026, 11, 27)},
    {"name": "Christmas Day", "date": date(2026, 12, 25)},
]


def generate_availabilities(
    config: GeneratorConfig,
    employees: List[Dict[str, Any]],
    rng: np.random.Generator,
) -> List[Dict[str, Any]]:
    """
    Generate employee availability and leave schedules across the 12-month planning year.
    """
    availabilities: List[Dict[str, Any]] = []
    seq = 1

    year = config.planning_start_date.year

    for emp in employees:
        emp_id = emp["id"]
        status = emp["employment_status"]
        std_hours = float(emp["standard_hours_per_week"])
        daily_hours = Decimal(str(round(std_hours / 5.0, 2)))

        # 1. Base Working Year Availability
        base_biz_id = availability_id(seq, year=year)
        base_pk = generate_uuid("Availability", base_biz_id)
        seq += 1

        created_at = datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        updated_at = datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 0, 0, 0, tzinfo=timezone.utc)

        availabilities.append({
            "id": base_pk,
            "business_id": base_biz_id,
            "employee_id": emp_id,
            "start_date": config.planning_start_date,
            "end_date": config.planning_end_date,
            "availability_type": "AVAILABLE" if status == "ACTIVE" else "BENCH" if status == "CONTRACTOR" else "PTO",
            "available_hours_per_day": daily_hours if status == "ACTIVE" else Decimal("0.00"),
            "capacity_percentage": Decimal("100.00") if status == "ACTIVE" else Decimal("0.00"),
            "reason": "Standard contractual baseline working capacity",
            "is_approved": True,
            "created_at": created_at,
            "updated_at": updated_at,
        })

        if status != "ACTIVE":
            continue

        # 2. Summer Vacation PTO Block (July or August, 1-2 weeks)
        pto_month = int(rng.choice([7, 8]))
        pto_day = int(rng.integers(1, 20))
        pto_start = date(year, pto_month, pto_day)
        pto_duration = int(rng.choice([5, 10]))  # 1 or 2 work weeks
        pto_end = pto_start + timedelta(days=pto_duration)

        pto_biz_id = availability_id(seq, year=year)
        pto_pk = generate_uuid("Availability", pto_biz_id)
        seq += 1

        availabilities.append({
            "id": pto_pk,
            "business_id": pto_biz_id,
            "employee_id": emp_id,
            "start_date": pto_start,
            "end_date": pto_end,
            "availability_type": "PTO",
            "available_hours_per_day": Decimal("0.00"),
            "capacity_percentage": Decimal("0.00"),
            "reason": "Annual summer vacation leave",
            "is_approved": True,
            "created_at": created_at,
            "updated_at": updated_at,
        })

        # 3. Winter Holiday PTO Block (Late December, 4-7 days)
        winter_start = date(year, 12, int(rng.integers(21, 26)))
        winter_end = date(year, 12, 31)

        win_biz_id = availability_id(seq, year=year)
        win_pk = generate_uuid("Availability", win_biz_id)
        seq += 1

        availabilities.append({
            "id": win_pk,
            "business_id": win_biz_id,
            "employee_id": emp_id,
            "start_date": winter_start,
            "end_date": winter_end,
            "availability_type": "PTO",
            "available_hours_per_day": Decimal("0.00"),
            "capacity_percentage": Decimal("0.00"),
            "reason": "Year-end holiday shutdown leave",
            "is_approved": True,
            "created_at": created_at,
            "updated_at": updated_at,
        })

        # 4. Occasional Sick Leave / Personal Days (for ~30% of employees)
        if rng.random() < 0.30:
            sick_month = int(rng.integers(2, 11))
            sick_start = date(year, sick_month, int(rng.integers(1, 25)))
            sick_end = sick_start + timedelta(days=int(rng.integers(1, 4)))

            sick_biz_id = availability_id(seq, year=year)
            sick_pk = generate_uuid("Availability", sick_biz_id)
            seq += 1

            availabilities.append({
                "id": sick_pk,
                "business_id": sick_biz_id,
                "employee_id": emp_id,
                "start_date": sick_start,
                "end_date": sick_end,
                "availability_type": "SICK_LEAVE",
                "available_hours_per_day": Decimal("0.00"),
                "capacity_percentage": Decimal("0.00"),
                "reason": "Unplanned medical / sick leave",
                "is_approved": True,
                "created_at": created_at,
                "updated_at": updated_at,
            })

    return availabilities

