"""
Automated Test Suite for Data Quality, Anomaly Injection, Ground Truth, and Reproducibility.

Verifies:
1. Valid baseline generation produces zero integrity errors and zero anomalies.
2. Controlled anomaly injection produces all 4 mandatory anomalies while preserving originals.
3. Decoupled Ground Truth schemas and zero label leakage into operational models.
4. Anomaly detection performance (Precision, Recall, F1, and Confusion Matrix).
5. Exact quantitative anomaly metrics (excess hours, days overdue, overlap intervals).
6. Full cryptographic reproducibility across repeated seed execution.
"""

from copy import deepcopy
import json
from pathlib import Path
import pytest

from backend.generator.anomalies import inject_anomalies
from backend.generator.config import GeneratorConfig
from backend.generator.generate import generate_workforce_dataset
from backend.generator.ground_truth import GroundTruthRecord, save_ground_truth
from backend.evaluation.evaluate import evaluate_anomaly_detection
from backend.evaluation.reproducibility import run_reproducibility_benchmark
from backend.evaluation.validate import DataValidator


@pytest.fixture(scope="module")
def baseline_dataset():
    """Deterministic clean baseline dataset."""
    config = GeneratorConfig(scale="starter", seed=20261022)
    return generate_workforce_dataset(config)


@pytest.fixture(scope="module")
def anomalous_suite(baseline_dataset):
    """Anomalous dataset with injected Ground Truth."""
    config = GeneratorConfig(scale="starter", seed=20261022)
    data_copy = {k: list(v) for k, v in baseline_dataset.items()}
    anom_data, gt_records = inject_anomalies(data_copy, config, seed=20261022)
    return anom_data, gt_records


def test_baseline_validation_passes(baseline_dataset):
    """Verify that the baseline dataset has zero integrity failures and zero business anomalies."""
    config = GeneratorConfig(scale="starter", seed=20261022)
    validator = DataValidator(config)
    report = validator.validate_dataset(baseline_dataset)

    assert report.is_valid is True, "Baseline dataset must have valid relational integrity"
    assert report.integrity_failures_count == 0, "Baseline dataset must have 0 integrity errors"
    assert report.detected_anomalies_count == 0, "Baseline dataset must have 0 business anomalies"


def test_anomaly_injection_mandatory_types(anomalous_suite):
    """Verify that all four mandatory anomalies are injected with valid ground truth."""
    anom_data, gt_records = anomalous_suite
    injected_types = {gt.issue_type for gt in gt_records}

    assert "OVERALLOCATION" in injected_types
    assert "STALE_SKILL" in injected_types
    assert "DUPLICATE_DEMAND" in injected_types
    assert "OVERLAPPING_ALLOCATION" in injected_types

    # Verify required ground truth schema fields
    for gt in gt_records:
        assert gt.scenario_id.startswith("SCN-ANOMALY-")
        assert gt.entity_type in ["Allocation", "EmployeeSkill", "DemandPlan"]
        assert gt.entity_id is not None
        assert gt.expected_detection is True
        assert gt.expected_severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert gt.expected_action in [
            "REDUCE_ALLOCATION_HOURS",
            "REVERIFY_EMPLOYEE_SKILL",
            "DE_DUPLICATE_DEMAND_LINE",
            "RESOLVE_SCHEDULE_OVERLAP",
        ]
        assert gt.expected_value is not None
        assert gt.rule_version == "1.0.0"


def test_ground_truth_isolation_and_no_leakage(anomalous_suite):
    """Ensure ground-truth labels and scenario metadata are NEVER injected into operational dataset."""
    anom_data, gt_records = anomalous_suite

    # Operational entities must not contain evaluation/ground-truth metadata
    forbidden_metadata_fields = [
        "scenario_id",
        "expected_detection",
        "expected_severity",
        "expected_action",
        "expected_value",
        "rule_version",
        "is_anomaly",
        "ground_truth",
    ]

    for table_name, records in anom_data.items():
        for r in records:
            for field in forbidden_metadata_fields:
                assert field not in r, f"Ground truth evaluation metadata '{field}' leaked into operational table '{table_name}'!"


def test_exact_anomaly_metric_calculations(anomalous_suite):
    """Verify that exact excess hours, days overdue, and overlap times are calculated."""
    anom_data, gt_records = anomalous_suite

    for gt in gt_records:
        val = gt.expected_value
        if gt.issue_type == "OVERALLOCATION":
            assert "capacity_hours" in val
            assert "total_allocated_hours" in val
            assert "excess_hours" in val
            assert val["excess_hours"] > 0
            assert round(val["total_allocated_hours"] - val["capacity_hours"], 2) == val["excess_hours"]
        elif gt.issue_type == "STALE_SKILL":
            assert "elapsed_days" in val
            assert "validity_threshold_days" in val
            assert "days_overdue" in val
            assert val["elapsed_days"] > 730
            assert val["days_overdue"] == val["elapsed_days"] - 730
        elif gt.issue_type == "DUPLICATE_DEMAND":
            assert "original_demand_id" in val
            assert "duplicate_demand_id" in val
            assert "delivery_identity" in val
            assert val["original_demand_id"] != val["duplicate_demand_id"]
        elif gt.issue_type == "OVERLAPPING_ALLOCATION":
            assert "overlap_start" in val
            assert "overlap_end" in val
            assert "overlap_days" in val
            assert "overlap_hours" in val
            assert val["overlap_days"] > 0
            assert val["overlap_hours"] > 0


def test_evaluation_metrics_and_confusion_matrix(anomalous_suite):
    """Verify precision, recall, F1, and confusion matrix against ground truth."""
    anom_data, gt_records = anomalous_suite
    config = GeneratorConfig(scale="starter", seed=20261022)

    eval_report = evaluate_anomaly_detection(anom_data, gt_records, config)
    overall = eval_report["overall_evaluation"]
    metrics = overall["metrics"]
    cm = overall["confusion_matrix"]

    # Target 100% precision, 100% recall, 1.0 F1
    assert metrics["precision"] == 1.0, f"Precision must be 1.0, got {metrics['precision']}"
    assert metrics["recall"] == 1.0, f"Recall must be 1.0, got {metrics['recall']}"
    assert metrics["f1_score"] == 1.0, f"F1-Score must be 1.0, got {metrics['f1_score']}"
    assert cm["FP"] == 0, f"False positives must be 0, got {cm['FP']}"
    assert cm["FN"] == 0, f"False negatives must be 0, got {cm['FN']}"
    assert cm["TP"] == len(gt_records)
    assert cm["TN"] > 2000, "True negatives must evaluate all unaffected normal records"


def test_reproducibility_benchmark_passes(tmp_path):
    """Verify that running the generator twice with the same seed produces identical SHA256 hashes."""
    report = run_reproducibility_benchmark(
        scale="starter",
        seed=20261022,
        output_dir=tmp_path / "reproducibility_test",
    )

    assert report["status"] == "PASSED"
    assert report["summary"]["all_checksums_identical"] is True
    assert report["summary"]["all_row_counts_identical"] is True
    assert report["summary"]["entropy_divergence_confirmed"] is True
