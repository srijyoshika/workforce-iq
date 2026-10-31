# WorkforceIQ – Full Dataset Validation & Anomaly Detection Report

## 1. Executive Summary

This report presents the empirical validation and evaluation results of the **WorkforceIQ** platform on the complete enterprise **FULL Scale Dataset** (5,000 employees, 300 skills, 500 projects, 40 roles, 12 months of demand) generated deterministically using seed `20261022`.

Validation was executed in two phases:
1. **Clean Baseline Integrity Audit**: Verifying relational, temporal, and contractual constraints before any anomalies are introduced.
2. **Controlled Anomaly Detection Evaluation**: Injecting 60 deliberate, labeled anomalies across the 4 mandatory categories, storing ground truth in an isolated decoupled store, and evaluating the platform's detection engines against ground truth.

---

## 2. Dataset Scale & Entity Distribution

- **Random Seed**: `20261022`
- **As-of Planning Date**: `2026-10-22`
- **Generation Duration**: `48.12 seconds`
- **Total Relational Records**: `113,358 rows`

### Entity Breakdown
| Entity Table | Generated Record Count | Primary Key Type | Business ID Convention |
| :--- | :---: | :---: | :--- |
| `roles` | **40** | UUID v4 | `ROL-001` .. `ROL-040` |
| `skills` | **300** | UUID v4 | `SKL-001` .. `SKL-300` |
| `role_skills` | **196** | Composite PK | Bridge mapping role competencies |
| `employees` | **5,000** | UUID v4 | `EMP-2026-000001` .. `EMP-2026-005000` |
| `employee_skills` | **43,633** | Composite PK | `ESK-2026-000001` .. Bridge profiles |
| `projects` | **500** | UUID v4 | `PRJ-2026-0001` .. `PRJ-2026-0500` |
| `demand_plans` | **42,210** | UUID v4 | `DEM-2026-000001` .. Time-phased weekly demand |
| `availabilities` | **14,845** | UUID v4 | `AVL-2026-000001` .. PTO, Holidays, Sick Leave |
| `allocations` | **3,068** | UUID v4 | `ALC-2026-000001` .. Project staffing commitments |
| `trainings` | **1,544** | UUID v4 | `TRN-2026-000001` .. Upskilling course records |
| `gap_analyses` | **1,000** | UUID v4 | `GAP-2026-000001` .. Precomputed deficit metrics |
| `recommendations` | **1,000** | UUID v4 | `REC-2026-000001` .. AI remediation proposals |
| `issue_records` | **20** | UUID v4 | `ISS-2026-000001` .. Operational risk flags |
| `scenario_runs` | **1** | UUID v4 | `SCN-2026-000001` .. Baseline scenario definition |
| `audit_events` | **1** | UUID v4 | `AUD-2026-000001` .. Initial system provenance log |
| **TOTAL RECORDS** | **113,358** | | |

---

## 3. Baseline Data Quality Audit Results

Before anomaly injection, the dataset was subjected to comprehensive relational and semantic integrity checks via `backend/evaluation/validate.py`:

```
=======================================================
[Step 2/5] Validating Baseline Dataset (Target: 0 Errors, 0 Anomalies)...
  -> Baseline Integrity Status : PASSED
  -> Baseline Integrity Errors : 0
  -> Baseline Anomalies Found  : 0
=======================================================
```

### Relational Integrity Criteria
1. **Primary Key Uniqueness**: Evaluated 113,358 records across all tables. Duplicate PK count = `0`.
2. **Foreign Key Integrity**: Evaluated all 11 foreign key constraints (e.g., `employee_skills.employee_id -> employees.id`, `demand_plans.project_id -> projects.id`). Orphaned references = `0`.
3. **Enum Domain Adherence**: 100% of status and type fields conformed to allowed enum choices (`EmploymentStatus`, `DemandStatus`, `AllocationStatus`, `AvailabilityType`, `IssueSeverity`).
4. **Temporal Consistency**: 100% of records satisfied `start_date <= end_date`. Zero allocations or projects exhibited inverted chronological windows.
5. **Contractual Capacity Consistency**: All contractual hours were strictly positive ($20.0 \le \text{standard\_hours} \le 40.0$).

---

## 4. Controlled Anomaly Injection & Decoupled Ground Truth

To scientifically evaluate exception detection, 60 deliberate anomalies were injected across the four mandatory operational categories (15 anomalies per category) via `backend/generator/anomalies.py`:

### Decoupled Ground Truth Preservation
- Ground truth metadata was exported directly to `data/evaluation/ground_truth.json` and `data/evaluation/ground_truth.csv`.
- Ground truth contains: `ground_truth_id`, `anomaly_type`, `entity_type`, `entity_id`, `field_name`, `original_value`, `injected_value`, `injected_delta`, and `injection_rationale`.
- **Governance Boundary**: Ground truth files reside strictly outside application operational tables. Application services cannot access ground-truth labels.

---

## 5. Anomaly Detection Performance & Confusion Matrix

The `DataValidator` engine was executed on the anomalous dataset. Detection results were mapped against the decoupled ground truth:

```
=======================================================
 EVALUATION RESULTS & PERFORMANCE BENCHMARK
=======================================================
 Overall Precision : 100.0%
 Overall Recall    : 100.0%
 Overall F1-Score  : 1.0000
 Overall Accuracy  : 100.00%
-------------------------------------------------------
 Confusion Matrix  : TP=60 | FP=0 | FN=0 | TN=92024
=======================================================
```

### Confusion Matrix
| Metric | Injected Anomaly (Positive) | Normal Record (Negative) | Total |
| :--- | :---: | :---: | :---: |
| **Detected by Engine** | **True Positive (TP) = 60** | **False Positive (FP) = 0** | **60 Detected** |
| **Not Detected** | **False Negative (FN) = 0** | **True Negative (TN) = 92,024** | **92,024 Negative** |
| **Actual Ground Truth** | **60 Anomalies** | **92,024 Records** | **92,084 Evaluated** |

### Per-Issue Category Performance Breakdown

| Anomaly Category | Ground Truth Count | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **OVERALLOCATION** | 15 | 15 | 0 | 0 | **100.0%** | **100.0%** | **1.0000** |
| **STALE_SKILL** | 15 | 15 | 0 | 0 | **100.0%** | **100.0%** | **1.0000** |
| **DUPLICATE_DEMAND** | 15 | 15 | 0 | 0 | **100.0%** | **100.0%** | **1.0000** |
| **OVERLAPPING_ALLOCATION** | 15 | 15 | 0 | 0 | **100.0%** | **100.0%** | **1.0000** |
| **OVERALL TOTAL** | **60** | **60** | **0** | **0** | **100.0%** | **100.0%** | **1.0000** |

### Qualitative Anomaly Descriptions
1. **OVERALLOCATION**: Employee allocated 50-60 hours per week against a 40-hour contractual capacity. Correctly detected and categorized as `CAPACITY_OVERLOAD` with calculated excess hours.
2. **STALE_SKILL**: Employee skill verification timestamp older than 730 days (2 years) while `is_current=True`. Correctly flagged as `SKILL_SHORTAGE` without mutating underlying verification history.
3. **DUPLICATE_DEMAND**: Identical demand requirement submitted multiple times for the same project, role, and week. Detected by unique hash clustering.
4. **OVERLAPPING_ALLOCATION**: Concurrent active allocations for an employee during overlapping project dates totaling beyond capacity. Flagged as `ALLOCATION_CONFLICT`.

