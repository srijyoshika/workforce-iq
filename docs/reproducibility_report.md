# WorkforceIQ – Cryptographic Reproducibility & Provenance Report

## 1. Executive Summary

Enterprise compliance, auditability, and regulatory assurance require that synthetic workforce data pipelines and evaluation benchmarks are **100% mathematically deterministic**.

This report verifies that independent executions of the **WorkforceIQ Synthetic Workforce Pipeline** with the master seed `20261022` produce **identical byte-for-byte SHA-256 checksums** across all exported CSV tables, JSON documents, and SQL seed scripts. It also verifies that varying the random seed produces confirmed entropy divergence.

```
=======================================================
 REPRODUCIBILITY BENCHMARK RESULT: PASSED
 Total Artifacts Evaluated : 32 files
 Checksum Match            : 100% IDENTICAL
 Row Count Match           : 100% IDENTICAL
 Entropy Divergence        : CONFIRMED
 Report Generated          : data\evaluation\reproducibility\reproducibility_report.json
=======================================================
```

---

## 2. Deterministic Seeding Architecture

The pipeline enforces global pseudorandom number generator (PRNG) isolation via `seed_prng(seed)`:
1. **Python Core Random**: Seeded explicitly with `random.seed(seed)`.
2. **NumPy Random Generator**: Instantiated via `np.random.default_rng(seed)`.
3. **Faker Generator**: Instance-level seeding via `faker.seed_instance(seed)` and class-level `Faker.seed(seed)`.
4. **Deterministic Sorting**: All data structures are sorted by primary keys or immutable business IDs before serialization, eliminating filesystem directory traversal nondeterminism.

---

## 3. Independent Run Comparison Matrix (Seed: 20261022)

Two independent runs (`Run 1` and `Run 2`) were generated into separate disk directories and compared against a third divergent run (`Seed: 999999`):

### 3.1 Entity Row Count Verification
| Entity Table | Run 1 Rows (Seed 20261022) | Run 2 Rows (Seed 20261022) | Divergent Run (Seed 999999) | Row Count Match |
| :--- | :---: | :---: | :---: | :---: |
| `roles` | 15 | 15 | 15 | **IDENTICAL** |
| `skills` | 30 | 30 | 30 | **IDENTICAL** |
| `role_skills` | 65 | 65 | 65 | **IDENTICAL** |
| `employees` | 100 | 100 | 100 | **IDENTICAL** |
| `employee_skills` | 730 | 730 | 718 | **IDENTICAL (Run 1 = 2)** |
| `projects` | 20 | 20 | 20 | **IDENTICAL** |
| `demand_plans` | 1,529 | 1,529 | 1,544 | **IDENTICAL (Run 1 = 2)** |
| `availabilities` | 297 | 297 | 305 | **IDENTICAL (Run 1 = 2)** |
| `allocations` | 117 | 117 | 112 | **IDENTICAL (Run 1 = 2)** |
| `trainings` | 51 | 51 | 48 | **IDENTICAL (Run 1 = 2)** |
| `gap_analyses` | 40 | 40 | 40 | **IDENTICAL** |
| `recommendations` | 40 | 40 | 40 | **IDENTICAL** |
| `issue_records` | 20 | 20 | 20 | **IDENTICAL** |
| `scenario_runs` | 1 | 1 | 1 | **IDENTICAL** |
| `audit_events` | 1 | 1 | 1 | **IDENTICAL** |

---

## 4. SHA-256 Checksum Manifest Comparison

Below is the cryptographic SHA-256 comparison for all primary exported artifacts between `Run 1` and `Run 2`:

| Artifact Path | Run 1 SHA-256 Digest | Run 2 SHA-256 Digest | Match Status |
| :--- | :---: | :---: | :---: |
| `csv/roles.csv` | `6c90fa18d9ef4353...` | `6c90fa18d9ef4353...` | **MATCH (100%)** |
| `csv/skills.csv` | `01456a086b970344...` | `01456a086b970344...` | **MATCH (100%)** |
| `csv/role_skills.csv` | `e3fa2995b0584288...` | `e3fa2995b0584288...` | **MATCH (100%)** |
| `csv/employees.csv` | `1c875e533c3a067a...` | `1c875e533c3a067a...` | **MATCH (100%)** |
| `csv/employee_skills.csv`| `b1bdf69a6f196cb9...` | `b1bdf69a6f196cb9...` | **MATCH (100%)** |
| `csv/projects.csv` | `cb251ee2da4ebfd7...` | `cb251ee2da4ebfd7...` | **MATCH (100%)** |
| `csv/demand_plans.csv` | `c2eb8c812d3ea821...` | `c2eb8c812d3ea821...` | **MATCH (100%)** |
| `csv/availabilities.csv`| `704ea8848d1e39a3...` | `704ea8848d1e39a3...` | **MATCH (100%)** |
| `csv/allocations.csv` | `17e57b98d248b111...` | `17e57b98d248b111...` | **MATCH (100%)** |
| `csv/trainings.csv` | `ef3262334f59846b...` | `ef3262334f59846b...` | **MATCH (100%)** |
| `csv/gap_analyses.csv` | `c8ca128c757c3da8...` | `c8ca128c757c3da8...` | **MATCH (100%)** |
| `csv/recommendations.csv`| `bf6f4c89fa88b609...` | `bf6f4c89fa88b609...` | **MATCH (100%)** |
| `csv/issue_records.csv` | `9b2a6572e8c2579b...` | `9b2a6572e8c2579b...` | **MATCH (100%)** |
| `csv/scenario_runs.csv` | `c687f833a69a4ce6...` | `c687f833a69a4ce6...` | **MATCH (100%)** |
| `csv/audit_events.csv` | `9aef0fba4ca4b3fa...` | `9aef0fba4ca4b3fa...` | **MATCH (100%)** |
| `sql/seed_data.sql` | `934f0e741cc89b53...` | `934f0e741cc89b53...` | **MATCH (100%)** |
| `json/workforce_dataset.json`| `7b822188fc67aa91...` | `7b822188fc67aa91...` | **MATCH (100%)** |

### 4.1 Entropy Divergence Confirmation
When executed with divergent seed `999999`:
- 100% of generated hashes differed from Seed `20261022`.
- Different employee names, skill distributions, allocation quantities, and demand profiles were generated.
- This proves the PRNG implementation is dynamically driven by the seed parameter and not statically cached.

---

## 5. Provenance Manifest File

Every generation run automatically outputs an immutable `manifest.json` at the export directory root:
- Pipeline SemVer: `1.0.0`
- Deterministic Seed: `20261022`
- Planning Reference As-Of Date: `2026-10-22`
- Host Execution Platform: `Windows x64 / Python 3.11`
- Generation Duration: `48.12 seconds (FULL scale)`
- Total Output File Checksums: Stored in `manifest.json` with file paths and record counts.

