"""
WorkforceIQ Evaluation and Anomaly Detection Benchmarking Engine.

Compares validation-detected exceptions against decoupled Ground Truth expectations:
1. Calculates Precision, Recall, and F1-Score across overall and per-issue categories.
2. Computes Confusion Matrix (TP, FP, FN, TN) including normal negative controls.
3. Produces evaluation_report.json and exports ground_truth.json/ground_truth.csv.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Set, Tuple

# Ensure paths
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

for p in [str(PROJECT_ROOT), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.generator.anomalies import inject_anomalies
from backend.generator.config import GeneratorConfig
from backend.generator.generate import generate_workforce_dataset
from backend.generator.ground_truth import GroundTruthRecord, save_ground_truth
from backend.evaluation.validate import DataValidator, DetectedAnomaly, ValidationReport


def calculate_metrics(tp: int, fp: int, fn: int, tn: int) -> Dict[str, float]:
    """Calculate standard precision, recall, and harmonic F1-score."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if fn == 0 else 0.0)
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 1.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "accuracy": round(accuracy, 4),
    }


def evaluate_anomaly_detection(
    dataset: Dict[str, List[Dict[str, Any]]],
    ground_truth: List[GroundTruthRecord],
    config: GeneratorConfig,
) -> Dict[str, Any]:
    """
    Run DataValidator on dataset and evaluate detection performance against Ground Truth.
    Includes normal negative controls to compute False Positives and True Negatives.
    """
    validator = DataValidator(config)
    val_report: ValidationReport = validator.validate_dataset(dataset)

    # Key sets: (entity_id, issue_type)
    gt_positives: Dict[Tuple[str, str], GroundTruthRecord] = {
        (gt.entity_id, gt.issue_type): gt for gt in ground_truth if gt.expected_detection
    }
    detected_positives: Dict[Tuple[str, str], DetectedAnomaly] = {
        (det.entity_id, det.issue_type): det for det in val_report.detected_anomalies
    }

    # Evaluate across the 4 mandatory anomaly domains
    mandatory_issues = [
        "OVERALLOCATION",
        "STALE_SKILL",
        "DUPLICATE_DEMAND",
        "OVERLAPPING_ALLOCATION",
    ]

    # Calculate negative population (normal unaffected records) per issue type
    total_allocations = len(dataset.get("allocations", []))
    total_skills = len(dataset.get("employee_skills", []))
    total_demands = len(dataset.get("demand_plans", []))

    population_by_issue = {
        "OVERALLOCATION": total_allocations,
        "STALE_SKILL": total_skills,
        "DUPLICATE_DEMAND": total_demands,
        "OVERLAPPING_ALLOCATION": total_allocations,
    }

    per_issue_metrics: Dict[str, Any] = {}
    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_tn = 0

    for issue in mandatory_issues:
        gt_issue_keys = {k for k in gt_positives.keys() if k[1] == issue}
        det_issue_keys = {k for k in detected_positives.keys() if k[1] == issue}

        tp_set = gt_issue_keys & det_issue_keys
        fn_set = gt_issue_keys - det_issue_keys
        fp_set = det_issue_keys - gt_issue_keys

        tp = len(tp_set)
        fn = len(fn_set)
        fp = len(fp_set)

        # True negatives: total candidate population minus ground truth minus false positives
        pop = population_by_issue.get(issue, 100)
        tn = max(0, pop - (tp + fn + fp))

        metrics = calculate_metrics(tp, fp, fn, tn)

        per_issue_metrics[issue] = {
            "confusion_matrix": {"TP": tp, "FP": fp, "FN": fn, "TN": tn},
            "metrics": metrics,
            "true_positive_ids": [k[0] for k in tp_set],
            "false_negative_ids": [k[0] for k in fn_set],
            "false_positive_ids": [k[0] for k in fp_set],
        }

        total_tp += tp
        total_fp += fp
        total_fn += fn
        total_tn += tn

    overall_metrics = calculate_metrics(total_tp, total_fp, total_fn, total_tn)

    evaluation_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scale": config.scale,
        "seed": config.seed,
        "as_of_date": str(config.as_of_date),
        "data_integrity": {
            "is_valid": val_report.is_valid,
            "integrity_failures_count": val_report.integrity_failures_count,
            "failures": [f.to_dict() for f in val_report.integrity_failures],
        },
        "overall_evaluation": {
            "confusion_matrix": {
                "TP": total_tp,
                "FP": total_fp,
                "FN": total_fn,
                "TN": total_tn,
            },
            "metrics": overall_metrics,
            "ground_truth_total": len(ground_truth),
            "detected_anomalies_total": len(val_report.detected_anomalies),
        },
        "per_issue_evaluation": per_issue_metrics,
    }

    return evaluation_report


def run_full_evaluation_pipeline(
    scale: str = "starter",
    seed: int = 20261022,
    output_dir: Path = Path("data/evaluation"),
) -> Dict[str, Any]:
    """
    Execute end-to-end evaluation:
    1. Generate clean baseline data.
    2. Validate baseline (guarantee 0 anomalies).
    3. Inject controlled anomalies and decoupled Ground Truth.
    4. Run validation on anomalous dataset.
    5. Evaluate detection precision, recall, F1, and confusion matrix.
    6. Export ground_truth.json, ground_truth.csv, and evaluation_report.json.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    config = GeneratorConfig(scale=scale, seed=seed)

    print("\n=======================================================")
    print(" WORKFORCEIQ DATA QUALITY & EVALUATION ENGINE")
    print(f" Scale: {scale.upper()} | Seed: {seed} | As-Of Date: {config.as_of_date}")
    print("=======================================================")

    # Step 1: Baseline Generation
    print("\n[Step 1/5] Generating Valid Baseline Dataset...")
    baseline_dataset = generate_workforce_dataset(config)

    # Step 2: Validate Baseline
    print("[Step 2/5] Validating Baseline Dataset (Target: 0 Errors, 0 Anomalies)...")
    validator = DataValidator(config)
    baseline_val = validator.validate_dataset(baseline_dataset)
    print(f"  -> Baseline Integrity Status : {'PASSED' if baseline_val.is_valid else 'FAILED'}")
    print(f"  -> Baseline Integrity Errors : {baseline_val.integrity_failures_count}")
    print(f"  -> Baseline Anomalies Found  : {baseline_val.detected_anomalies_count}")

    if not baseline_val.is_valid:
        raise RuntimeError("Baseline dataset failed relational data integrity validation!")

    # Step 3: Controlled Anomaly Injection
    print("\n[Step 3/5] Injecting Deliberate Anomaly Suite & Decoupled Ground Truth...")
    anomalous_dataset, ground_truth = inject_anomalies(baseline_dataset, config, seed=seed)
    gt_json_path, gt_csv_path = save_ground_truth(ground_truth, output_dir)
    print(f"  -> Injected Ground Truth Total : {len(ground_truth)} anomalies")
    print(f"  -> Saved Ground Truth JSON     : {gt_json_path}")
    print(f"  -> Saved Ground Truth CSV      : {gt_csv_path}")

    # Step 4: Validate Anomalous Dataset
    print("\n[Step 4/5] Running Anomaly Detection Validator on Anomalous Dataset...")
    eval_report = evaluate_anomaly_detection(anomalous_dataset, ground_truth, config)

    # Step 5: Save & Print Report
    eval_json_path = output_dir / "evaluation_report.json"
    with open(eval_json_path, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    overall = eval_report["overall_evaluation"]
    cm = overall["confusion_matrix"]
    metrics = overall["metrics"]

    print("\n=======================================================")
    print(" EVALUATION RESULTS & PERFORMANCE BENCHMARK")
    print("=======================================================")
    print(f" Overall Precision : {metrics['precision'] * 100:.1f}%")
    print(f" Overall Recall    : {metrics['recall'] * 100:.1f}%")
    print(f" Overall F1-Score  : {metrics['f1_score']:.4f}")
    print(f" Overall Accuracy  : {metrics['accuracy'] * 100:.2f}%")
    print("-------------------------------------------------------")
    print(f" Confusion Matrix  : TP={cm['TP']} | FP={cm['FP']} | FN={cm['FN']} | TN={cm['TN']}")
    print("-------------------------------------------------------")
    print(" Per-Issue Breakdown:")
    for issue_type, issue_data in eval_report["per_issue_evaluation"].items():
        sub_cm = issue_data["confusion_matrix"]
        sub_m = issue_data["metrics"]
        print(f"   [{issue_type}]")
        print(f"     Precision: {sub_m['precision']*100:.1f}% | Recall: {sub_m['recall']*100:.1f}% | F1: {sub_m['f1_score']:.4f} (TP={sub_cm['TP']}, FP={sub_cm['FP']}, FN={sub_cm['FN']})")
    print("=======================================================\n")

    return eval_report


def main():
    parser = argparse.ArgumentParser(description="WorkforceIQ Anomaly Detection Evaluation CLI")
    parser.add_argument("--scale", choices=["starter", "full"], default="starter", help="Dataset scale")
    parser.add_argument("--seed", type=int, default=20261022, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="data/evaluation", help="Evaluation output directory")

    args = parser.parse_args()
    run_full_evaluation_pipeline(
        scale=args.scale,
        seed=args.seed,
        output_dir=Path(args.output_dir),
    )


if __name__ == "__main__":
    main()

