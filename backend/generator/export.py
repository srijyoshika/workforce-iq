"""
Data Export and Manifest Pipeline.
Exports synthetic datasets to CSV, JSON, and SQL Seed Scripts with deterministic ordering,
SHA256 integrity checksums, and synthetic provenance manifests.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from backend.generator.config import GeneratorConfig


class CustomJSONEncoder(json.JSONEncoder):
    """JSON Encoder handling Decimal, date, and datetime objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def serialize_records_for_dataframe(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format dates and complex structures for clean tabular export."""
    clean_records = []
    for r in records:
        row = {}
        for k, v in r.items():
            if isinstance(v, Decimal):
                row[k] = float(v)
            elif isinstance(v, datetime):
                row[k] = v.isoformat()
            elif isinstance(v, date):
                row[k] = v.isoformat()
            elif isinstance(v, dict):
                row[k] = json.dumps(v, cls=CustomJSONEncoder)
            else:
                row[k] = v
        clean_records.append(row)
    return clean_records


def calculate_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def export_to_csv(dataset: Dict[str, List[Dict[str, Any]]], output_dir: Path) -> Dict[str, str]:
    """Export every table to deterministically sorted CSV files."""
    csv_dir = output_dir / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)
    file_hashes: Dict[str, str] = {}

    for table_name, records in dataset.items():
        if not records:
            continue
        # Deterministic ordering by business_id or id
        sorted_records = sorted(records, key=lambda x: x.get("business_id") or x.get("id"))
        clean_rows = serialize_records_for_dataframe(sorted_records)
        df = pd.DataFrame(clean_rows)

        csv_path = csv_dir / f"{table_name}.csv"
        # Export with consistent UTF-8 encoding and float formatting
        df.to_csv(csv_path, index=False, encoding="utf-8")
        file_hashes[f"csv/{table_name}.csv"] = calculate_sha256(csv_path)

    return file_hashes


def export_to_json(dataset: Dict[str, List[Dict[str, Any]]], output_dir: Path) -> Dict[str, str]:
    """Export dataset to JSON format."""
    json_dir = output_dir / "json"
    json_dir.mkdir(parents=True, exist_ok=True)
    file_hashes: Dict[str, str] = {}

    # 1. Export unified JSON dataset
    unified_data = {}
    for table_name, records in dataset.items():
        sorted_records = sorted(records, key=lambda x: x.get("business_id") or x.get("id"))
        unified_data[table_name] = sorted_records

    unified_path = json_dir / "workforce_dataset.json"
    with open(unified_path, "w", encoding="utf-8") as f:
        json.dump(unified_data, f, indent=2, cls=CustomJSONEncoder)
    file_hashes["json/workforce_dataset.json"] = calculate_sha256(unified_path)

    # 2. Export individual table JSONs
    for table_name, records in dataset.items():
        sorted_records = sorted(records, key=lambda x: x.get("business_id") or x.get("id"))
        table_path = json_dir / f"{table_name}.json"
        with open(table_path, "w", encoding="utf-8") as f:
            json.dump(sorted_records, f, indent=2, cls=CustomJSONEncoder)
        file_hashes[f"json/{table_name}.json"] = calculate_sha256(table_path)

    return file_hashes


def export_to_sql(dataset: Dict[str, List[Dict[str, Any]]], output_dir: Path) -> Dict[str, str]:
    """Generate transactional SQL seed script."""
    sql_dir = output_dir / "sql"
    sql_dir.mkdir(parents=True, exist_ok=True)
    sql_path = sql_dir / "seed_data.sql"

    # Strict insertion order respecting foreign key dependencies
    insertion_order = [
        "roles",
        "skills",
        "role_skills",
        "employees",
        "employee_skills",
        "availabilities",
        "projects",
        "demand_plans",
        "allocations",
        "trainings",
        "gap_analyses",
        "recommendations",
        "scenario_runs",
        "issue_records",
        "audit_events",
    ]

    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("-- ==========================================================\n")
        f.write("-- WorkforceIQ Deterministic Synthetic Data Seed Script     \n")
        f.write("-- Notice: All records are synthetic; no real PII contained \n")
        f.write("-- ==========================================================\n\n")
        f.write("BEGIN TRANSACTION;\n\n")

        for table in insertion_order:
            records = dataset.get(table, [])
            if not records:
                continue

            sorted_records = sorted(records, key=lambda x: x.get("business_id") or x.get("id"))
            columns = [k for k in sorted_records[0].keys() if k != "experience_tier"]

            f.write(f"-- Table: {table} ({len(sorted_records)} rows)\n")
            cols_joined = ", ".join(columns)

            for r in sorted_records:
                vals = []
                for col in columns:
                    val = r.get(col)
                    if val is None:
                        vals.append("NULL")
                    elif isinstance(val, (int, float, Decimal)):
                        vals.append(str(val))
                    elif isinstance(val, bool):
                        vals.append("TRUE" if val else "FALSE")
                    elif isinstance(val, dict):
                        escaped_json = json.dumps(val, cls=CustomJSONEncoder).replace("'", "''")
                        vals.append(f"'{escaped_json}'")
                    elif isinstance(val, (date, datetime)):
                        vals.append(f"'{val.isoformat()}'")
                    else:
                        escaped = str(val).replace("'", "''")
                        vals.append(f"'{escaped}'")

                vals_joined = ", ".join(vals)
                f.write(f"INSERT INTO {table} ({cols_joined}) VALUES ({vals_joined});\n")
            f.write("\n")

        f.write("COMMIT;\n")

    return {"sql/seed_data.sql": calculate_sha256(sql_path)}


def write_manifest(
    config: GeneratorConfig,
    dataset: Dict[str, List[Dict[str, Any]]],
    checksums: Dict[str, str],
    output_dir: Path,
    generation_duration_sec: float,
) -> Path:
    """Generate provenance manifest recording synthetic data integrity and parameters."""
    manifest_path = output_dir / "manifest.json"

    row_counts = {table: len(records) for table, records in dataset.items()}
    total_rows = sum(row_counts.values())

    manifest_payload = {
        "workforceiq_generator_version": "1.0.0",
        "provenance": {
            "source": "WorkforceIQ Synthetic Data Generation Engine",
            "is_synthetic": True,
            "disclaimer": "This dataset is 100% synthetic, procedurally generated for simulation, workforce modeling, and enterprise benchmarking. No confidential or real personal employee data is used.",
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_duration_seconds": round(generation_duration_sec, 2),
        },
        "configuration": {
            "scale": config.scale,
            "seed": config.seed,
            "as_of_date": config.as_of_date.isoformat(),
            "planning_start_date": config.planning_start_date.isoformat(),
            "planning_end_date": config.planning_end_date.isoformat(),
            "target_scale_config": {
                "employee_count": config.scale_config.employee_count,
                "skill_count": config.scale_config.skill_count,
                "project_count": config.scale_config.project_count,
                "role_count": config.scale_config.role_count,
                "months_of_demand": config.scale_config.months_of_demand,
            },
        },
        "summary_statistics": {
            "total_tables": len(row_counts),
            "total_rows_generated": total_rows,
            "table_row_counts": row_counts,
        },
        "sha256_file_checksums": checksums,
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_payload, f, indent=2)

    return manifest_path


async def seed_dataset_to_database(engine: AsyncEngine, dataset: Dict[str, List[Dict[str, Any]]]) -> int:
    """
    Directly insert generated synthetic dataset into the active database engine using bulk inserts.
    Respects foreign key hierarchy.
    """
    insertion_order = [
        ("roles", "roles"),
        ("skills", "skills"),
        ("role_skills", "role_skills"),
        ("employees", "employees"),
        ("employee_skills", "employee_skills"),
        ("availabilities", "availabilities"),
        ("projects", "projects"),
        ("demand_plans", "demand_plans"),
        ("allocations", "allocations"),
        ("trainings", "trainings"),
        ("gap_analyses", "gap_analyses"),
        ("recommendations", "recommendations"),
        ("scenario_runs", "scenario_runs"),
        ("issue_records", "issue_records"),
        ("audit_events", "audit_events"),
    ]

    total_inserted = 0
    from app.models.base import Base

    async with engine.begin() as conn:
        for key, table_name in insertion_order:
            records = dataset.get(key, [])
            if not records:
                continue

            table_obj = Base.metadata.tables.get(table_name)
            if table_obj is None:
                continue

            # Filter out generator-internal metadata like 'experience_tier'
            col_names = set(c.name for c in table_obj.columns)
            clean_records = []
            for r in records:
                clean_r = {k: v for k, v in r.items() if k in col_names}
                clean_records.append(clean_r)

            await conn.execute(table_obj.insert(), clean_records)
            total_inserted += len(clean_records)

    return total_inserted
