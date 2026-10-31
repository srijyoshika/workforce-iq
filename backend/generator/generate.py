"""
Master Synthetic Workforce Data Generator CLI.
Executes the parameterized generation pipeline across roles, skills, employees,
projects, demand plans, availability, allocations, and derived intelligence.
"""

import argparse
import asyncio
from datetime import date, datetime
import os
from pathlib import Path
import random
import sys
import time
from typing import Any, Dict, List
from faker import Faker
import numpy as np

# Ensure project root is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

for p in [str(PROJECT_ROOT), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.generator.config import GeneratorConfig
from backend.generator.id_generator import generate_uuid, role_id
from backend.generator.master_data import get_roles
from backend.generator.employee_generator import generate_employees
from backend.generator.skill_generator import (
    generate_employee_skills,
    generate_role_skills,
    generate_skills,
)
from backend.generator.project_generator import generate_projects
from backend.generator.demand_generator import generate_demand_plans
from backend.generator.availability_generator import generate_availabilities
from backend.generator.allocation_generator import generate_allocations
from backend.generator.training_generator import generate_trainings
from backend.generator.derived_generator import generate_derived_intelligence
from backend.generator.export import (
    export_to_csv,
    export_to_json,
    export_to_sql,
    seed_dataset_to_database,
    write_manifest,
)


def seed_prng(seed: int) -> tuple[Faker, np.random.Generator]:
    """Deterministically seed Python random, NumPy, and Faker."""
    random.seed(seed)
    np_rng = np.random.default_rng(seed)
    faker = Faker()
    faker.seed_instance(seed)
    Faker.seed(seed)
    return faker, np_rng


def generate_workforce_dataset(config: GeneratorConfig) -> Dict[str, List[Dict[str, Any]]]:
    """
    Execute the deterministic workforce generation pipeline in strict chronological order.
    """
    faker, rng = seed_prng(config.seed)
    print(f"\n[1/12] Initializing PRNG with seed {config.seed} ({config.scale.upper()} Scale)...")

    # 1. Role Master Data
    print(f"[2/12] Generating Roles ({config.scale_config.role_count} roles)...")
    raw_roles = get_roles(config.scale_config.role_count)
    roles: List[Dict[str, Any]] = []
    for seq, r in enumerate(raw_roles, start=1):
        biz_id = role_id(seq)
        pk_id = generate_uuid("Role", biz_id)
        roles.append({
            "id": pk_id,
            "business_id": biz_id,
            "title": r["title"],
            "code": r["code"],
            "department": r["dept"],
            "description": r["desc"],
            "standard_hourly_rate": r["rate"],
            "is_active": True,
            "created_at": datetime(2025, 1, 1, 0, 0, 0),
            "updated_at": datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 0, 0, 0),
        })

    # 2. Skill Taxonomy
    print(f"[3/12] Generating Skill Taxonomy ({config.scale_config.skill_count} skills)...")
    skills = generate_skills(config)

    # 3. Role-Skill Requirements Bridge
    print(f"[4/12] Mapping Role-Skill competency requirements...")
    role_skills = generate_role_skills(config, roles, skills, rng)

    # 4. Employee Master Records
    print(f"[5/12] Generating Employees ({config.scale_config.employee_count} records)...")
    employees = generate_employees(config, roles, faker, rng)

    # 5. Employee Skill Profiles (with historical verification progression)
    print(f"[6/12] Generating Employee Skill Profiles & Verification History...")
    employee_skills = generate_employee_skills(config, employees, skills, role_skills, rng)

    # 6. Project Master Records
    print(f"[7/12] Generating Projects ({config.scale_config.project_count} projects)...")
    projects = generate_projects(config, employees, rng)

    # 7. 12 Months Weekly Time-Phased Demand Plans
    print(f"[8/12] Generating 12 Months of Time-Phased Weekly Demand Plans...")
    demand_plans = generate_demand_plans(config, projects, roles, skills, role_skills, rng)

    # 8 & 9. Employee Availability & Leave Records
    print(f"[9/12] Generating Availability Schedules, Holidays & PTO Leave...")
    availabilities = generate_availabilities(config, employees, rng)

    # 10. Staffing Allocations
    print(f"[10/12] Generating Staffing Allocations & Preserving Versioning History...")
    allocations = generate_allocations(config, employees, projects, demand_plans, rng)

    # 11. Training & Upskilling Records
    print(f"[11/12] Generating Employee Upskilling & Training Records...")
    trainings = generate_trainings(config, employees, skills, rng)

    # 12. Calculate Derived Data (Gap Analysis, Recommendations, Issues, Scenario, Audit)
    print(f"[12/12] Calculating Derived Intelligence & Operational Telemetry...")
    derived = generate_derived_intelligence(config, employees, projects, demand_plans, allocations, skills, rng)

    # Combine into unified dataset
    dataset: Dict[str, List[Dict[str, Any]]] = {
        "roles": roles,
        "skills": skills,
        "role_skills": role_skills,
        "employees": employees,
        "employee_skills": employee_skills,
        "availabilities": availabilities,
        "projects": projects,
        "demand_plans": demand_plans,
        "allocations": allocations,
        "trainings": trainings,
        "gap_analyses": derived["gap_analyses"],
        "recommendations": derived["recommendations"],
        "issue_records": derived["issue_records"],
        "scenario_runs": derived["scenario_runs"],
        "audit_events": derived["audit_events"],
    }

    return dataset


async def run_pipeline(
    scale: str = "starter",
    seed: int = 20261022,
    as_of_date_str: str = "2026-10-22",
    output_dir_str: str = "data/exports",
    export_format: str = "all",
    seed_db: bool = False,
):
    """Orchestrate synthetic data generation, export, validation, and database seeding."""
    start_time = time.time()
    as_of = date.fromisoformat(as_of_date_str)
    out_dir = Path(output_dir_str) / scale.lower()
    out_dir.mkdir(parents=True, exist_ok=True)

    config = GeneratorConfig(
        scale=scale,
        seed=seed,
        as_of_date=as_of,
        output_dir=out_dir,
    )

    print("=" * 70)
    print(f" WorkforceIQ Synthetic Workforce Data Generator v1.0.0 ")
    print(f" Scale: {config.scale.upper()} | Seed: {config.seed} | As-Of Date: {config.as_of_date}")
    print(f" Targets: {config.scale_config.employee_count} Emp, {config.scale_config.skill_count} Skl, {config.scale_config.project_count} Prj, {config.scale_config.role_count} Roles")
    print("=" * 70)

    # Generate complete dataset
    dataset = generate_workforce_dataset(config)

    # Exporting
    print("\n[Exporting Datasets]...")
    all_checksums: Dict[str, str] = {}

    if export_format in ["all", "csv"]:
        print(f"Writing CSV tables to: {out_dir / 'csv'}")
        csv_hashes = export_to_csv(dataset, out_dir)
        all_checksums.update(csv_hashes)

    if export_format in ["all", "json"]:
        print(f"Writing JSON files to: {out_dir / 'json'}")
        json_hashes = export_to_json(dataset, out_dir)
        all_checksums.update(json_hashes)

    if export_format in ["all", "sql"]:
        print(f"Writing SQL seed script to: {out_dir / 'sql'}")
        sql_hashes = export_to_sql(dataset, out_dir)
        all_checksums.update(sql_hashes)

    # Database seeding if requested
    if seed_db:
        print("\n[Database Seeding] Seeding dataset directly into database...")
        from app.database import init_db_engine, close_db_engine
        engine, dialect = await init_db_engine()
        inserted_count = await seed_dataset_to_database(engine, dataset)
        await close_db_engine()
        print(f"Successfully seeded {inserted_count} rows into {dialect.upper()} database.")

    duration = time.time() - start_time
    manifest_path = write_manifest(config, dataset, all_checksums, out_dir, duration)

    # Print Summary Report
    print("\n" + "=" * 70)
    print(" GENERATION & VALIDATION SUMMARY REPORT")
    print("=" * 70)
    print(f"Status               : SUCCESS (Completed in {duration:.2f}s)")
    print(f"Scale                : {config.scale.upper()}")
    print(f"Random Seed          : {config.seed} (Deterministic)")
    print(f"Output Directory     : {out_dir.resolve()}")
    print(f"Provenance Manifest  : {manifest_path.resolve()}")
    print("\nEntity Row Counts:")
    print("-" * 45)
    total_rows = 0
    for table_name, rows in dataset.items():
        count = len(rows)
        total_rows += count
        print(f"  • {table_name:<20} : {count:>7,d} rows")
    print("-" * 45)
    print(f"  TOTAL RECORDS      : {total_rows:>7,d} rows")
    print("=" * 70)


def main():
    """CLI Entry point."""
    parser = argparse.ArgumentParser(description="WorkforceIQ Synthetic Data Generator")
    parser.add_argument("--scale", choices=["starter", "full"], default="starter", help="Data volume scale (starter | full)")
    parser.add_argument("--seed", type=int, default=20261022, help="Deterministic random seed (default: 20261022)")
    parser.add_argument("--as-of-date", default="2026-10-22", help="Planning as-of reference date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", default="data/exports", help="Base directory for exports")
    parser.add_argument("--format", choices=["all", "csv", "json", "sql"], default="all", help="Export formats")
    parser.add_argument("--seed-db", action="store_true", help="Insert generated dataset directly into database")

    args = parser.parse_args()

    asyncio.run(run_pipeline(
        scale=args.scale,
        seed=args.seed,
        as_of_date_str=args.as_of_date,
        output_dir_str=args.output_dir,
        export_format=args.format,
        seed_db=args.seed_db,
    ))


if __name__ == "__main__":
    main()

