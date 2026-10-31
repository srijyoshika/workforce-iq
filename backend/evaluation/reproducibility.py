"""
WorkforceIQ Reproducibility Verification Engine.

Executes identical synthetic pipeline configurations across independent runs,
calculates cryptographic SHA-256 checksums, validates row-count identity,
and produces a structured reproducibility_report.json.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any, Dict

# Ensure paths
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

for p in [str(PROJECT_ROOT), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.generator.config import GeneratorConfig
from backend.generator.export import export_to_csv, export_to_json, export_to_sql
from backend.generator.generate import generate_workforce_dataset


def calculate_dir_checksums(directory: Path) -> Dict[str, str]:
    """Recursively calculate SHA-256 checksums for all files in a directory."""
    checksums = {}
    for fpath in sorted(directory.rglob("*")):
        if fpath.is_file() and not fpath.name.endswith(".tmp"):
            rel_name = str(fpath.relative_to(directory)).replace("\\", "/")
            h = hashlib.sha256()
            with open(fpath, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            checksums[rel_name] = h.hexdigest()
    return checksums


def run_reproducibility_benchmark(
    scale: str = "starter",
    seed: int = 20261022,
    divergence_seed: int = 999999,
    output_dir: Path = Path("data/evaluation/reproducibility"),
) -> Dict[str, Any]:
    """
    Run identical generation runs to confirm byte-for-byte SHA256 reproducibility,
    and a divergent run to confirm entropy variation.
    """
    output_dir = Path(output_dir)
    run1_dir = output_dir / "run_1"
    run2_dir = output_dir / "run_2"
    diff_dir = output_dir / "run_diff"

    for d in [run1_dir, run2_dir, diff_dir]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    config_base = GeneratorConfig(scale=scale, seed=seed)
    config_diff = GeneratorConfig(scale=scale, seed=divergence_seed)

    print(f"\n[Reproducibility Test] Executing Run 1 (Seed: {seed}, Scale: {scale.upper()})...")
    dataset_1 = generate_workforce_dataset(config_base)
    export_to_csv(dataset_1, run1_dir)
    export_to_json(dataset_1, run1_dir)
    export_to_sql(dataset_1, run1_dir)

    print(f"[Reproducibility Test] Executing Run 2 (Seed: {seed}, Scale: {scale.upper()})...")
    dataset_2 = generate_workforce_dataset(config_base)
    export_to_csv(dataset_2, run2_dir)
    export_to_json(dataset_2, run2_dir)
    export_to_sql(dataset_2, run2_dir)

    print(f"[Reproducibility Test] Executing Divergent Run 3 (Seed: {divergence_seed}, Scale: {scale.upper()})...")
    dataset_3 = generate_workforce_dataset(config_diff)
    export_to_csv(dataset_3, diff_dir)
    export_to_json(dataset_3, diff_dir)

    # Compute checksums
    run1_hashes = calculate_dir_checksums(run1_dir)
    run2_hashes = calculate_dir_checksums(run2_dir)
    diff_hashes = calculate_dir_checksums(diff_dir)

    # Compare checksums between Run 1 and Run 2
    all_files = sorted(set(run1_hashes.keys()) | set(run2_hashes.keys()))
    checksum_matches = {}
    all_checksums_identical = True

    for f_rel in all_files:
        h1 = run1_hashes.get(f_rel)
        h2 = run2_hashes.get(f_rel)
        match = (h1 == h2) and (h1 is not None)
        checksum_matches[f_rel] = {
            "run_1_sha256": h1,
            "run_2_sha256": h2,
            "identical": match,
        }
        if not match:
            all_checksums_identical = False

    # Compare row counts
    row_count_matches = {}
    all_row_counts_identical = True
    for table_name in sorted(dataset_1.keys()):
        c1 = len(dataset_1[table_name])
        c2 = len(dataset_2[table_name])
        match = (c1 == c2)
        row_count_matches[table_name] = {
            "run_1_rows": c1,
            "run_2_rows": c2,
            "identical": match,
        }
        if not match:
            all_row_counts_identical = False

    # Check divergence with Run 3 (divergent seed)
    divergence_confirmed = False
    for f_rel, h1 in run1_hashes.items():
        if f_rel in diff_hashes and diff_hashes[f_rel] != h1:
            divergence_confirmed = True
            break

    status = "PASSED" if (all_checksums_identical and all_row_counts_identical and divergence_confirmed) else "FAILED"

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "scale": scale,
        "seed": seed,
        "divergence_seed": divergence_seed,
        "summary": {
            "total_files_evaluated": len(all_files),
            "all_checksums_identical": all_checksums_identical,
            "all_row_counts_identical": all_row_counts_identical,
            "entropy_divergence_confirmed": divergence_confirmed,
        },
        "row_count_comparison": row_count_matches,
        "checksum_comparison": checksum_matches,
    }

    report_path = output_dir / "reproducibility_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n=======================================================")
    print(f" REPRODUCIBILITY BENCHMARK RESULT: {status}")
    print(f" Total Artifacts Evaluated : {len(all_files)} files")
    print(f" Checksum Match            : {'100% IDENTICAL' if all_checksums_identical else 'MISMATCH'}")
    print(f" Row Count Match           : {'100% IDENTICAL' if all_row_counts_identical else 'MISMATCH'}")
    print(f" Entropy Divergence        : {'CONFIRMED' if divergence_confirmed else 'FAILED'}")
    print(f" Report Generated          : {report_path}")
    print(f"=======================================================\n")

    return report


def main():
    parser = argparse.ArgumentParser(description="WorkforceIQ Reproducibility Verification CLI")
    parser.add_argument("--scale", choices=["starter", "full"], default="starter", help="Dataset scale")
    parser.add_argument("--seed", type=int, default=20261022, help="Deterministic random seed")
    parser.add_argument("--output-dir", type=str, default="data/evaluation/reproducibility", help="Output directory")

    args = parser.parse_args()
    run_reproducibility_benchmark(
        scale=args.scale,
        seed=args.seed,
        output_dir=Path(args.output_dir),
    )


if __name__ == "__main__":
    main()
