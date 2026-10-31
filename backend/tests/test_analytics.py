"""
WorkforceIQ Analytics and Business Calculation Engine Test Suite.

Verifies canonical calculations and operational rules across all services:
1. Capacity Service: Standard full-time, part-time, leave deductions, zero available capacity.
2. Utilization Service: Underutilized, Normal, High, Overallocated, and boundary zero capacity.
3. Skill Matching Service: Proficiency scoring, availability weight, and stale skill invalidation.
4. Demand Aggregation Service: Aggregations across project, role, skill, and priority tiers.
5. Gap Analysis Service: Talent deficits, supply vs demand hours, dynamic severity tiers.
6. Risk Service: Overallocation, stale skills, duplicate demand, overlapping allocations, and staffing shortages.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pytest

from app.models.enums import (
    AllocationStatus,
    AvailabilityType,
    EmploymentStatus,
    GapSeverity,
    IssueSeverity,
    IssueType,
    ProjectStatus,
    VerificationStatus,
)
from app.services.capacity_service import CapacityResult, CapacityService
from app.services.demand_aggregation_service import DemandAggregationService
from app.services.gap_analysis_service import GapAnalysisService
from app.services.risk_service import RiskService
from app.services.skill_matching_service import CandidateMatch, SkillMatchingService
from app.services.thresholds import DEFAULT_THRESHOLDS, PlanningThresholds
from app.services.utilization_service import (
    UtilizationCategory,
    UtilizationResult,
    UtilizationService,
)


# =============================================================================
# 1. CAPACITY SERVICE TESTS
# =============================================================================

def test_capacity_normal_fulltime():
    """Verify normal full-time employee with 40 contract hours and no leave."""
    emp = {
        "id": "EMP-001",
        "business_id": "EMP-000001",
        "employment_status": "ACTIVE",
        "standard_hours_per_week": 40.0,
    }
    start = date(2026, 11, 2)
    end = date(2026, 11, 8)  # 1 week

    res = CapacityService.calculate_period_capacity(emp, start, end, availabilities=[])
    assert res.contract_hours_per_week == 40.0
    assert res.base_period_hours == 40.0
    assert res.leave_hours_deducted == 0.0
    assert res.net_available_hours == 40.0
    assert res.is_active_in_period is True


def test_capacity_part_time_employee():
    """Verify part-time employees (20h and 30h) calculate proportionate capacity."""
    emp_20 = {
        "id": "EMP-PT-20",
        "business_id": "EMP-000020",
        "employment_status": "ACTIVE",
        "standard_hours_per_week": 20.0,
    }
    emp_30 = {
        "id": "EMP-PT-30",
        "business_id": "EMP-000030",
        "employment_status": "ACTIVE",
        "standard_hours_per_week": 30.0,
    }
    start = date(2026, 11, 2)
    end = date(2026, 11, 8)

    res_20 = CapacityService.calculate_period_capacity(emp_20, start, end)
    res_30 = CapacityService.calculate_period_capacity(emp_30, start, end)

    assert res_20.net_available_hours == 20.0
    assert res_30.net_available_hours == 30.0


def test_capacity_with_leave_deductions():
    """Verify leave records (PTO, sick leave) deduct accurately based on daily hours."""
    emp = {
        "id": "EMP-002",
        "business_id": "EMP-000002",
        "employment_status": "ACTIVE",
        "standard_hours_per_week": 40.0,
    }
    start = date(2026, 11, 2)
    end = date(2026, 11, 8)
    # 1 full day of PTO (8h) + 1 half day of SICK_LEAVE (4h deduction)
    leave = [
        {
            "employee_id": "EMP-002",
            "availability_type": "PTO",
            "start_date": date(2026, 11, 3),
            "end_date": date(2026, 11, 3),
            "capacity_percentage": 0.0,
            "available_hours_per_day": 0.0,
        },
        {
            "employee_id": "EMP-002",
            "availability_type": "SICK_LEAVE",
            "start_date": date(2026, 11, 4),
            "end_date": date(2026, 11, 4),
            "capacity_percentage": 50.0,
            "available_hours_per_day": 4.0,
        },
    ]

    res = CapacityService.calculate_period_capacity(emp, start, end, availabilities=leave)
    assert res.base_period_hours == 40.0
    assert res.leave_hours_deducted == 12.0
    assert res.net_available_hours == 28.0


def test_capacity_zero_available_capacity():
    """Verify zero capacity conditions: terminated employee or full-week PTO."""
    # 1. Terminated status
    emp_term = {
        "id": "EMP-TERM",
        "business_id": "EMP-000099",
        "employment_status": "TERMINATED",
        "standard_hours_per_week": 40.0,
    }
    start = date(2026, 11, 2)
    end = date(2026, 11, 8)
    res_term = CapacityService.calculate_period_capacity(emp_term, start, end)
    assert res_term.is_active_in_period is False
    assert res_term.net_available_hours == 0.0

    # 2. Full-week approved leave (Monday to Friday = 5 working days * 8h = 40h)
    emp_pto = {
        "id": "EMP-PTO",
        "business_id": "EMP-000100",
        "employment_status": "ACTIVE",
        "standard_hours_per_week": 40.0,
    }
    leave_full = [
        {
            "employee_id": "EMP-PTO",
            "availability_type": "PTO",
            "start_date": start,
            "end_date": end,
            "capacity_percentage": 0.0,
            "available_hours_per_day": 0.0,
        }
    ]
    res_pto = CapacityService.calculate_period_capacity(emp_pto, start, end, availabilities=leave_full)
    assert res_pto.net_available_hours == 0.0
    assert res_pto.leave_hours_deducted == 40.0


# =============================================================================
# 2. UTILIZATION SERVICE TESTS
# =============================================================================

def test_utilization_threshold_categorization():
    """Verify all 4 utilization categories based on configured boundaries and calculations."""
    emp = {
        "id": "EMP-UTIL",
        "business_id": "EMP-000001",
        "employment_status": "ACTIVE",
        "standard_hours_per_week": 40.0,
    }
    start = date(2026, 11, 2)
    end = date(2026, 11, 8)  # 7-day period

    # 1. Underutilized (< 70%): 20 hours -> 50%
    alloc_under = [{
        "employee_id": "EMP-UTIL",
        "allocated_hours_per_week": 20.0,
        "start_date": start,
        "end_date": end,
        "is_active": True,
        "status": "ACTIVE",
    }]
    u_under = UtilizationService.calculate_utilization(emp, start, end, allocations=alloc_under)
    assert u_under.utilization_percentage == 50.0
    assert u_under.category == UtilizationCategory.UNDERUTILIZED.value
    assert u_under.remaining_hours == 20.0
    assert u_under.is_overallocated is False

    # 2. Normal (70% - 90%): 32 hours -> 80%
    alloc_norm = [{
        "employee_id": "EMP-UTIL",
        "allocated_hours_per_week": 32.0,
        "start_date": start,
        "end_date": end,
        "is_active": True,
        "status": "ACTIVE",
    }]
    u_norm = UtilizationService.calculate_utilization(emp, start, end, allocations=alloc_norm)
    assert u_norm.utilization_percentage == 80.0
    assert u_norm.category == UtilizationCategory.NORMAL.value
    assert u_norm.remaining_hours == 8.0

    # 3. High (90% - 100%): 38 hours -> 95%
    alloc_high = [{
        "employee_id": "EMP-UTIL",
        "allocated_hours_per_week": 38.0,
        "start_date": start,
        "end_date": end,
        "is_active": True,
        "status": "ACTIVE",
    }]
    u_high = UtilizationService.calculate_utilization(emp, start, end, allocations=alloc_high)
    assert u_high.utilization_percentage == 95.0
    assert u_high.category == UtilizationCategory.HIGH.value
    assert u_high.remaining_hours == 2.0

    # 4. Overallocated (> 100%): 50 hours -> 125%
    alloc_over = [{
        "employee_id": "EMP-UTIL",
        "allocated_hours_per_week": 50.0,
        "start_date": start,
        "end_date": end,
        "is_active": True,
        "status": "ACTIVE",
    }]
    u_over = UtilizationService.calculate_utilization(emp, start, end, allocations=alloc_over)
    assert u_over.utilization_percentage == 125.0
    assert u_over.category == UtilizationCategory.OVERALLOCATED.value
    assert u_over.remaining_hours == -10.0
    assert u_over.is_overallocated is True


def test_utilization_zero_capacity_boundary():
    """Verify utilization boundary when available capacity is 0 hours."""
    # Zero available hours due to 100% PTO
    emp = {
        "id": "EMP-ZERO",
        "business_id": "EMP-000000",
        "employment_status": "ACTIVE",
        "standard_hours_per_week": 40.0,
    }
    start = date(2026, 11, 2)
    end = date(2026, 11, 8)
    leave_full = [{
        "employee_id": "EMP-ZERO",
        "availability_type": "PTO",
        "start_date": start,
        "end_date": end,
        "capacity_percentage": 0.0,
        "available_hours_per_day": 0.0,
    }]

    # Zero available and zero allocated -> ZERO_CAPACITY
    res_zero = UtilizationService.calculate_utilization(emp, start, end, allocations=[], availabilities=leave_full)
    assert res_zero.category == UtilizationCategory.ZERO_CAPACITY.value
    assert res_zero.utilization_percentage == 0.0

    # Zero available but assigned work -> OVERALLOCATED
    alloc_work = [{
        "employee_id": "EMP-ZERO",
        "allocated_hours_per_week": 10.0,
        "start_date": start,
        "end_date": end,
        "is_active": True,
        "status": "ACTIVE",
    }]
    res_assigned = UtilizationService.calculate_utilization(emp, start, end, allocations=alloc_work, availabilities=leave_full)
    assert res_assigned.category == UtilizationCategory.OVERALLOCATED.value
    assert res_assigned.is_overallocated is True


# =============================================================================
# 3. SKILL MATCHING SERVICE TESTS
# =============================================================================

def test_skill_matching_stale_skill_invalidation():
    """
    CRITICAL RULE: A stale skill must NOT count as verified current.
    If last verification exceeds 730 days, effective_certified_proficiency must be 0.
    """
    as_of = date(2026, 10, 22)
    start_d = date(2026, 11, 2)
    end_d = date(2026, 11, 8)

    # 1. Fresh Skill: Verified 100 days ago
    fresh_skill = {
        "id": "ES-01",
        "employee_id": "EMP-01",
        "skill_id": "SKL-001",
        "proficiency_level": 4,
        "is_current": True,
        "verification_status": "ASSESSMENT_CERTIFIED",
        "verified_at": (as_of - timedelta(days=100)).isoformat(),
    }
    match_fresh = SkillMatchingService.evaluate_candidate(
        employee={"id": "EMP-01", "standard_hours_per_week": 40.0, "employment_status": "ACTIVE"},
        employee_skill=fresh_skill,
        required_proficiency=3,
        start_date=start_d,
        end_date=end_d,
        required_hours=40.0,
        as_of_date=as_of,
    )
    assert match_fresh.is_fully_qualified is True
    assert match_fresh.is_stale is False
    assert match_fresh.effective_certified_proficiency == 4
    assert match_fresh.match_score >= 80.0

    # 2. Stale Skill: Verified 800 days ago (> 730 days)
    stale_skill = {
        "id": "ES-02",
        "employee_id": "EMP-02",
        "skill_id": "SKL-001",
        "proficiency_level": 5,
        "is_current": True,
        "verification_status": "ASSESSMENT_CERTIFIED",
        "verified_at": (as_of - timedelta(days=800)).isoformat(),
    }
    match_stale = SkillMatchingService.evaluate_candidate(
        employee={"id": "EMP-02", "standard_hours_per_week": 40.0, "employment_status": "ACTIVE"},
        employee_skill=stale_skill,
        required_proficiency=3,
        start_date=start_d,
        end_date=end_d,
        required_hours=40.0,
        as_of_date=as_of,
    )
    assert match_stale.is_stale is True
    assert match_stale.effective_certified_proficiency == 0
    assert match_stale.is_fully_qualified is False
    assert match_stale.match_score < 50.0


# =============================================================================
# 4. DEMAND AGGREGATION SERVICE TESTS
# =============================================================================

def test_demand_aggregation_by_dimensions():
    """Verify multi-dimensional demand aggregation in memory."""
    demands = [
        {"project_id": "PRJ-01", "role_id": "ROL-01", "primary_skill_id": "SKL-01", "priority": 1, "required_headcount": 2, "required_hours": 80.0},
        {"project_id": "PRJ-01", "role_id": "ROL-02", "primary_skill_id": "SKL-02", "priority": 1, "required_headcount": 1, "required_hours": 40.0},
        {"project_id": "PRJ-02", "role_id": "ROL-01", "primary_skill_id": "SKL-01", "priority": 3, "required_headcount": 3, "required_hours": 120.0},
    ]

    # Aggregate by Project
    by_proj = DemandAggregationService.aggregate_records(demands, dimension="project_id")
    assert len(by_proj) == 2
    p1 = next(item for item in by_proj if item.dimension_id == "PRJ-01")
    assert p1.total_required_headcount == 3
    assert p1.total_required_hours == 120.0
    assert p1.demand_lines_count == 2

    # Aggregate by Role
    by_role = DemandAggregationService.aggregate_records(demands, dimension="role_id")
    assert len(by_role) == 2
    r1 = next(item for item in by_role if item.dimension_id == "ROL-01")
    assert r1.total_required_headcount == 5
    assert r1.total_required_hours == 200.0

    # Aggregate by Priority
    by_prio = DemandAggregationService.aggregate_records(demands, dimension="priority")
    assert len(by_prio) == 2
    prio_1 = next(item for item in by_prio if item.dimension_id == "1")
    assert prio_1.total_required_headcount == 3
    assert prio_1.total_required_hours == 120.0


# =============================================================================
# 5. GAP ANALYSIS SERVICE TESTS
# =============================================================================

def test_gap_analysis_calculation_and_severities():
    """Verify quantitative deficit metrics and dynamic severity thresholds."""
    d_plan = {
        "id": "DEM-001",
        "project_id": "PRJ-01",
        "role_id": "ROL-01",
        "primary_skill_id": "SKL-01",
        "required_headcount": 5,
        "required_hours": 200.0,
        "fulfilled_hours": 0.0,
        "min_proficiency": 3,
        "start_date": date(2026, 11, 2),
        "end_date": date(2026, 11, 30),
        "priority": 1,
    }

    # Case 1: 0 candidates -> 100% unfilled -> CRITICAL
    gap_crit = GapAnalysisService.calculate_demand_gap(
        demand_plan=d_plan,
        qualified_candidates=[],
        project_name="Cloud Migration",
        skill_name="Python",
    )
    assert gap_crit.required_headcount == 5
    assert gap_crit.available_qualified_headcount == 0
    assert gap_crit.headcount_deficit == 5
    assert gap_crit.unfilled_demand_hours == 200.0
    assert gap_crit.fulfillment_percentage == 0.0
    assert gap_crit.severity == GapSeverity.CRITICAL.value

    # Case 2: 3 qualified candidates (40h each = 120h supply) -> capacity gap 80h (40% deficit)
    cand = [
        CandidateMatch(
            employee_id=f"EMP-{i}",
            business_id=f"EMP-00000{i}",
            employee_name=f"Dev {i}",
            role_id="ROL-01",
            department="Engineering",
            skill_id="SKL-01",
            skill_name="Python",
            assessed_proficiency=4,
            effective_certified_proficiency=4,
            required_proficiency=3,
            proficiency_gap=0,
            verification_status="ASSESSMENT_CERTIFIED",
            verified_at="2026-09-01",
            is_stale=False,
            available_hours=40.0,
            allocated_hours=0.0,
            remaining_capacity_hours=40.0,
            is_fully_qualified=True,
            match_score=92.5,
            calculated_at="2026-10-22T00:00:00Z",
            rule_version="1.0.0",
        )
        for i in range(3)
    ]
    gap_high = GapAnalysisService.calculate_demand_gap(
        demand_plan=d_plan,
        qualified_candidates=cand,
        project_name="Cloud Migration",
        skill_name="Python",
    )
    assert gap_high.available_qualified_headcount == 3
    assert gap_high.headcount_deficit == 2
    assert gap_high.qualified_supply_hours == 120.0
    assert gap_high.capacity_gap_hours == 80.0
    assert gap_high.severity == GapSeverity.CRITICAL.value  # Priority 1 demand is critical


# =============================================================================
# 6. RISK SERVICE TESTS (5 MANDATORY RISK CATEGORIES)
# =============================================================================

def test_risk_service_overallocation():
    """Verify detection of overallocation when total active assignments exceed capacity."""
    emp = {"id": "EMP-RISK-1", "business_id": "EMP-000001", "standard_hours_per_week": 40.0}
    # Two assignments of 25h each -> total 50h > 40h -> 10h excess
    allocs = [
        {
            "id": "ALLOC-1",
            "business_id": "ALLOC-000001",
            "employee_id": "EMP-RISK-1",
            "project_id": "PRJ-01",
            "allocated_hours_per_week": 25.0,
            "start_date": date(2026, 11, 2),
            "end_date": date(2026, 11, 30),
            "is_active": True,
            "status": "CONFIRMED",
        },
        {
            "id": "ALLOC-2",
            "business_id": "ALLOC-000002",
            "employee_id": "EMP-RISK-1",
            "project_id": "PRJ-01",
            "allocated_hours_per_week": 25.0,
            "start_date": date(2026, 11, 2),
            "end_date": date(2026, 11, 30),
            "is_active": True,
            "status": "CONFIRMED",
        },
    ]

    risks = RiskService.detect_overallocations(allocations=allocs, employees=[emp])
    assert len(risks) == 1
    r = risks[0]
    assert r.issue_type == IssueType.CAPACITY_OVERLOAD.value
    assert r.severity == IssueSeverity.CRITICAL.value
    assert r.details["excess_hours"] == 10.0
    assert r.details["utilization_pct"] == 125.0


def test_risk_service_stale_skills():
    """Verify detection of skills marked current but verified over 730 days ago."""
    as_of = date(2026, 10, 22)
    skills = [
        {
            "id": "ES-01",
            "business_id": "ES-000001",
            "employee_id": "EMP-01",
            "skill_id": "SKL-PY",
            "proficiency_level": 4,
            "is_current": True,
            "verified_at": as_of - timedelta(days=750),  # 20 days overdue
        },
        {
            "id": "ES-02",
            "business_id": "ES-000002",
            "employee_id": "EMP-01",
            "skill_id": "SKL-AWS",
            "proficiency_level": 3,
            "is_current": True,
            "verified_at": as_of - timedelta(days=200),  # Valid
        },
    ]

    risks = RiskService.detect_stale_skills(skills, as_of_date=as_of)
    assert len(risks) == 1
    r = risks[0]
    assert r.issue_type == IssueType.SKILL_SHORTAGE.value
    assert r.entity_id == "ES-01"
    assert r.details["days_overdue"] == 20


def test_risk_service_duplicate_demand():
    """Verify duplicate deliveries sharing same delivery identity are detected."""
    demands = [
        {
            "id": "DEM-ORIG",
            "business_id": "DEM-000001",
            "project_id": "PRJ-01",
            "role_id": "ROL-01",
            "primary_skill_id": "SKL-01",
            "start_date": date(2026, 11, 2),
            "end_date": date(2026, 11, 30),
        },
        {
            "id": "DEM-DUP",
            "business_id": "DEM-000002",
            "project_id": "PRJ-01",
            "role_id": "ROL-01",
            "primary_skill_id": "SKL-01",
            "start_date": date(2026, 11, 2),
            "end_date": date(2026, 11, 30),
        },
    ]

    risks = RiskService.detect_duplicate_demand(demands)
    assert len(risks) == 1
    r = risks[0]
    assert r.issue_type == IssueType.UNFULFILLED_DEMAND.value
    assert r.entity_id == "DEM-DUP"
    assert r.details["original_demand_id"] == "DEM-ORIG"


def test_risk_service_overlapping_allocations():
    """Verify concurrent cross-project commitments >= 14 days and >= 40% are detected."""
    allocs = [
        {
            "id": "ALLOC-P1",
            "business_id": "ALLOC-000001",
            "employee_id": "EMP-OVERLAP",
            "project_id": "PRJ-ALPHA",
            "allocation_percentage": 50.0,
            "allocated_hours_per_week": 20.0,
            "start_date": date(2026, 11, 2),
            "end_date": date(2026, 11, 30),
            "is_active": True,
            "status": "CONFIRMED",
        },
        {
            "id": "ALLOC-P2",
            "business_id": "ALLOC-000002",
            "employee_id": "EMP-OVERLAP",
            "project_id": "PRJ-BETA",
            "allocation_percentage": 50.0,
            "allocated_hours_per_week": 20.0,
            "start_date": date(2026, 11, 10),
            "end_date": date(2026, 12, 10),
            "is_active": True,
            "status": "CONFIRMED",
        },
    ]

    risks = RiskService.detect_overlapping_allocations(allocs, min_overlap_days=14)
    assert len(risks) == 1
    r = risks[0]
    assert r.issue_type == IssueType.ALLOCATION_CONFLICT.value
    assert r.severity == IssueSeverity.HIGH.value
    assert r.entity_id == "ALLOC-P2"
    assert r.details["overlap_days"] >= 14


def test_risk_service_project_staffing_shortage():
    """Verify detection of critical unfulfilled demands starting within the 60-day horizon."""
    ref_date = date(2026, 10, 22)
    projects = [
        {"id": "PRJ-IMM", "name": "Banking Core Modernization", "status": "ACTIVE"}
    ]
    # Starts in 10 days, requires 4 people (160h), 0 allocated
    demands = [
        {
            "id": "DEM-SHORT",
            "business_id": "DEM-000010",
            "project_id": "PRJ-IMM",
            "start_date": date(2026, 11, 1),
            "required_headcount": 4,
            "required_hours": 160.0,
            "priority": 1,
        }
    ]

    risks = RiskService.detect_project_staffing_shortages(
        projects=projects,
        demand_plans=demands,
        allocations=[],
        as_of_date=ref_date,
    )
    assert len(risks) == 1
    r = risks[0]
    assert r.issue_type == IssueType.UNFULFILLED_DEMAND.value
    assert r.severity == IssueSeverity.CRITICAL.value
    assert r.details["headcount_deficit"] == 4
    assert r.details["days_until_start"] == 10


def test_configurable_thresholds_override():
    """Verify that calculations strictly respect custom PlanningThresholds overrides."""
    custom_thresholds = PlanningThresholds(
        underutilization_threshold=60.0,
        normal_utilization_min=60.0,
        normal_utilization_max=85.0,
        high_utilization_max=95.0,
        overallocation_threshold=95.0,
        stale_skill_validity_days=365,  # 1 year instead of 2 years
    )

    # Utilization classification test with override:
    # 97.5% is High under default thresholds (<100%), but OVERALLOCATED under custom 95% threshold!
    cat_default = UtilizationService.classify_utilization(97.5, available_hours=40.0, thresholds=DEFAULT_THRESHOLDS)
    assert cat_default == UtilizationCategory.HIGH

    cat_custom = UtilizationService.classify_utilization(97.5, available_hours=40.0, thresholds=custom_thresholds)
    assert cat_custom == UtilizationCategory.OVERALLOCATED

    # Skill verified 400 days ago is valid under default 730 days, but STALE under custom 365 days
    skills = [
        {
            "id": "ES-CUSTOM",
            "business_id": "ES-000099",
            "employee_id": "EMP-TEST",
            "skill_id": "SKL-CUSTOM",
            "proficiency_level": 3,
            "is_current": True,
            "verified_at": date(2026, 10, 22) - timedelta(days=400),
        }
    ]
    r_default = RiskService.detect_stale_skills(skills, as_of_date=date(2026, 10, 22), thresholds=DEFAULT_THRESHOLDS)
    assert len(r_default) == 0

    r_custom = RiskService.detect_stale_skills(skills, as_of_date=date(2026, 10, 22), thresholds=custom_thresholds)
    assert len(r_custom) == 1
    assert r_custom[0].details["days_overdue"] == 35
