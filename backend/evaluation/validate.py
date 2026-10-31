"""
WorkforceIQ Data Quality and Validation Engine.

Separates technical data-integrity failures from deliberate business-rule violations:
1. Data Integrity: Primary key uniqueness, foreign key validity, non-nullable fields,
   allowed enums, and date ordering.
2. Business Validation & Anomaly Detection:
   - Capacity Reconciliation (OVERALLOCATION)
   - Skill Certification Freshness (STALE_SKILL)
   - Delivery Identity Deduplication (DUPLICATE_DEMAND)
   - Project Schedule Conflicts (OVERLAPPING_ALLOCATION)
   - Demand Reconciliation and Lifecycle Consistency
"""

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.models.enums import (
    AllocationStatus,
    AvailabilityType,
    DemandStatus,
    EmploymentStatus,
    GapSeverity,
    GapStatus,
    IssueSeverity,
    IssueStatus,
    IssueType,
    ProjectStatus,
    RecommendationStatus,
    RecommendationType,
    ScenarioStatus,
    SkillCategory,
    TrainingStatus,
    VerificationStatus,
)
from backend.generator.config import GeneratorConfig


@dataclass
class DataIntegrityFailure:
    """Represents a structural or relational schema violation."""
    category: str
    entity_type: str
    record_id: str
    field_name: Optional[str]
    error_message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DetectedAnomaly:
    """Represents a detected business-rule exception or operational risk."""
    issue_type: str
    entity_type: str
    entity_id: str
    severity: str
    action: str
    details: Dict[str, Any]
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationReport:
    """Master report summarizing data integrity and detected business anomalies."""
    is_valid: bool
    integrity_failures_count: int
    detected_anomalies_count: int
    integrity_failures: List[DataIntegrityFailure] = field(default_factory=list)
    detected_anomalies: List[DetectedAnomaly] = field(default_factory=list)
    anomalies_by_type: Dict[str, int] = field(default_factory=dict)
    summary_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "integrity_failures_count": self.integrity_failures_count,
            "detected_anomalies_count": self.detected_anomalies_count,
            "anomalies_by_type": self.anomalies_by_type,
            "summary_metrics": self.summary_metrics,
            "integrity_failures": [f.to_dict() for f in self.integrity_failures],
            "detected_anomalies": [a.to_dict() for a in self.detected_anomalies],
        }

    def save(self, filepath: Path) -> Path:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        return filepath


class DataValidator:
    """Comprehensive validator enforcing relational integrity and business rule audits."""

    def __init__(self, config: Optional[GeneratorConfig] = None):
        self.config = config or GeneratorConfig()
        self.as_of_date = self.config.as_of_date
        self.validity_threshold_days = 730  # 2 years

    def validate_dataset(self, dataset: Dict[str, List[Dict[str, Any]]]) -> ValidationReport:
        """Run complete integrity and business validation suite."""
        integrity_failures: List[DataIntegrityFailure] = []
        detected_anomalies: List[DetectedAnomaly] = []

        # 1. Structural & Relational Integrity Checks
        integrity_failures.extend(self._check_primary_key_uniqueness(dataset))
        integrity_failures.extend(self._check_foreign_key_integrity(dataset))
        integrity_failures.extend(self._check_required_fields(dataset))
        integrity_failures.extend(self._check_allowed_enums(dataset))
        integrity_failures.extend(self._check_date_ordering(dataset))
        integrity_failures.extend(self._check_lifecycle_consistency(dataset))

        # 2. Business Anomaly & Rule Violations Detection
        detected_anomalies.extend(self._detect_overallocations(dataset))
        detected_anomalies.extend(self._detect_stale_skills(dataset))
        detected_anomalies.extend(self._detect_duplicate_demand(dataset))
        detected_anomalies.extend(self._detect_overlapping_allocations(dataset))

        # Group anomalies by issue type
        anom_counts: Dict[str, int] = {}
        for a in detected_anomalies:
            anom_counts[a.issue_type] = anom_counts.get(a.issue_type, 0) + 1

        is_valid = len(integrity_failures) == 0

        summary = {
            "total_entities_evaluated": sum(len(records) for records in dataset.values()),
            "total_tables": len(dataset),
            "integrity_checks_status": "PASSED" if is_valid else "FAILED",
            "business_anomalies_detected": len(detected_anomalies),
            "as_of_date": str(self.as_of_date),
        }

        return ValidationReport(
            is_valid=is_valid,
            integrity_failures_count=len(integrity_failures),
            detected_anomalies_count=len(detected_anomalies),
            integrity_failures=integrity_failures,
            detected_anomalies=detected_anomalies,
            anomalies_by_type=anom_counts,
            summary_metrics=summary,
        )

    # -------------------------------------------------------------------------
    # DATA INTEGRITY CHECKS (Must pass 100% on both baseline and anomalous data)
    # -------------------------------------------------------------------------

    def _check_primary_key_uniqueness(self, dataset: Dict[str, List[Dict[str, Any]]]) -> List[DataIntegrityFailure]:
        failures = []
        for table_name, records in dataset.items():
            seen_ids: Set[str] = set()
            for r in records:
                r_id = r.get("id")
                if not r_id:
                    failures.append(
                        DataIntegrityFailure("PRIMARY_KEY", table_name, "UNKNOWN", "id", "Missing primary key")
                    )
                elif r_id in seen_ids:
                    failures.append(
                        DataIntegrityFailure("PRIMARY_KEY", table_name, r_id, "id", f"Duplicate primary key '{r_id}'")
                    )
                else:
                    seen_ids.add(r_id)
        return failures

    def _check_foreign_key_integrity(self, dataset: Dict[str, List[Dict[str, Any]]]) -> List[DataIntegrityFailure]:
        failures = []
        role_ids = {r["id"] for r in dataset.get("roles", [])}
        skill_ids = {s["id"] for s in dataset.get("skills", [])}
        employee_ids = {e["id"] for e in dataset.get("employees", [])}
        project_ids = {p["id"] for p in dataset.get("projects", [])}
        demand_ids = {d["id"] for d in dataset.get("demand_plans", [])}
        gap_ids = {g["id"] for g in dataset.get("gap_analyses", [])}

        # RoleSkill
        for rs in dataset.get("role_skills", []):
            if rs.get("role_id") not in role_ids:
                failures.append(DataIntegrityFailure("FOREIGN_KEY", "RoleSkill", rs["id"], "role_id", "Invalid role_id"))
            if rs.get("skill_id") not in skill_ids:
                failures.append(DataIntegrityFailure("FOREIGN_KEY", "RoleSkill", rs["id"], "skill_id", "Invalid skill_id"))

        # Employee
        for emp in dataset.get("employees", []):
            if emp.get("role_id") not in role_ids:
                failures.append(DataIntegrityFailure("FOREIGN_KEY", "Employee", emp["id"], "role_id", "Invalid role_id"))
            if emp.get("manager_id") and emp["manager_id"] not in employee_ids:
                failures.append(DataIntegrityFailure("FOREIGN_KEY", "Employee", emp["id"], "manager_id", "Invalid manager_id"))

        # EmployeeSkill
        for es in dataset.get("employee_skills", []):
            if es.get("employee_id") not in employee_ids:
                failures.append(DataIntegrityFailure("FOREIGN_KEY", "EmployeeSkill", es["id"], "employee_id", "Invalid employee_id"))
            if es.get("skill_id") not in skill_ids:
                failures.append(DataIntegrityFailure("FOREIGN_KEY", "EmployeeSkill", es["id"], "skill_id", "Invalid skill_id"))

        # Project
        for p in dataset.get("projects", []):
            if p.get("manager_id") and p["manager_id"] not in employee_ids:
                failures.append(DataIntegrityFailure("FOREIGN_KEY", "Project", p["id"], "manager_id", "Invalid manager_id"))

        # DemandPlan
        for d in dataset.get("demand_plans", []):
            if d.get("project_id") not in project_ids:
                failures.append(DataIntegrityFailure("FOREIGN_KEY", "DemandPlan", d["id"], "project_id", "Invalid project_id"))
            if d.get("role_id") not in role_ids:
                failures.append(DataIntegrityFailure("FOREIGN_KEY", "DemandPlan", d["id"], "role_id", "Invalid role_id"))
            if d.get("primary_skill_id") and d["primary_skill_id"] not in skill_ids:
                failures.append(DataIntegrityFailure("FOREIGN_KEY", "DemandPlan", d["id"], "primary_skill_id", "Invalid primary_skill_id"))

        # Allocation
        for a in dataset.get("allocations", []):
            if a.get("employee_id") not in employee_ids:
                failures.append(DataIntegrityFailure("FOREIGN_KEY", "Allocation", a["id"], "employee_id", "Invalid employee_id"))
            if a.get("project_id") not in project_ids:
                failures.append(DataIntegrityFailure("FOREIGN_KEY", "Allocation", a["id"], "project_id", "Invalid project_id"))
            if a.get("demand_plan_id") and a["demand_plan_id"] not in demand_ids:
                failures.append(DataIntegrityFailure("FOREIGN_KEY", "Allocation", a["id"], "demand_plan_id", "Invalid demand_plan_id"))

        return failures

    def _check_required_fields(self, dataset: Dict[str, List[Dict[str, Any]]]) -> List[DataIntegrityFailure]:
        failures = []
        required_by_entity = {
            "employees": ["id", "business_id", "first_name", "last_name", "email", "role_id", "employment_status", "hire_date"],
            "projects": ["id", "business_id", "name", "code", "start_date", "end_date", "status"],
            "skills": ["id", "business_id", "name", "category"],
            "demand_plans": ["id", "business_id", "project_id", "role_id", "start_date", "end_date", "required_headcount"],
            "allocations": ["id", "business_id", "employee_id", "project_id", "start_date", "end_date", "allocation_percentage"],
        }
        for table, req_fields in required_by_entity.items():
            for r in dataset.get(table, []):
                for f_name in req_fields:
                    if r.get(f_name) is None:
                        failures.append(
                            DataIntegrityFailure("REQUIRED_FIELD", table, r.get("id", "UNKNOWN"), f_name, f"Field '{f_name}' cannot be null")
                        )
        return failures

    def _check_allowed_enums(self, dataset: Dict[str, List[Dict[str, Any]]]) -> List[DataIntegrityFailure]:
        failures = []
        valid_emp_status = {e.value for e in EmploymentStatus}
        valid_proj_status = {p.value for p in ProjectStatus}
        valid_skill_cat = {c.value for c in SkillCategory}
        valid_verif_status = {v.value for v in VerificationStatus}
        valid_alloc_status = {a.value for a in AllocationStatus}

        for emp in dataset.get("employees", []):
            if str(emp.get("employment_status")) not in valid_emp_status:
                failures.append(DataIntegrityFailure("ENUM_CONSTRAINT", "Employee", emp["id"], "employment_status", f"Invalid status {emp.get('employment_status')}"))

        for p in dataset.get("projects", []):
            if str(p.get("status")) not in valid_proj_status:
                failures.append(DataIntegrityFailure("ENUM_CONSTRAINT", "Project", p["id"], "status", f"Invalid status {p.get('status')}"))

        for s in dataset.get("skills", []):
            if str(s.get("category")) not in valid_skill_cat:
                failures.append(DataIntegrityFailure("ENUM_CONSTRAINT", "Skill", s["id"], "category", f"Invalid category {s.get('category')}"))

        for es in dataset.get("employee_skills", []):
            if str(es.get("verification_status")) not in valid_verif_status:
                failures.append(DataIntegrityFailure("ENUM_CONSTRAINT", "EmployeeSkill", es["id"], "verification_status", f"Invalid status {es.get('verification_status')}"))

        for a in dataset.get("allocations", []):
            if str(a.get("status")) not in valid_alloc_status:
                failures.append(DataIntegrityFailure("ENUM_CONSTRAINT", "Allocation", a["id"], "status", f"Invalid status {a.get('status')}"))

        return failures

    def _check_date_ordering(self, dataset: Dict[str, List[Dict[str, Any]]]) -> List[DataIntegrityFailure]:
        failures = []
        for p in dataset.get("projects", []):
            if p["start_date"] > p["end_date"]:
                failures.append(DataIntegrityFailure("DATE_ORDERING", "Project", p["id"], "start_date", "start_date must be <= end_date"))

        for d in dataset.get("demand_plans", []):
            if d["start_date"] > d["end_date"]:
                failures.append(DataIntegrityFailure("DATE_ORDERING", "DemandPlan", d["id"], "start_date", "start_date must be <= end_date"))

        for a in dataset.get("allocations", []):
            if a["start_date"] > a["end_date"]:
                failures.append(DataIntegrityFailure("DATE_ORDERING", "Allocation", a["id"], "start_date", "start_date must be <= end_date"))

        for emp in dataset.get("employees", []):
            if emp.get("exit_date") and emp["hire_date"] > emp["exit_date"]:
                failures.append(DataIntegrityFailure("DATE_ORDERING", "Employee", emp["id"], "hire_date", "hire_date must be <= exit_date"))

        return failures

    def _check_lifecycle_consistency(self, dataset: Dict[str, List[Dict[str, Any]]]) -> List[DataIntegrityFailure]:
        failures = []
        for a in dataset.get("allocations", []):
            if not a.get("is_active") and not a.get("superseded_by_id") and a.get("status") not in ["COMPLETED", "CANCELLED", "RELEASED"]:
                failures.append(
                    DataIntegrityFailure("LIFECYCLE", "Allocation", a["id"], "superseded_by_id", "Inactive allocation must reference superseding record or be closed")
                )
        return failures

    # -------------------------------------------------------------------------
    # BUSINESS ANOMALY DETECTIONS
    # -------------------------------------------------------------------------

    def _detect_overallocations(self, dataset: Dict[str, List[Dict[str, Any]]]) -> List[DetectedAnomaly]:
        """
        Detect allocations that cause an employee's total active hours to exceed capacity.
        Identifies the specific breaching allocation and calculates exact excess hours.
        """
        detected = []
        emp_capacity = {e["id"]: float(e.get("standard_hours_per_week", 40.0)) for e in dataset.get("employees", [])}

        allocs_by_emp: Dict[str, List[Dict[str, Any]]] = {}
        for a in dataset.get("allocations", []):
            if a.get("is_active"):
                allocs_by_emp.setdefault(a["employee_id"], []).append(a)

        for emp_id, emp_allocs in allocs_by_emp.items():
            cap = emp_capacity.get(emp_id, 40.0)
            sorted_allocs = sorted(emp_allocs, key=lambda x: (x["start_date"], str(x.get("created_at", ""))))

            for idx, alloc in enumerate(sorted_allocs):
                a_start = alloc["start_date"]
                a_end = alloc["end_date"]
                a_hours = float(alloc["allocated_hours_per_week"])

                # Prior overlapping hours established by allocations ordered before this one
                prior_overlapping_hours = sum(
                    float(other["allocated_hours_per_week"])
                    for other in sorted_allocs[:idx]
                    if not (a_end < other["start_date"] or a_start > other["end_date"])
                )

                total_hours = prior_overlapping_hours + a_hours

                # Flag the allocation whose addition breached available capacity
                if total_hours > cap and prior_overlapping_hours <= cap:
                    exact_excess = round(total_hours - cap, 2)
                    detected.append(
                        DetectedAnomaly(
                            issue_type="OVERALLOCATION",
                            entity_type="Allocation",
                            entity_id=alloc["id"],
                            severity="CRITICAL",
                            action="REDUCE_ALLOCATION_HOURS",
                            details={
                                "employee_id": emp_id,
                                "allocation_id": alloc["id"],
                                "business_id": alloc["business_id"],
                                "capacity_hours": cap,
                                "total_allocated_hours": round(total_hours, 2),
                                "excess_hours": exact_excess,
                                "window_start": str(a_start),
                                "window_end": str(a_end),
                            },
                        )
                    )
        return detected

    def _detect_stale_skills(self, dataset: Dict[str, List[Dict[str, Any]]]) -> List[DetectedAnomaly]:
        """
        Detect employee skill records whose verification date exceeds the 730-day validity
        period while remaining marked as current (is_current = True).
        """
        detected = []
        for sk in dataset.get("employee_skills", []):
            if not sk.get("is_current"):
                continue

            verified_at = sk.get("verified_at")
            if not verified_at:
                continue

            if isinstance(verified_at, str):
                v_date = datetime.fromisoformat(verified_at).date()
            elif isinstance(verified_at, datetime):
                v_date = verified_at.date()
            elif isinstance(verified_at, date):
                v_date = verified_at
            else:
                continue

            elapsed_days = (self.as_of_date - v_date).days
            if elapsed_days > self.validity_threshold_days:
                days_overdue = elapsed_days - self.validity_threshold_days
                detected.append(
                    DetectedAnomaly(
                        issue_type="STALE_SKILL",
                        entity_type="EmployeeSkill",
                        entity_id=sk["id"],
                        severity="HIGH",
                        action="REVERIFY_EMPLOYEE_SKILL",
                        details={
                            "employee_id": sk["employee_id"],
                            "skill_id": sk["skill_id"],
                            "business_id": sk["business_id"],
                            "verified_at": v_date.isoformat(),
                            "as_of_date": str(self.as_of_date),
                            "elapsed_days": elapsed_days,
                            "validity_threshold_days": self.validity_threshold_days,
                            "days_overdue": days_overdue,
                        },
                    )
                )
        return detected

    def _detect_duplicate_demand(self, dataset: Dict[str, List[Dict[str, Any]]]) -> List[DetectedAnomaly]:
        """
        Detect duplicate deliveries of existing demand plans using core delivery identity:
        (project_id, role_id, start_date, end_date, primary_skill_id).
        Does NOT misclassify legitimate separate roles or separate week demand.
        """
        detected = []
        delivery_groups: Dict[Tuple, List[Dict[str, Any]]] = {}

        for d in dataset.get("demand_plans", []):
            # Signature representing an identical requirement delivery
            sig = (
                d["project_id"],
                d["role_id"],
                str(d["start_date"]),
                str(d["end_date"]),
                d.get("primary_skill_id"),
            )
            delivery_groups.setdefault(sig, []).append(d)

        for sig, items in delivery_groups.items():
            if len(items) > 1:
                # The first item is original; subsequent items are duplicates
                orig = items[0]
                for dup in items[1:]:
                    detected.append(
                        DetectedAnomaly(
                            issue_type="DUPLICATE_DEMAND",
                            entity_type="DemandPlan",
                            entity_id=dup["id"],
                            severity="MEDIUM",
                            action="DE_DUPLICATE_DEMAND_LINE",
                            details={
                                "original_demand_id": orig["id"],
                                "duplicate_demand_id": dup["id"],
                                "original_business_id": orig["business_id"],
                                "duplicate_business_id": dup["business_id"],
                                "project_id": sig[0],
                                "role_id": sig[1],
                                "start_date": sig[2],
                                "end_date": sig[3],
                                "delivery_identity": f"{sig[0]}:{sig[1]}:{sig[2]}:{sig[3]}",
                            },
                        )
                    )
        return detected

    def _detect_overlapping_allocations(self, dataset: Dict[str, List[Dict[str, Any]]]) -> List[DetectedAnomaly]:
        """
        Detect employees assigned to concurrent conflicting project allocations.
        Calculates exact overlap start, end, days, and committed hours.
        """
        detected = []
        allocs_by_emp: Dict[str, List[Dict[str, Any]]] = {}
        for a in dataset.get("allocations", []):
            if a.get("is_active"):
                allocs_by_emp.setdefault(a["employee_id"], []).append(a)

        for emp_id, emp_allocs in allocs_by_emp.items():
            if len(emp_allocs) < 2:
                continue

            sorted_allocs = sorted(emp_allocs, key=lambda x: (x["start_date"], str(x.get("created_at", ""))))
            seen_conflict_ids = set()

            # Check pairwise overlaps across distinct projects
            for i in range(len(sorted_allocs)):
                for j in range(i + 1, len(sorted_allocs)):
                    a1 = sorted_allocs[i]
                    a2 = sorted_allocs[j]

                    if a1["project_id"] == a2["project_id"] or a2["id"] in seen_conflict_ids:
                        continue

                    # Date overlap
                    o_start = max(a1["start_date"], a2["start_date"])
                    o_end = min(a1["end_date"], a2["end_date"])

                    if o_start <= o_end:
                        overlap_days = (o_end - o_start).days + 1
                        # If both are dedicated (>=80%) or combined pct exceeds 100%
                        pct1 = float(a1["allocation_percentage"])
                        pct2 = float(a2["allocation_percentage"])

                        if overlap_days >= 14 and pct1 >= 40.0 and pct2 >= 40.0:
                            combined_hours = float(a1["allocated_hours_per_week"]) + float(a2["allocated_hours_per_week"])
                            overlap_hours = round((overlap_days / 7.0) * float(a2["allocated_hours_per_week"]), 2)
                            seen_conflict_ids.add(a2["id"])

                            # Flag the secondary/conflicting allocation a2
                            detected.append(
                                DetectedAnomaly(
                                    issue_type="OVERLAPPING_ALLOCATION",
                                    entity_type="Allocation",
                                    entity_id=a2["id"],
                                    severity="HIGH",
                                    action="RESOLVE_SCHEDULE_OVERLAP",
                                    details={
                                        "employee_id": emp_id,
                                        "primary_allocation_id": a1["id"],
                                        "conflicting_allocation_id": a2["id"],
                                        "primary_business_id": a1["business_id"],
                                        "conflicting_business_id": a2["business_id"],
                                        "overlap_start": str(o_start),
                                        "overlap_end": str(o_end),
                                        "overlap_days": overlap_days,
                                        "overlap_hours": overlap_hours,
                                        "combined_weekly_hours": round(combined_hours, 2),
                                    },
                                )
                            )
        return detected
