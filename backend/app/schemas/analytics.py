"""
Workforce Analytics Request and Response Pydantic Schemas.
Wraps CapacityService, UtilizationService, and GapAnalysisService outputs.
"""

from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CapacityCalculationRequest(BaseModel):
    employee_id: str
    start_date: date
    end_date: date


class CapacityResponse(BaseModel):
    employee_id: str
    business_id: str
    start_date: str
    end_date: str
    contract_hours_per_week: float
    base_period_hours: float
    leave_hours_deducted: float
    lifecycle_status: str
    is_active_in_period: bool
    net_available_hours: float
    calculated_at: str
    rule_version: str


class UtilizationCalculationRequest(BaseModel):
    employee_id: str
    start_date: date
    end_date: date


class UtilizationResponse(BaseModel):
    employee_id: str
    business_id: str
    start_date: str
    end_date: str
    available_hours: float
    allocated_hours: float
    remaining_hours: float
    utilization_percentage: float
    category: str
    is_overallocated: bool
    allocation_count: int
    calculated_at: str
    rule_version: str


class DepartmentUtilizationResponse(BaseModel):
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


class GapAnalysisResponse(BaseModel):
    demand_plan_id: str
    project_id: str
    project_name: str
    skill_id: str
    skill_name: str
    role_id: str
    start_date: str
    end_date: str
    required_proficiency: int
    required_headcount: int
    available_qualified_headcount: int
    headcount_deficit: int
    required_demand_hours: float
    qualified_supply_hours: float
    unfilled_demand_hours: float
    capacity_gap_hours: float
    fulfillment_percentage: float
    severity: str
    status: str
    calculated_at: str
    rule_version: str
