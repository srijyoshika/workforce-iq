# WorkforceIQ Enterprise Business Rules & Data Governance

This specification defines the foundational data governance policies, relational cardinality rules, constraints, and audit preservation mechanisms enforced across the **WorkforceIQ** platform.

---

## 1. Core Entity Cardinality & Associative Rules

| Relationship | Cardinality | Implementation & Governance Rule |
| :--- | :--- | :--- |
| **Employee ↔ Skill** | **Many-to-Many** | Implemented through the `EmployeeSkill` bridge table. An employee possesses multiple skills; a skill is shared across many employees. Each association captures an independently verified proficiency level (1–5) and timestamped validity span. |
| **Role ↔ Skill** | **Many-to-Many** | Implemented through the `RoleSkill` bridge table. A role benchmarks multiple mandatory or desirable skills with distinct importance weights ($0.00–1.00$) and target proficiency levels ($1–5$). |
| **Project ↔ DemandPlan** | **One-to-Many** | A single project initiative contains multiple time-phased demand line items broken down by role, required competency, start/end dates, and ISO week numbers. |
| **Employee ↔ Allocation** | **One-to-Many** | An employee may be simultaneously or consecutively allocated across multiple projects and demand lines. |
| **Project ↔ Allocation** | **One-to-Many** | A project receives multiple employee allocations to fulfill its collective demand plans. |
| **GapAnalysis ↔ Recommendation** | **One-to-Many** | An identified skill/capacity deficit triggers one or more intelligence recommendations (e.g., training, internal reallocation, contractor hiring). |

---

## 2. Historical Record Preservation & Auditability

### 2.1 Allocation History Preservation
- **Rule**: **Do not silently overwrite historical records.**
- When an employee's allocation percentage, date range, or billing rate is modified:
  1. The existing record's `is_active` flag is set to `FALSE`.
  2. A new `Allocation` record is inserted with `version = previous_version + 1`.
  3. The older record's `superseded_by_id` foreign key points to the newly created version.
  4. Both records are permanently preserved for historical variance analysis, billing audits, and predictive model backtesting.

### 2.2 Skill Verification & Competency Progression History
- **Rule**: **Preserve employee skill verification history.**
- Employees cannot delete or overwrite prior skill assessments.
- When an employee upgrades their proficiency (e.g., from Level 2 to Level 4) or obtains managerial verification:
  1. The previous assessment is marked `is_current = FALSE` with an explicit `effective_end_date`.
  2. A new `EmployeeSkill` assessment is inserted with `is_current = TRUE`, `effective_start_date`, and the verifier's identity (`verified_by_id`).
  3. Unique constraint `(employee_id, skill_id, effective_start_date)` ensures deterministic timeline indexing.

### 2.3 Tamper-Evident Audit Logging
- Every transactional mutation (INSERT, UPDATE, DELETE, VERIFY, ALLOCATE, SIMULATE) emits an immutable `AuditEvent` entry recording:
  - Actor employee identifier (`performed_by_id`).
  - Target entity class and identifier (`entity_type`, `entity_id`).
  - Action taken (`action`).
  - UTC timestamp (`timestamp`).
  - JSON snapshots of prior state (`old_values`) and subsequent state (`new_values`).
  - Stated operational justification (`reason`).

---

## 3. Identification & Keying Conventions

### 3.1 Primary Keys vs. Business Identifiers
- **Surrogate Primary Keys**: Standard UUID version 4 strings (`id: VARCHAR(36)`) serve as universal primary keys for optimized index lookups and decoupled foreign key references.
- **Natural / Business Keys**: Human-readable, immutable business identifiers are stored in a dedicated `business_id` column with unique, indexed constraints.
- **Rule**: **Never use employee names, project titles, or human labels as primary or foreign keys.**

### 3.2 Canonical Business Identifier Format Conventions

| Entity | Pattern | Example | Notes |
| :--- | :--- | :--- | :--- |
| **Employee** | `EMP-######` | `EMP-000001` | Sequential zero-padded integer |
| **Skill** | `SKL-######` | `SKL-000001` | Taxonomy catalog identifier |
| **Role** | `ROL-######` | `ROL-000001` | Job role catalog identifier |
| **Project** | `PRJ-YYYY-######` | `PRJ-2026-000001` | Year-anchored sequence |
| **DemandPlan** | `DEM-<project-code>-YYYYWww` | `DEM-PRJ-2026-000001-2026W01` | Tied to project and ISO planning week |
| **Allocation** | `ALLOC-YYYY-######` | `ALLOC-2026-000001` | Year-anchored allocation sequence |
| **Availability** | `AVL-YYYY-######` | `AVL-2026-000001` | Leave / calendar booking sequence |
| **Training** | `TRN-YYYY-######` | `TRN-2026-000001` | Upskilling enrollment sequence |
| **GapAnalysis** | `GAP-YYYY-######` | `GAP-2026-000001` | Capability deficit identifier |
| **Recommendation** | `REC-YYYY-######` | `REC-2026-000001` | AI advisory record identifier |
| **ScenarioRun** | `SCN-YYYY-######` | `SCN-2026-000001` | Simulation run identifier |
| **IssueRecord** | `ISS-YYYY-######` | `ISS-2026-000001` | Risk / conflict tracking identifier |
| **AuditEvent** | `AUD-YYYY-######` | `AUD-2026-000001` | Immutable audit log sequence |

---

## 4. Integrity, Validation & Domain Constraints

### 4.1 Chronological Date Constraints
All temporal entities enforce logical date order via database check constraints:
- `projects`: `CHECK (end_date >= start_date)`
- `demand_plans`: `CHECK (end_date >= start_date)`
- `allocations`: `CHECK (end_date >= start_date)`
- `availabilities`: `CHECK (end_date >= start_date)`
- `trainings`: `CHECK (completion_date IS NULL OR completion_date >= start_date)`
- `employees`: `CHECK (exit_date IS NULL OR exit_date >= hire_date)`
- `employee_skills`: `CHECK (effective_end_date IS NULL OR effective_end_date >= effective_start_date)`

### 4.2 Numerical Range & Domain Checks
- **Skill Proficiency Scale**:
  - `employee_skills.proficiency_level`: `CHECK (proficiency_level >= 1 AND proficiency_level <= 5)`
  - `role_skills.required_proficiency`: `CHECK (required_proficiency >= 1 AND required_proficiency <= 5)`
  - `demand_plans.min_proficiency`: `CHECK (min_proficiency >= 1 AND min_proficiency <= 5)`
  - `trainings.target_proficiency`: `CHECK (target_proficiency >= 1 AND target_proficiency <= 5)`
  - `gap_analyses.required_proficiency`: `CHECK (required_proficiency >= 1 AND required_proficiency <= 5)`
- **Capacity & Workload Percentage**:
  - `allocations.allocation_percentage`: `CHECK (allocation_percentage >= 0.00 AND allocation_percentage <= 100.00)`
  - `availabilities.capacity_percentage`: `CHECK (capacity_percentage >= 0.00 AND capacity_percentage <= 100.00)`
  - `availabilities.available_hours_per_day`: `CHECK (available_hours_per_day >= 0.00 AND available_hours_per_day <= 24.00)`
- **Confidence & Weights**:
  - `recommendations.confidence_score`: `CHECK (confidence_score >= 0.000 AND confidence_score <= 1.000)`
  - `role_skills.importance_weight`: `CHECK (importance_weight >= 0.00 AND importance_weight <= 1.00)`
- **Financial & Headcount Measures**:
  - `demand_plans.required_headcount`: `CHECK (required_headcount > 0)`
  - `demand_plans.required_hours`: `CHECK (required_hours > 0.00)`
  - `demand_plans.fulfilled_hours`: `CHECK (fulfilled_hours >= 0.00)`
  - `projects.budget`: `CHECK (budget IS NULL OR budget >= 0.00)`
  - `employees.standard_hours_per_week`: `CHECK (standard_hours_per_week > 0.00 AND standard_hours_per_week <= 80.00)`

### 4.3 Referential Actions
- `RESTRICT` on core taxonomy dimensions (`skills`, `roles`, `employees`) prevents accidental deletion of records referenced by active allocations, demand plans, or audit trails.
- `CASCADE` is strictly scoped to dependent operational children (e.g., deleting a draft `Project` cascades to its owned `DemandPlans` and unconfirmed `Allocations`).

---

## 5. Lifecycle States & State Transition Machines

### 5.1 Project Lifecycle (`ProjectStatus`)
$$\text{PIPELINE} \longrightarrow \text{DRAFT} \longrightarrow \text{APPROVED} \longrightarrow \text{ACTIVE} \longrightarrow \begin{cases} \text{COMPLETED} \\ \text{ON\_HOLD} \\ \text{CANCELLED} \end{cases}$$
- Only `APPROVED` or `ACTIVE` projects can receive confirmed employee allocations.

### 5.2 Demand Plan Lifecycle (`DemandStatus`)
$$\text{DRAFT} \longrightarrow \text{SUBMITTED} \longrightarrow \text{APPROVED} \longrightarrow \begin{cases} \text{PARTIALLY\_FULFILLED} \\ \text{FULFILLED} \\ \text{CANCELLED} \end{cases}$$
- When total active allocated hours match or exceed `required_hours`, status automatically transitions to `FULFILLED`.

### 5.3 Staffing Allocation Lifecycle (`AllocationStatus`)
$$\text{PROPOSED} \longrightarrow \text{CONFIRMED} \longrightarrow \text{ACTIVE} \longrightarrow \begin{cases} \text{COMPLETED} \\ \text{RELEASED} \\ \text{CANCELLED} \end{cases}$$
- `PROPOSED`: Draft allocations evaluated by resource managers or optimization algorithms.
- `CONFIRMED`: Contractually booked; debits employee's net availability.
- `ACTIVE`: Engagement has commenced and is currently underway.

### 5.4 Competency Verification Lifecycle (`VerificationStatus`)
$$\text{SELF\_REPORTED} \longrightarrow \text{PEER\_REVIEWED} \longrightarrow \begin{cases} \text{MANAGER\_VERIFIED} \\ \text{ASSESSMENT\_CERTIFIED} \end{cases} \longrightarrow \begin{cases} \text{EXPIRED} \\ \text{REVOKED} \end{cases}$$
- Reallocation optimization algorithms assign higher confidence weighting to `ASSESSMENT_CERTIFIED` and `MANAGER_VERIFIED` proficiencies.

