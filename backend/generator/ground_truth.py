"""
Ground Truth Management Module.
Defines schema and storage for injected anomaly expectations.
Separated strictly from operational datasets to prevent label leakage.
"""

from dataclasses import asdict, dataclass
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class GroundTruthRecord:
    """
    Ground truth specification for a controlled deliberate anomaly.
    Never embedded into operational input features or database tables.
    """
    scenario_id: str
    entity_type: str
    entity_id: str
    issue_type: str
    expected_detection: bool
    expected_severity: str
    expected_action: str
    expected_value: Union[str, Dict[str, Any]]
    rule_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to JSON-serializable dictionary."""
        d = asdict(self)
        if isinstance(d["expected_value"], dict):
            # Keep as dict for JSON, serialize for CSV
            pass
        return d


def save_ground_truth(
    records: List[GroundTruthRecord],
    output_dir: Path,
) -> tuple[Path, Path]:
    """
    Save ground truth records to separate JSON and CSV files.
    Outputs are deterministically sorted by scenario_id.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "ground_truth.json"
    csv_path = output_dir / "ground_truth.csv"

    # Sort deterministically
    sorted_records = sorted(records, key=lambda r: r.scenario_id)
    dict_records = [r.to_dict() for r in sorted_records]

    # Write JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dict_records, f, indent=2)

    # Write CSV
    fieldnames = [
        "scenario_id",
        "entity_type",
        "entity_id",
        "issue_type",
        "expected_detection",
        "expected_severity",
        "expected_action",
        "expected_value",
        "rule_version",
    ]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in dict_records:
            row = dict(r)
            if isinstance(row["expected_value"], (dict, list)):
                row["expected_value"] = json.dumps(row["expected_value"])
            writer.writerow(row)

    return json_path, csv_path


def load_ground_truth(json_or_csv_path: Path) -> List[GroundTruthRecord]:
    """Load ground truth records from either JSON or CSV format."""
    if not json_or_csv_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {json_or_csv_path}")

    records: List[GroundTruthRecord] = []

    if json_or_csv_path.suffix.lower() == ".json":
        with open(json_or_csv_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            for item in raw_data:
                records.append(GroundTruthRecord(**item))
    elif json_or_csv_path.suffix.lower() == ".csv":
        with open(json_or_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                exp_val = row["expected_value"]
                try:
                    exp_val = json.loads(exp_val)
                except (json.JSONDecodeError, TypeError):
                    pass
                records.append(
                    GroundTruthRecord(
                        scenario_id=row["scenario_id"],
                        entity_type=row["entity_type"],
                        entity_id=row["entity_id"],
                        issue_type=row["issue_type"],
                        expected_detection=row["expected_detection"].lower() == "true",
                        expected_severity=row["expected_severity"],
                        expected_action=row["expected_action"],
                        expected_value=exp_val,
                        rule_version=row["rule_version"],
                    )
                )
    else:
        raise ValueError(f"Unsupported format: {json_or_csv_path.suffix}")

    return records

