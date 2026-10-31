# WorkforceIQ REST API Documentation

WorkforceIQ provides an enterprise-grade RESTful API built on **FastAPI**, **SQLAlchemy 2.0 Async Engine**, **Pydantic v2**, and **PostgreSQL** (with SQLite local development fallback).

All operational and intelligence endpoints are versioned under the `/api/v1` namespace prefix and secured with JWT Bearer Authentication and Role-Based Access Control (RBAC).

---

## 🔐 1. Authentication & Authorization

### Roles
- `ADMIN`: Unrestricted platform access, system configuration, audit viewing.
- `HR_PARTNER`: Employee directory, skills management, upskilling and training.
- `PROJECT_MANAGER`: Project portfolio, demand planning, resource allocation, scenario simulations.
- `OPERATIONS_PARTNER`: Utilization monitoring, capacity forecasting, exception resolution.
- `EMPLOYEE`: Read-only self-service profile and team availability.

### Endpoints

| Method | Endpoint | Description | Roles Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Authenticate with email/password; returns JWT access token | Public |
| `GET` | `/api/v1/auth/me` | Fetch authenticated employee profile, role and permissions | Authenticated |
| `POST` | `/api/v1/auth/logout` | Invalidate current user session | Authenticated |

---

## 👥 2. Workforce & Organizational Taxonomy

### Employees (`/api/v1/employees`)
- `GET /api/v1/employees`: Paginated employee directory with filtering by department, status, role, search query.
- `POST /api/v1/employees`: Provision new workforce member record.
- `GET /api/v1/employees/{id}`: Fetch detailed employee profile with competency profiles and allocations.
- `PUT /api/v1/employees/{id}`: Update employee metadata.
- `DELETE /api/v1/employees/{id}`: Terminate or soft-delete employee record.

### Roles & Skills (`/api/v1/roles`, `/api/v1/skills`)
- `GET /api/v1/roles`: List standardized job roles and competencies.
- `POST /api/v1/roles`: Register new job role taxonomy entry.
- `GET /api/v1/skills`: List capabilities with category filters (`TECHNICAL`, `DOMAIN`, `LEADERSHIP`, `METHODOLOGY`, `TOOL`, `COMPLIANCE`).
- `POST /api/v1/skills`: Add skill definition.
- `GET /api/v1/skills/employee-skills`: Fetch employee competency bridges with verification dates and status.

### Availability & Leave (`/api/v1/availability`)
- `GET /api/v1/availability`: List upcoming leave events (PTO, SICK_LEAVE, HOLIDAY, BENCH).
- `POST /api/v1/availability`: Schedule workforce leave or reserved capacity.

### Upskilling & Training (`/api/v1/training`)
- `GET /api/v1/training`: List active training programs and employee enrollments.
- `POST /api/v1/training`: Enroll employee in upskilling track.

---

## 📈 3. Planning & Resource Allocation

### Projects (`/api/v1/projects`)
- `GET /api/v1/projects`: Portfolio overview with status filtering (`ACTIVE`, `PIPELINE`, `DRAFT`, `COMPLETED`).
- `POST /api/v1/projects`: Create enterprise project engagement.
- `GET /api/v1/projects/{id}`: Get project details, staffing demands, and assigned resources.

### Demand Plans (`/api/v1/demand`)
- `GET /api/v1/demand`: Query weekly demand plan records by project, role, and priority.
- `POST /api/v1/demand`: Register structured project workforce requirement line.

### Allocations (`/api/v1/allocations`)
- `GET /api/v1/allocations`: List staffing allocations with employee and project relationships.
- `POST /api/v1/allocations`: Create resource assignment (logs `ALLOCATE` audit event).
- `PUT /api/v1/allocations/{id}`: Update allocation hours/dates, incrementing `version` (logs `UPDATE` audit event with previous state snapshot).
- `DELETE /api/v1/allocations/{id}`: Release or decommission allocation (logs `DELETE` audit event).

---

## 🧠 4. Analytics & Workforce Intelligence

### Capacity & Utilization (`/api/v1/analytics`)
- `GET /api/v1/analytics/capacity`: Organizational capacity rollup deducting part-time ratios and scheduled leaves.
- `GET /api/v1/analytics/utilization`: Workload distribution categorization (`UNDERUTILIZED` <70%, `NORMAL` 70-90%, `HIGH` 90-100%, `OVERALLOCATED` >100%).
- `GET /api/v1/analytics/gaps`: Unfulfilled skill demand analysis with severity tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).

### Demand Forecasting (`/api/v1/forecasting`)
- `GET /api/v1/forecasting/project-demand`: Forward project demand aggregated by week, role, and priority.
- `GET /api/v1/forecasting/historical-forecast`: Time-series forecasting models (Seasonal Naive, Moving Average, Exponential Smoothing, Random Forest) with MAE, RMSE, WAPE, and Forecast Bias metrics.

### AI Recommendations (`/api/v1/recommendations`)
- `GET /api/v1/recommendations`: Paginated list of historical staffing recommendations.
- `POST /api/v1/recommendations/generate`: Execute 5-step decision hierarchy (`REALLOCATE` -> `TRAIN` -> `HIRE` -> `RESCHEDULE`).
- `POST /api/v1/recommendations/{id}/approve`: Manager approval workflow, transition state to `ACCEPTED`, logs immutable `APPROVE` audit event.
- `POST /api/v1/recommendations/{id}/reject`: Manager rejection workflow, transition state to `REJECTED`, logs immutable `REJECT` audit event.

### Optimization (`/api/v1/optimization`)
- `POST /api/v1/optimization/solve`: Run Google OR-Tools CP-SAT integer programming solver to compute optimal multi-constraint allocation schedule and benchmark against greedy baseline.

---

## 🧪 5. Scenario Planning & What-If Simulations

### Endpoints (`/api/v1/scenarios`)
- `GET /api/v1/scenarios`: List historical what-if simulation runs.
- `POST /api/v1/scenarios`: Execute what-if scenario with configurable disruption parameters:
  - `demand_surge_percentage`: Global demand scaling (+50%, -20%).
  - `terminated_employee_ids`: Simulated workforce reductions or attrition.
  - `hypothetical_projects`: Injected pipeline projects with demanded skills.
  - `training_budget` & `hiring_budget`: Remodelled capital constraints.
- `GET /api/v1/scenarios/{id}`: Retrieve detailed simulation report including OR-Tools optimization results, greedy baseline comparison, and explainable infeasibility diagnoses.

> **Strict Baseline Protection Guarantee**:
> Scenario runs clone operational datasets entirely in memory. The baseline database records (`employees`, `projects`, `demand_plans`, `allocations`) remain strictly immutable during all scenario simulations.

---

## 🛡️ 6. Data Quality, Evaluation & Audit

### Exception Monitoring (`/api/v1/risks`)
- `GET /api/v1/risks/anomalies`: Active anomaly scan identifying:
  1. `OVERALLOCATION`: Allocation exceeds available hours.
  2. `STALE_SKILL`: Skills unverified for >730 days.
  3. `DUPLICATE_DEMAND`: Redundant delivery of matching demand keys.
  4. `OVERLAPPING_ALLOCATION`: Overlapping scheduling conflicts.

### Data Quality & Reproducibility (`/api/v1/quality`, `/api/v1/evaluation`)
- `GET /api/v1/quality/metrics`: Ground-truth evaluation metrics (Precision, Recall, F1-Score, Confusion Matrix).
- `POST /api/v1/evaluation/reproducibility`: Cryptographic SHA-256 reproducibility benchmark across synthetic seed datasets.

### Audit Trail (`/api/v1/audit`)
- `GET /api/v1/audit`: Paginated, immutable compliance audit log capturing actor IDs, timestamps, old/new snapshot JSON payloads, and reasons for all allocation and recommendation mutations.

