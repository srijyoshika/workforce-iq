"""
WorkforceIQ Planning and Analytics Thresholds Configuration.
Encapsulates configurable business rules, utilization boundaries, and governance limits.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PlanningThresholds:
    """
    Configurable governance thresholds and calculation rules.
    Every analytics calculation references this canonical configuration.
    """
    rule_version: str = "1.0.0"

    # Utilization Percentage Boundaries
    underutilization_threshold: float = 70.0   # < 70% is underutilized
    normal_utilization_min: float = 70.0       # 70% - 90% is normal
    normal_utilization_max: float = 90.0
    high_utilization_max: float = 100.0        # 90% - 100% is high
    overallocation_threshold: float = 100.0    # > 100% is overallocated

    # Competency and Skill Validity
    stale_skill_validity_days: int = 730       # 2 years (730 days)

    # Risk & Staffing Shortage Windows
    shortage_warning_days: int = 60            # Projects starting within 60 days
    critical_priority_level: int = 1           # Priority 1 is critical demand

    # Gap Severity Categorization (% unfilled threshold)
    critical_gap_unfilled_pct: float = 60.0
    high_gap_unfilled_pct: float = 40.0
    medium_gap_unfilled_pct: float = 20.0

    # Default Contract Weekly Hours (Full-Time)
    default_standard_hours: float = 40.0


DEFAULT_THRESHOLDS = PlanningThresholds()

