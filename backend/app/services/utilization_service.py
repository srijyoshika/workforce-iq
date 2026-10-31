"""
Workforce Utilization Service for WorkforceIQ.

Calculates allocated, available, and remaining capacity hours, utilization percentages,
and categorizes utilization states (UNDERUTILIZED, NORMAL, HIGH, OVERALLOCATED).
Supports individual employee evaluation, batch aggregation, and departmental rollups.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.allocation import Allocation
from app.models.employee import Availability, Employee
from app.models.enums import AllocationStatus
from app.services.capacity_service import CapacityResult, CapacityService
from app.services.thresholds import DEFAULT_THRESHOLDS, PlanningThresholds


class UtilizationCategory(str, Enum):
    """Categorized workload capacity state."""
    UNDERUTILIZED = "UNDERUTILIZED"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    OVERALLOCATED = "OVERALLOCATED"
    ZERO_CAPACITY = "ZERO_CAPACITY"


@dataclass(frozen=True)
class UtilizationResult:
    """Detailed utilization metrics for an individual employee."""
    employee_id: str
    business_id: str
    start_date: date
    end_date: date
    available_hours: float
    allocated_hours: float
    remaining_hours: float
    utilization_percentage: float
    category: str
    is_overallocated: bool
    allocation_count: int
    calculated_at: str
    rule_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "business_id": self.business_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "available_hours": self.available_hours,
            "allocated_hours": self.allocated_hours,
            "remaining_hours": self.remaining_hours,
            "utilization_percentage": self.utilization_percentage,
            "category": self.category,
            "is_overallocated": self.is_overallocated,
            "allocation_count": self.allocation_count,
            "calculated_at": self.calculated_at,
            "rule_version": self.rule_version,
        }


@dataclass(frozen=True)
class DepartmentUtilizationSummary:
    """Aggregated department-level capacity and utilization benchmark."""
    department: str
    headcount: int
    total_available_hours: float
    total_allocated_hours: float
    average_utilization_percentage: float
    underutilized_count: int
    normal_count: int
    high_count: int
    overallocated_count: int
    calculated_at: str


class UtilizationService:
    """Canonical service for all employee and departmental utilization analytics."""

    @classmethod
    def classify_utilization(
        cls,
        utilization_pct: float,
        available_hours: float,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> UtilizationCategory:
        """Classify utilization percentage into canonical governance categories."""
        if available_hours <= 0.0:
            if utilization_pct > 0.0:
                return UtilizationCategory.OVERALLOCATED
            return UtilizationCategory.ZERO_CAPACITY

        if utilization_pct > thresholds.overallocation_threshold:
            return UtilizationCategory.OVERALLOCATED
        elif utilization_pct >= thresholds.normal_utilization_max:
            return UtilizationCategory.HIGH
        elif utilization_pct >= thresholds.normal_utilization_min:
            return UtilizationCategory.NORMAL
        else:
            return UtilizationCategory.UNDERUTILIZED

    @classmethod
    def calculate_utilization(
        cls,
        employee: Union[Employee, Dict[str, Any]],
        start_date: date,
        end_date: date,
        allocations: Optional[Sequence[Union[Allocation, Dict[str, Any]]]] = None,
        availabilities: Optional[Sequence[Union[Availability, Dict[str, Any]]]] = None,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> UtilizationResult:
        """
        Calculate employee workload utilization for a defined time window.
        Integrates with CapacityService for net available capacity.
        """
        cap_result: CapacityResult = CapacityService.calculate_period_capacity(
            employee=employee,
            start_date=start_date,
            end_date=end_date,
            availabilities=availabilities,
            thresholds=thresholds,
        )

        emp_id = cap_result.employee_id
        biz_id = cap_result.business_id
        avail_hours = cap_result.net_available_hours

        # Compute allocated hours during [start_date, end_date]
        allocated_hours = 0.0
        matching_allocs_count = 0

        if allocations:
            period_days = (end_date - start_date).days + 1
            for alloc in allocations:
                if isinstance(alloc, dict):
                    is_active = alloc.get("is_active", True)
                    status = alloc.get("status")
                    a_start = alloc.get("start_date")
                    a_end = alloc.get("end_date")
                    weekly_hours = float(alloc.get("allocated_hours_per_week") or 0.0)
                else:
                    is_active = getattr(alloc, "is_active", True)
                    status = getattr(alloc, "status", None)
                    a_start = getattr(alloc, "start_date", None)
                    a_end = getattr(alloc, "end_date", None)
                    weekly_hours = float(getattr(alloc, "allocated_hours_per_week", None) or 0.0)

                if not is_active:
                    continue

                if isinstance(status, AllocationStatus):
                    status_val = status.value
                else:
                    status_val = str(status)

                if status_val not in [AllocationStatus.ACTIVE.value, AllocationStatus.CONFIRMED.value, "ACTIVE", "CONFIRMED"]:
                    continue

                if not a_start or not a_end:
                    continue

                # Check date overlap
                o_start = max(start_date, a_start)
                o_end = min(end_date, a_end)
                if o_start <= o_end:
                    overlap_days = (o_end - o_start).days + 1
                    overlap_hours = (overlap_days / 7.0) * weekly_hours
                    allocated_hours += overlap_hours
                    matching_allocs_count += 1

        allocated_hours = round(allocated_hours, 2)
        remaining_hours = round(avail_hours - allocated_hours, 2)

        # Utilization calculation
        if avail_hours > 0.0:
            util_pct = round((allocated_hours / avail_hours) * 100.0, 2)
        else:
            util_pct = 999.0 if allocated_hours > 0.0 else 0.0

        category = cls.classify_utilization(util_pct, avail_hours, thresholds)
        is_overallocated = (category == UtilizationCategory.OVERALLOCATED)

        return UtilizationResult(
            employee_id=emp_id,
            business_id=biz_id,
            start_date=start_date,
            end_date=end_date,
            available_hours=avail_hours,
            allocated_hours=allocated_hours,
            remaining_hours=remaining_hours,
            utilization_percentage=util_pct,
            category=category.value,
            is_overallocated=is_overallocated,
            allocation_count=matching_allocs_count,
            calculated_at=datetime.now(timezone.utc).isoformat(),
            rule_version=thresholds.rule_version,
        )

    @classmethod
    async def get_employee_utilization_async(
        cls,
        session: AsyncSession,
        employee_id: str,
        start_date: date,
        end_date: date,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> Optional[UtilizationResult]:
        """Fetch database records and compute utilization for an individual employee."""
        emp_stmt = select(Employee).where(Employee.id == employee_id)
        emp_res = await session.execute(emp_stmt)
        employee = emp_res.scalar_one_or_none()
        if not employee:
            return None

        # Fetch active allocations overlapping period
        alloc_stmt = select(Allocation).where(
            and_(
                Allocation.employee_id == employee_id,
                Allocation.is_active == True,
                Allocation.status.in_([AllocationStatus.ACTIVE, AllocationStatus.CONFIRMED]),
                Allocation.start_date <= end_date,
                Allocation.end_date >= start_date,
            )
        )
        alloc_res = await session.execute(alloc_stmt)
        allocations = alloc_res.scalars().all()

        # Fetch availability
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

        return cls.calculate_utilization(
            employee=employee,
            start_date=start_date,
            end_date=end_date,
            allocations=allocations,
            availabilities=availabilities,
            thresholds=thresholds,
        )

    @classmethod
    async def get_department_utilization_summary_async(
        cls,
        session: AsyncSession,
        department: str,
        start_date: date,
        end_date: date,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> DepartmentUtilizationSummary:
        """Compute aggregated utilization metrics for an enterprise department."""
        # Query all active employees in department
        emp_stmt = select(Employee).where(
            and_(
                Employee.department == department,
                Employee.employment_status != AllocationStatus.CANCELLED,  # Active workforce
            )
        )
        emp_res = await session.execute(emp_stmt)
        employees = emp_res.scalars().all()

        if not employees:
            return DepartmentUtilizationSummary(
                department=department,
                headcount=0,
                total_available_hours=0.0,
                total_allocated_hours=0.0,
                average_utilization_percentage=0.0,
                underutilized_count=0,
                normal_count=0,
                high_count=0,
                overallocated_count=0,
                calculated_at=datetime.now(timezone.utc).isoformat(),
            )

        emp_ids = [e.id for e in employees]

        # Batch fetch allocations
        alloc_stmt = select(Allocation).where(
            and_(
                Allocation.employee_id.in_(emp_ids),
                Allocation.is_active == True,
                Allocation.status.in_([AllocationStatus.ACTIVE, AllocationStatus.CONFIRMED]),
                Allocation.start_date <= end_date,
                Allocation.end_date >= start_date,
            )
        )
        alloc_res = await session.execute(alloc_stmt)
        all_allocs = alloc_res.scalars().all()
        allocs_by_emp: Dict[str, List[Allocation]] = {}
        for a in all_allocs:
            allocs_by_emp.setdefault(a.employee_id, []).append(a)

        # Batch fetch availabilities
        av_stmt = select(Availability).where(
            and_(
                Availability.employee_id.in_(emp_ids),
                Availability.is_approved == True,
                Availability.start_date <= end_date,
                Availability.end_date >= start_date,
            )
        )
        av_res = await session.execute(av_stmt)
        all_avs = av_res.scalars().all()
        avs_by_emp: Dict[str, List[Availability]] = {}
        for av in all_avs:
            avs_by_emp.setdefault(av.employee_id, []).append(av)

        total_avail = 0.0
        total_alloc = 0.0
        under_c = 0
        norm_c = 0
        high_c = 0
        over_c = 0

        for emp in employees:
            res = cls.calculate_utilization(
                employee=emp,
                start_date=start_date,
                end_date=end_date,
                allocations=allocs_by_emp.get(emp.id, []),
                availabilities=avs_by_emp.get(emp.id, []),
                thresholds=thresholds,
            )
            total_avail += res.available_hours
            total_alloc += res.allocated_hours

            if res.category == UtilizationCategory.UNDERUTILIZED.value:
                under_c += 1
            elif res.category == UtilizationCategory.NORMAL.value:
                norm_c += 1
            elif res.category == UtilizationCategory.HIGH.value:
                high_c += 1
            elif res.category == UtilizationCategory.OVERALLOCATED.value:
                over_c += 1

        avg_util = round((total_alloc / total_avail * 100.0), 2) if total_avail > 0.0 else 0.0

        return DepartmentUtilizationSummary(
            department=department,
            headcount=len(employees),
            total_available_hours=round(total_avail, 2),
            total_allocated_hours=round(total_alloc, 2),
            average_utilization_percentage=avg_util,
            underutilized_count=under_c,
            normal_count=norm_c,
            high_count=high_c,
            overallocated_count=over_c,
            calculated_at=datetime.now(timezone.utc).isoformat(),
        )

