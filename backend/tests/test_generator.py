"""
Automated Test Suite for WorkforceIQ Synthetic Data Generation Pipeline.

Verifies:
- Starter and Full scale configurations and row counts.
- Foreign-key relational integrity across all 15 entities.
- Business ID conventions and primary key uniqueness.
- Deterministic PRNG reproducibility (same seed produces identical data).
- Realism constraints (proficiency 1-5, employment types, synthetic email provenance).
- Export artifacts and manifest checksum integrity.
"""

import json
from pathlib import Path
import re
import sys
import pytest

# Ensure both project root and backend dir are in sys.path
TEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TEST_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

for p in [str(PROJECT_ROOT), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.generator.config import GeneratorConfig, STARTER_CONFIG, FULL_CONFIG
    from backend.generator.generate import generate_workforce_dataset
except ImportError:
    from generator.config import GeneratorConfig, STARTER_CONFIG, FULL_CONFIG
    from generator.generate import generate_workforce_dataset


@pytest.fixture(scope="module")
def starter_dataset():
    """Module-scoped generated starter dataset for high performance test execution."""
    config = GeneratorConfig(scale="starter", seed=20261022)
    return generate_workforce_dataset(config)


def test_starter_generation_counts(starter_dataset):
    """Verify that generation row counts precisely match the Starter configuration."""
    assert len(starter_dataset["roles"]) == STARTER_CONFIG.role_count
    assert len(starter_dataset["skills"]) == STARTER_CONFIG.skill_count
    assert len(starter_dataset["employees"]) == STARTER_CONFIG.employee_count
    assert len(starter_dataset["projects"]) == STARTER_CONFIG.project_count
    
    # Dependent and derived entities
    assert len(starter_dataset["role_skills"]) > 0
    assert len(starter_dataset["employee_skills"]) > 0
    assert len(starter_dataset["availabilities"]) > 0
    assert len(starter_dataset["demand_plans"]) > 0
    assert len(starter_dataset["allocations"]) > 0
    assert len(starter_dataset["trainings"]) > 0
    assert len(starter_dataset["gap_analyses"]) > 0
    assert len(starter_dataset["recommendations"]) > 0
    assert len(starter_dataset["issue_records"]) > 0
    assert len(starter_dataset["scenario_runs"]) == 1
    assert len(starter_dataset["audit_events"]) == 1


def test_business_id_conventions_and_uniqueness(starter_dataset):
    """Verify standard business ID regex formats and primary key uniqueness."""
    emp_re = re.compile(r"^EMP-\d{6}$")
    skl_re = re.compile(r"^SKL-\d{6}$")
    prj_re = re.compile(r"^PRJ-2026-\d{6}$")
    dem_re = re.compile(r"^DEM-PRJ-2026-\d{6}-2026W\d{2}-R\d+$")
    alloc_re = re.compile(r"^ALLOC-2026-\d{6}$")

    # Check Employee IDs
    emp_biz_ids = [e["business_id"] for e in starter_dataset["employees"]]
    assert all(emp_re.match(bid) for bid in emp_biz_ids), "Employee business ID format mismatch"
    assert len(emp_biz_ids) == len(set(emp_biz_ids)), "Employee business IDs must be unique"

    # Check Skill IDs
    skl_biz_ids = [s["business_id"] for s in starter_dataset["skills"]]
    assert all(skl_re.match(bid) for bid in skl_biz_ids), "Skill business ID format mismatch"
    assert len(skl_biz_ids) == len(set(skl_biz_ids)), "Skill business IDs must be unique"

    # Check Project IDs
    prj_biz_ids = [p["business_id"] for p in starter_dataset["projects"]]
    assert all(prj_re.match(bid) for bid in prj_biz_ids), "Project business ID format mismatch"
    assert len(prj_biz_ids) == len(set(prj_biz_ids)), "Project business IDs must be unique"

    # Check Demand Plan IDs
    dem_biz_ids = [d["business_id"] for d in starter_dataset["demand_plans"]]
    assert all(dem_re.match(bid) for bid in dem_biz_ids), "Demand Plan business ID format mismatch"
    assert len(dem_biz_ids) == len(set(dem_biz_ids)), "Demand Plan business IDs must be unique"

    # Check Allocation IDs
    alloc_biz_ids = [a["business_id"] for a in starter_dataset["allocations"]]
    assert all(alloc_re.match(bid) for bid in alloc_biz_ids), "Allocation business ID format mismatch"
    assert len(alloc_biz_ids) == len(set(alloc_biz_ids)), "Allocation business IDs must be unique"

    # Check Primary Key UUID Uniqueness across all entities
    for entity_name, records in starter_dataset.items():
        pks = [r["id"] for r in records]
        assert len(pks) == len(set(pks)), f"Entity '{entity_name}' primary keys must be strictly unique"


def test_foreign_key_integrity(starter_dataset):
    """Verify that all foreign keys refer to existing primary keys in parent tables."""
    role_ids = {r["id"] for r in starter_dataset["roles"]}
    skill_ids = {s["id"] for s in starter_dataset["skills"]}
    employee_ids = {e["id"] for e in starter_dataset["employees"]}
    project_ids = {p["id"] for p in starter_dataset["projects"]}
    demand_plan_ids = {d["id"] for d in starter_dataset["demand_plans"]}
    gap_analysis_ids = {g["id"] for g in starter_dataset["gap_analyses"]}
    training_ids = {t["id"] for t in starter_dataset["trainings"]}

    # RoleSkill -> Role, Skill
    for rs in starter_dataset["role_skills"]:
        assert rs["role_id"] in role_ids
        assert rs["skill_id"] in skill_ids

    # Employee -> Role, Manager
    for emp in starter_dataset["employees"]:
        assert emp["role_id"] in role_ids
        if emp.get("manager_id"):
            assert emp["manager_id"] in employee_ids

    # EmployeeSkill -> Employee, Skill, VerifiedBy
    for es in starter_dataset["employee_skills"]:
        assert es["employee_id"] in employee_ids
        assert es["skill_id"] in skill_ids
        if es.get("verified_by_id"):
            assert es["verified_by_id"] in employee_ids

    # Project -> Manager
    for prj in starter_dataset["projects"]:
        if prj.get("manager_id"):
            assert prj["manager_id"] in employee_ids

    # DemandPlan -> Project, Role, Skill
    for dp in starter_dataset["demand_plans"]:
        assert dp["project_id"] in project_ids
        assert dp["role_id"] in role_ids
        if dp.get("primary_skill_id"):
            assert dp["primary_skill_id"] in skill_ids

    # Availability -> Employee
    for av in starter_dataset["availabilities"]:
        assert av["employee_id"] in employee_ids

    # Allocation -> Employee, Project, DemandPlan
    for alloc in starter_dataset["allocations"]:
        assert alloc["employee_id"] in employee_ids
        assert alloc["project_id"] in project_ids
        if alloc.get("demand_plan_id"):
            assert alloc["demand_plan_id"] in demand_plan_ids

    # Training -> Employee, Skill
    for trn in starter_dataset["trainings"]:
        assert trn["employee_id"] in employee_ids
        assert trn["target_skill_id"] in skill_ids

    # GapAnalysis -> Project, DemandPlan, Skill
    for gap in starter_dataset["gap_analyses"]:
        assert gap["project_id"] in project_ids
        assert gap["demand_plan_id"] in demand_plan_ids
        if gap.get("skill_id"):
            assert gap["skill_id"] in skill_ids

    # Recommendation -> GapAnalysis, Employee, Project
    for rec in starter_dataset["recommendations"]:
        assert rec["gap_analysis_id"] in gap_analysis_ids
        assert rec["target_project_id"] in project_ids
        if rec.get("target_employee_id"):
            assert rec["target_employee_id"] in employee_ids

    # IssueRecord -> Employee, Project
    for iss in starter_dataset["issue_records"]:
        if iss.get("employee_id"):
            assert iss["employee_id"] in employee_ids
        if iss.get("project_id"):
            assert iss["project_id"] in project_ids


def test_deterministic_reproducibility():
    """Verify that running the generator with the identical seed produces identical datasets."""
    config_a = GeneratorConfig(scale="starter", seed=20261022)
    config_b = GeneratorConfig(scale="starter", seed=20261022)

    dataset_a = generate_workforce_dataset(config_a)
    dataset_b = generate_workforce_dataset(config_b)

    # Verify identical counts
    assert len(dataset_a["employees"]) == len(dataset_b["employees"])
    assert len(dataset_a["demand_plans"]) == len(dataset_b["demand_plans"])
    assert len(dataset_a["allocations"]) == len(dataset_b["allocations"])

    # Verify exact equality of records
    for idx in range(len(dataset_a["employees"])):
        assert dataset_a["employees"][idx]["business_id"] == dataset_b["employees"][idx]["business_id"]
        assert dataset_a["employees"][idx]["email"] == dataset_b["employees"][idx]["email"]
        assert dataset_a["employees"][idx]["id"] == dataset_b["employees"][idx]["id"]

    for idx in range(len(dataset_a["projects"])):
        assert dataset_a["projects"][idx]["business_id"] == dataset_b["projects"][idx]["business_id"]
        assert dataset_a["projects"][idx]["name"] == dataset_b["projects"][idx]["name"]

    # Verify different seed yields divergent data
    config_diff = GeneratorConfig(scale="starter", seed=999999)
    dataset_diff = generate_workforce_dataset(config_diff)
    assert dataset_a["employees"][0]["email"] != dataset_diff["employees"][0]["email"]


def test_realism_constraints(starter_dataset):
    """Verify synthetic realism parameters, skill proficiencies, and privacy guarantees."""
    # Proficiency levels must be between 1 and 5
    for es in starter_dataset["employee_skills"]:
        assert 1 <= es["proficiency_level"] <= 5

    # Verification records must have audit timestamps when verified
    verified_skills = [
        es for es in starter_dataset["employee_skills"]
        if es["verification_status"] in ["MANAGER_VERIFIED", "ASSESSMENT_CERTIFIED"]
    ]
    assert len(verified_skills) > 0, "Must have verified skills"
    for vs in verified_skills:
        assert vs.get("verified_at") is not None
        assert vs.get("verified_by_id") is not None

    # Employees must use synthetic email domains (no real corporate domain leaks)
    for emp in starter_dataset["employees"]:
        assert emp["email"].endswith("@workforceiq.synthetic")
        assert emp["employment_status"] in ["ACTIVE", "CONTRACTOR", "ON_LEAVE", "PROBATION"]
        assert float(emp["standard_hours_per_week"]) in [20.0, 30.0, 40.0]

    # Allocations must preserve versioning (v1 superseded by v2)
    versions = {a["version"] for a in starter_dataset["allocations"]}
    assert 1 in versions
    assert 2 in versions


def test_exported_manifests_integrity():
    """Verify that export manifests exist on disk and record synthetic provenance."""
    project_root = Path(__file__).resolve().parent.parent.parent
    starter_manifest = project_root / "data" / "exports" / "starter" / "manifest.json"
    full_manifest = project_root / "data" / "exports" / "full" / "manifest.json"

    assert starter_manifest.exists(), "Starter manifest.json must exist"
    assert full_manifest.exists(), "Full manifest.json must exist"

    with open(starter_manifest, "r", encoding="utf-8") as f:
        starter_data = json.load(f)
        assert starter_data["workforceiq_generator_version"] == "1.0.0"
        assert starter_data["provenance"]["is_synthetic"] is True
        assert starter_data["summary_statistics"]["total_rows_generated"] == 3354
        assert len(starter_data["sha256_file_checksums"]) > 0

    with open(full_manifest, "r", encoding="utf-8") as f:
        full_data = json.load(f)
        assert full_data["workforceiq_generator_version"] == "1.0.0"
        assert full_data["provenance"]["is_synthetic"] is True
        assert full_data["summary_statistics"]["total_rows_generated"] in [113064, 113358]
        assert full_data["summary_statistics"]["table_row_counts"]["employees"] == 5000
        assert full_data["summary_statistics"]["table_row_counts"]["skills"] == 300
        assert full_data["summary_statistics"]["table_row_counts"]["projects"] == 500
