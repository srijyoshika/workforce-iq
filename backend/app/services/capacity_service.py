"""
Employee Capacity Service for WorkforceIQ.

Calculates contractual, adjusted, and net available working capacity based on:
1. Contract standard hours (Full-time 40h, Part-time 20h/30h).
2. Lifecycle employment status (ACTIVE, ON_LEAVE, TERMINATED, CONTRACTOR, PROBATION).
3. Availability and scheduled leave deductions (PTO, HOLIDAY, SICK_LEAVE, TRAINING).
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Union
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Availability, Employee
from app.models.enums import AvailabilityType, EmploymentStatus
from app.services.thresholds import DEFAULT_THRESHOLDS, PlanningThresholds


@dataclass(frozen=True)
class CapacityResult:
    """Detailed capacity calculation output for an employee."""
    employee_id: str
    business_id: str
    start_date: date
    end_date: date
    contract_hours_per_week: float
    base_period_hours: float
    leave_hours_deducted: float
    lifecycle_status: str
    is_active_in_period: bool
    net_available_hours: float
    calculated_at: str
    rule_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "business_id": self.business_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "contract_hours_per_week": self.contract_hours_per_week,
            "base_period_hours": self.base_period_hours,
            "leave_hours_deducted": self.leave_hours_deducted,
            "lifecycle_status": self.lifecycle_status,
            "is_active_in_period": self.is_active_in_period,
            "net_available_hours": self.net_available_hours,
            "calculated_at": self.calculated_at,
            "rule_version": self.rule_version,
        }


class CapacityService:
    """Canonical engine for all workforce capacity calculations."""

    @classmethod
    def calculate_period_capacity(
        cls,
        employee: Union[Employee, Dict[str, Any]],
        start_date: date,
        end_date: date,
        availabilities: Optional[Sequence[Union[Availability, Dict[str, Any]]]] = None,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> CapacityResult:
        """
        Calculate net available working capacity for an employee in [start_date, end_date].
        Operates on either SQLAlchemy Employee model or serialized dictionary.
        """
        if end_date < start_date:
            raise ValueError(f"end_date ({end_date}) cannot be earlier than start_date ({start_date})")

        # Extract attributes handling both model and dict
        if isinstance(employee, dict):
            emp_id = employee.get("id")
            biz_id = employee.get("business_id", "EMP-UNKNOWN")
            hire_date = employee.get("hire_date")
            exit_date = employee.get("exit_date")
            emp_status = employee.get("employment_status", "ACTIVE")
            std_hours = float(employee.get("standard_hours_per_week") or thresholds.default_standard_hours)
        else:
            emp_id = getattr(employee, "id", None)
            biz_id = getattr(employee, "business_id", "EMP-UNKNOWN")
            hire_date = getattr(employee, "hire_date", None)
            exit_date = getattr(employee, "exit_date", None)
            emp_status = getattr(employee, "employment_status", "ACTIVE")
            std_hours = float(getattr(employee, "standard_hours_per_week", None) or thresholds.default_standard_hours)

        if isinstance(emp_status, EmploymentStatus):
            emp_status_val = emp_status.value
        else:
            emp_status_val = str(emp_status)

        # Check employment active window
        is_active = True
        if hire_date and hire_date > end_date:
            is_active = False
        if exit_date and exit_date < start_date:
            is_active = False
        if emp_status_val == EmploymentStatus.TERMINATED.value:
            if not exit_date or exit_date <= start_date:
                is_active = False

        # Calculate calendar days and working days (Monday-Friday) in period
        working_days = 0
        curr = start_date
        while curr <= end_date:
            if curr.weekday() < 5:  # Monday to Friday
                # Check if employee was hired and not exited on this specific day
                day_active = True
                if hire_date and curr < hire_date:
                    day_active = False
                if exit_date and curr > exit_date:
                    day_active = False
                if day_active:
                    working_days += 1
            curr += timedelta(days=1)

        daily_rate = std_hours / 5.0
        base_period_hours = round(working_days * daily_rate, 2)

        # Lifecycle Status Adjustments:
        # ON_LEAVE without specific availability overrides reduces base capacity to zero
        if emp_status_val == EmploymentStatus.ON_LEAVE.value:
            base_period_hours = 0.0

        if not is_active:
            return CapacityResult(
                employee_id=emp_id,
                business_id=biz_id,
                start_date=start_date,
                end_date=end_date,
                contract_hours_per_week=std_hours,
                base_period_hours=0.0,
                leave_hours_deducted=0.0,
                lifecycle_status=emp_status_val,
                is_active_in_period=False,
                net_available_hours=0.0,
                calculated_at=datetime.now(timezone.utc).isoformat(),
                rule_version=thresholds.rule_version,
            )

        # Calculate leave and availability deductions
        leave_hours = 0.0
        if availabilities and base_period_hours > 0.0:
            for av in availabilities:
                if isinstance(av, dict):
                    av_type = av.get("availability_type")
                    av_start = av.get("start_date")
                    av_end = av.get("end_date")
                    cap_pct = float(av.get("capacity_percentage") or 0.0)
                    hrs_per_day = float(av.get("available_hours_per_day") or 0.0)
                else:
                    av_type = getattr(av, "availability_type", None)
                    av_start = getattr(av, "start_date", None)
                    av_end = getattr(av, "end_date", None)
                    cap_pct = float(getattr(av, "capacity_percentage", 0.0) or 0.0)
                    hrs_per_day = float(getattr(av, "available_hours_per_day", 0.0) or 0.0)

                if isinstance(av_type, AvailabilityType):
                    av_type_val = av_type.value
                else:
                    av_type_val = str(av_type)

                deductible_types = {
                    AvailabilityType.PTO.value,
                    AvailabilityType.HOLIDAY.value,
                    AvailabilityType.SICK_LEAVE.value,
                    AvailabilityType.TRAINING.value,
                    AvailabilityType.RESERVED.value,
                }
                if av_type_val not in deductible_types:
                    continue

                if not av_start or not av_end:
                    continue

                # Compute overlapping working days
                o_start = max(start_date, av_start)
                o_end = min(end_date, av_end)
                if o_start <= o_end:
                    overlap_workdays = 0
                    o_curr = o_start
                    while o_curr <= o_end:
                        if o_curr.weekday() < 5:
                            overlap_workdays += 1
                        o_curr += timedelta(days=1)

                    if cap_pct == 0.0 and hrs_per_day == 0.0:
                        # Full day deduction
                        leave_hours += overlap_workdays * daily_rate
                    else:
                        # Partial day deduction
                        lost_hours_per_day = max(0.0, daily_rate - hrs_per_day)
                        leave_hours += overlap_workdays * lost_hours_per_day

        leave_hours = round(min(base_period_hours, leave_hours), 2)
        net_hours = round(max(0.0, base_period_hours - leave_hours), 2)

        return CapacityResult(
            employee_id=emp_id,
            business_id=biz_id,
            start_date=start_date,
            end_date=end_date,
            contract_hours_per_week=std_hours,
            base_period_hours=base_period_hours,
            leave_hours_deducted=leave_hours,
            lifecycle_status=emp_status_val,
            is_active_in_period=is_active,
            net_available_hours=net_hours,
            calculated_at=datetime.now(timezone.utc).isoformat(),
            rule_version=thresholds.rule_version,
        )

    @classmethod
    def calculate_weekly_capacity(
        cls,
        employee: Union[Employee, Dict[str, Any]],
        target_week_start: date,
        availabilities: Optional[Sequence[Union[Availability, Dict[str, Any]]]] = None,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> CapacityResult:
        """Convenience method to calculate capacity for a standard 7-day Monday-Sunday week."""
        target_week_end = target_week_start + timedelta(days=6)
        return cls.calculate_period_capacity(
            employee=employee,
            start_date=target_week_start,
            end_date=target_week_end,
            availabilities=availabilities,
            thresholds=thresholds,
        )

    @classmethod
    async def get_employee_capacity_async(
        cls,
        session: AsyncSession,
        employee_id: str,
        start_date: date,
        end_date: date,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> Optional[CapacityResult]:
        """Fetch employee and active availability records from database and compute capacity."""
        # Query employee
        emp_stmt = select(Employee).where(Employee.id == employee_id)
        emp_res = await session.execute(emp_stmt)
        employee = emp_res.scalar_one_or_none()
        if not employee:
            return None

        # Query overlapping availability
        av_stmt = select(Availability).where(
            and_(
                Availability.employee_id == employee_id,
                Availability.is_approved == True,
                Availability.start_date <= end_date,
                Availability.end_date >= start_date,
            )
        )
        av_res = await session.execute(av_stmt)
        availabilities = av_res.scalars().all()

        return cls.calculate_period_capacity(
            employee=employee,
            start_date=start_date,
            end_date=end_date,
            availabilities=availabilities,
            thresholds=thresholds,
        )

    @classmethod
    async def get_batch_employee_capacities_async(
        cls,
        session: AsyncSession,
        employee_ids: List[str],
        start_date: date,
        end_date: date,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> Dict[str, CapacityResult]:
        """Batch query employees and availabilities to calculate capacity in high throughput."""
        if not employee_ids:
            return {}

        emp_stmt = select(Employee).where(Employee.id.in_(employee_ids))
        emp_res = await session.execute(emp_stmt)
        employees = emp_res.scalars().all()

        av_stmt = select(Availability).where(
            and_(
                Availability.employee_id.in_(employee_ids),
                Availability.is_approved == True,
                Availability.start_date <= end_date,
                Availability.end_date >= start_date,
            )
        )
        av_res = await session.execute(av_stmt)
        all_availabilities = av_res.scalars().all()

        av_by_emp: Dict[str, List[Availability]] = {}
        for av in all_availabilities:
            av_by_emp.setdefault(av.employee_id, []).append(av)

        results = {}
        for emp in employees:
            results[emp.id] = cls.calculate_period_capacity(
                employee=emp,
                start_date=start_date,
                end_date=end_date,
                availabilities=av_by_emp.get(emp.id, []),
                thresholds=thresholds,
            )
        return results

