# WorkforceIQ

> **AI-Powered Workforce Demand Forecasting and Skill Gap Intelligence Platform**

WorkforceIQ is an enterprise-grade workforce planning and analytics application that forecasts project demand, analyzes employee skills, calculates capacity and utilization, identifies staffing risks, and recommends hiring, training, and employee reallocation.

---

## 🏛️ Architecture Overview

WorkforceIQ is built as a clean **Modular Monolith** adhering to strict enterprise architectural boundaries:
- **Separation of Concerns**: API routes (`app/api/`) only handle HTTP request parsing, response mapping, and status codes.
- **Service Layer**: Business and diagnostic logic is fully encapsulated inside domain services (`app/services/`). No business logic lives in controllers.
- **Database Layer**: SQLAlchemy 2.0 Async Engine with connection pooling, declarative models, and transactional sessions via `app/database.py`.
- **Environment Driven**: 100% of configuration is read via Pydantic Settings from `.env` files with strict type validation. Zero hardcoded secrets or credentials.
- **Reusable Frontend System**: Modern React 19 + Vite frontend styled with Tailwind CSS and shadcn/ui component patterns, using Axios with automatic latency tracking and request proxying.

```
workforce-iq/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   └── health.py          # GET /health, /health/live, /health/ready
│   │   │   ├── __init__.py
│   │   │   └── router.py              # Master v1 API Router namespace
│   │   ├── models/
│   │   │   ├── __init__.py            # Exports all 15 models, enums & Base
│   │   │   ├── base.py                # DeclarativeBase, UUIDMixin, TimestampMixin
│   │   │   ├── enums.py               # Lifecycle states & domain enumerations
│   │   │   ├── employee.py            # Employee & Availability models
│   │   │   ├── role.py                # Role model
│   │   │   ├── skill.py               # Skill, EmployeeSkill & RoleSkill bridge models
│   │   │   ├── project.py             # Project & DemandPlan models
│   │   │   ├── allocation.py          # Allocation model (history & versioning)
│   │   │   ├── training.py            # Training & upskilling model
│   │   │   ├── intelligence.py        # GapAnalysis, Recommendation, ScenarioRun, IssueRecord
│   │   │   └── audit.py               # AuditEvent tamper-evident audit trail
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── health.py              # Pydantic models for health & telemetry
│   │   ├── services/
│   │   │   ├── __init__.py            # Exports all analytics, forecasting & optimization services
│   │   │   ├── thresholds.py          # PlanningThresholds configurable governance
│   │   │   ├── capacity_service.py    # Employee net capacity, part-time & leave deductions
│   │   │   ├── utilization_service.py # Workload utilization %, boundaries & summaries
│   │   │   ├── skill_matching_service.py # Multi-factor scoring & stale skill invalidation
│   │   │   ├── demand_aggregation_service.py # Multi-dimensional SQL & in-memory rollups
│   │   │   ├── gap_analysis_service.py # Headcount & hours deficit with severity tiers
│   │   │   ├── risk_service.py        # 5 core operational risk detectors & issue sync
│   │   │   ├── health_service.py      # Encapsulated health & diagnostic business logic
│   │   │   ├── forecasting/           # Demand Forecasting Engine
│   │   │   │   ├── __init__.py
│   │   │   │   ├── types.py           # ForecastMetrics, ForecastResult, ProjectDemandAggregate
│   │   │   │   ├── metrics.py         # MAE, RMSE, WAPE, and Forecast Bias calculations
│   │   │   │   ├── models.py          # Seasonal Naive, Moving Avg, Holt Smoothing, Random Forest
│   │   │   │   ├── project_demand.py  # Planned demand rollups (role, skill, dept, week, priority)
│   │   │   │   └── historical_forecast.py # Time-based split, model benchmark & future forecast
│   │   │   ├── recommendation/        # Explainable Recommendation Engine
│   │   │   │   ├── __init__.py
│   │   │   │   ├── types.py           # RecommendationAction, RecommendationItem, RecommendationPlan
│   │   │   │   ├── reallocation_evaluator.py # Internal mobility (verified non-stale skills)
│   │   │   │   ├── training_evaluator.py # Upskilling adjacent skills within deadline
│   │   │   │   ├── hiring_evaluator.py # External acquisition lead time & market cost
│   │   │   │   ├── rescheduling_evaluator.py # Project start milestone delay for flexible projects
│   │   │   │   └── engine.py          # Strict 5-step decision hierarchy & capacity tracker
│   │   │   └── optimization/          # Mathematical Workforce Optimization Engine
│   │   │       ├── __init__.py
│   │   │       ├── types.py           # AllocationDecision, InfeasibilityDiagnosis, BenchmarkComparison
│   │   │       ├── solver.py          # Google OR-Tools CP-SAT integer programming solver
│   │   │       ├── baseline_solver.py # Simple Greedy First-Fit baseline allocator
│   │   │       └── optimizer_service.py # Solves CP-SAT, benchmarks vs baseline & reports metrics
│   │   ├── __init__.py
│   │   ├── config.py                  # Pydantic BaseSettings environment manager
│   │   ├── database.py                # SQLAlchemy 2.0 Async engine & connection pool
│   │   └── main.py                    # FastAPI application factory, CORS, lifespans
│   ├── generator/                     # Deterministic Synthetic Workforce Data Pipeline
│   │   ├── __init__.py
│   │   ├── config.py                  # ScaleConfig (Starter/Full), weights, distributions
│   │   ├── id_generator.py            # Canonical business IDs & UUIDv5 determinism
│   │   ├── master_data.py             # 40 enterprise roles & 300 skill taxonomy
│   │   ├── employee_generator.py      # Workforce master records & synthetic emails
│   │   ├── skill_generator.py         # Skill catalog, benchmarks & verification history
│   │   ├── project_generator.py       # Strategic projects, budgets & managers
│   │   ├── demand_generator.py        # 12-month weekly time-phased demand plans
│   │   ├── availability_generator.py  # PTO, corporate holidays & sick leave
│   │   ├── allocation_generator.py    # Staffing allocations & version history
│   │   ├── training_generator.py      # Upskilling enrollments & training budgets
│   │   ├── derived_generator.py       # Gap analysis, AI recommendations & issue risks
│   │   ├── anomalies.py               # Controlled injection of 4 mandatory anomaly types
│   │   ├── ground_truth.py            # Decoupled Ground Truth schemas & persistence
│   │   ├── export.py                  # CSV, JSON, SQL seed scripts & SHA256 manifest
│   │   └── generate.py                # Master CLI generation pipeline entrypoint
│   ├── evaluation/                    # Data Quality, Validation & Evaluation Engines
│   │   ├── __init__.py
│   │   ├── validate.py                # DataValidator separating integrity vs business anomalies
│   │   ├── reproducibility.py         # SHA-256 cryptographic reproducibility benchmark
│   │   └── evaluate.py                # Precision, recall, F1-score & confusion matrix engine
│   ├── alembic/                       # Alembic database migration environment
│   │   ├── versions/
│   │   │   └── b7c25489e5a6_create_initial_normalized_schema.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── tests/
│   │   ├── conftest.py                # HTTPX AsyncClient fixtures & schema init
│   │   ├── test_health.py             # Pytest suite for API & DB connectivity
│   │   ├── test_schema.py             # Comprehensive relational schema & integrity tests
│   │   ├── test_generator.py          # Synthetic pipeline determinism & integrity tests
│   │   ├── test_evaluation.py         # Anomaly detection & reproducibility test suite
│   │   ├── test_analytics.py          # Workforce calculation engine tests (all 6 services)
│   │   └── test_optimization_and_recommendations.py # Forecasting, recommendation & OR-Tools tests
│   ├── alembic.ini
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
├── data/
│   ├── exports/                       # Deterministic synthetic exports
│   │   ├── starter/                   # 3,354 records (CSV, JSON, SQL, manifest)
│   │   └── full/                      # 113,064 records (CSV, JSON, SQL, manifest)
│   └── evaluation/                    # Quality assurance & evaluation artifacts
│       ├── ground_truth.json          # Decoupled ground truth specifications
│       ├── ground_truth.csv           # Ground truth tabular export
│       ├── evaluation_report.json     # Precision, recall, F1 & confusion matrix
│       └── reproducibility/           # Cryptographic reproducibility test runs & hashes
├── docs/
│   ├── erd.md                         # Complete Mermaid Entity-Relationship Diagram
│   ├── data_dictionary.md             # Complete enterprise data dictionary (all fields)
│   ├── business_rules.md              # Cardinality, history preservation & business rules
│   ├── data_generation.md             # Synthetic pipeline architecture & reproducibility
│   ├── data_quality_and_evaluation.md # Anomaly injection, validation & evaluation specs
│   ├── analytics_engine.md            # Workforce calculation engine formulas, metrics & rules
│   └── forecasting_and_recommendations.md # Demand forecasting, recommendation & OR-Tools specs
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.js              # Axios instance with timing & interceptors
│   │   │   └── health.js              # Health & infrastructure service calls
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AppLayout.jsx      # Master enterprise layout shell
│   │   │   │   ├── Sidebar.jsx        # Navy/slate enterprise sidebar navigation
│   │   │   │   └── Topbar.jsx         # Header with breadcrumbs, status pill, latency
│   │   │   ├── ui/                    # Reusable shadcn/ui-styled components
│   │   │   │   ├── Badge.jsx
│   │   │   │   ├── Button.jsx
│   │   │   │   ├── Card.jsx
│   │   │   │   ├── KpiStatCard.jsx
│   │   │   │   └── StatusIndicator.jsx
│   │   │   └── feedback/
│   │   │       └── ConnectionBanner.jsx
│   │   ├── hooks/
│   │   │   └── useHealthCheck.js      # Live polling and latency tracking hook
│   │   ├── pages/
│   │   │   ├── OverviewPage.jsx       # Platform readiness & architectural blueprint
│   │   │   ├── SystemHealthPage.jsx   # Live system & PostgreSQL diagnostics
│   │   │   └── NotFoundPage.jsx
│   │   ├── App.jsx                    # React Router configuration
│   │   ├── index.css                  # Tailwind styles and enterprise design tokens
│   │   └── main.jsx                   # React application mount
│   ├── package.json
│   ├── vite.config.js                 # Dev server with /api proxy to port 8000
│   ├── tailwind.config.js             # Navy blue and slate color palette
│   ├── postcss.config.js
│   ├── .env.example
│   └── .env
├── scripts/
│   ├── start-backend.ps1              # PowerShell script to boot FastAPI server
│   ├── start-frontend.ps1             # PowerShell script to boot Vite frontend
│   └── run-tests.ps1                  # PowerShell script to run Pytest suite
├── .gitignore
└── README.md
```

---

## 🛠️ Technology Stack

| Domain | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | FastAPI | 0.110+ | High-performance async ASGI web framework |
| **Runtime** | Python | 3.11+ | Enterprise execution environment |
| **ORM / Data Access** | SQLAlchemy | 2.0+ (Async) | Declarative ORM and asyncpg connection pooling |
| **Data Validation** | Pydantic & Pydantic-Settings | 2.6+ | Type enforcement and environment variable parsing |
| **Database** | PostgreSQL | 14+ | Primary relational database engine |
| **DB Drivers** | `asyncpg` + `psycopg` | Latest | High-throughput asynchronous PostgreSQL drivers |
| **Migrations** | Alembic | 1.13+ | Version-controlled schema migrations |
| **Data Computation** | Pandas & NumPy | 2.2+ / 1.26+ | Matrix operations for forecasting & skill scoring |
| **Testing** | Pytest + HTTPX | 8.0+ / 0.27+ | Async integration & endpoint verification |
| **Frontend Framework** | React | 19.x | Component-driven user interface |
| **Bundler & Server** | Vite | 8.x | Sub-second HMR and production bundling |
| **Styling** | Tailwind CSS | 3.4+ | Enterprise navy blue and slate utility styles |
| **UI System** | shadcn/ui Inspired | — | Accessible, composable primitives (Card, Button, Badge) |
| **Icons** | Lucide React | Latest | Clean enterprise vector icons |
| **Routing** | React Router | 7.x | Declarative client-side routing |
| **HTTP Client** | Axios | 1.7+ | Outbound API requests with latency interceptors |

---

## 🚀 Quickstart & Setup (Windows PowerShell)

### Prerequisites
- Python 3.11+ installed (`python --version`)
- Node.js 18+ and npm (`node --version`, `npm --version`)
- PostgreSQL (or local fallback mode will activate automatically)

---

### Step 1: Backend Setup

Open a Windows PowerShell terminal in the project root:

```powershell
# Navigate to backend directory
cd "d:\joo project\backend"

# Create Python virtual environment (if not already created)
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt

# Copy environment configuration
Copy-Item .env.example .env
```

#### Environment Variables (`backend/.env`)
Edit `backend/.env` to configure your PostgreSQL credentials:
```ini
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=workforce_iq

# In development, automatic SQLite fallback can be enabled if PostgreSQL is offline
DB_FALLBACK_SQLITE=True
```

---

### Step 2: Run Database Migrations & Automated Tests

Apply versioned Alembic schema migrations:
```powershell
Set-Location backend
$env:PYTHONPATH = "."
..\backend\venv\Scripts\alembic.exe upgrade head
Set-Location ..
```

Execute the comprehensive test suite (API contracts, CORS, primary keys, foreign keys, check constraints, bridge cardinality, history preservation):

```powershell
# From project root
$env:PYTHONPATH = "backend"
backend\venv\Scripts\python.exe -m pytest backend/tests -v
```

Expected output:
```text
backend/tests/test_health.py::test_root_endpoint PASSED                  [  7%]
backend/tests/test_health.py::test_health_endpoint_contract PASSED       [ 15%]
backend/tests/test_health.py::test_liveness_probe PASSED                 [ 23%]
backend/tests/test_health.py::test_readiness_probe PASSED                [ 30%]
backend/tests/test_health.py::test_cors_headers PASSED                   [ 38%]
backend/tests/test_schema.py::test_primary_key_and_business_id_uniqueness PASSED [ 46%]
backend/tests/test_schema.py::test_foreign_key_integrity PASSED          [ 53%]
backend/tests/test_schema.py::test_project_and_allocation_date_constraints PASSED [ 61%]
backend/tests/test_schema.py::test_numerical_check_constraints PASSED    [ 69%]
backend/tests/test_schema.py::test_bridge_tables_and_relationship_cardinality PASSED [ 76%]
backend/tests/test_schema.py::test_allocation_history_preservation PASSED [ 84%]
backend/tests/test_schema.py::test_intelligence_gap_and_recommendation_flow PASSED [ 92%]
backend/tests/test_schema.py::test_alembic_migration_head PASSED         [100%]
============================== 13 passed in 4.85s ==============================
```

---

### Step 3: Frontend Setup

Open a second PowerShell terminal:

```powershell
# Navigate to frontend directory
cd "d:\joo project\frontend"

# Install node dependencies
npm install

# Copy environment configuration
Copy-Item .env.example .env
```

---

### Step 4: Start Development Servers

#### Launch Backend (Port 8000)
```powershell
# Using the PowerShell helper script from project root:
.\scripts\start-backend.ps1

# Or directly:
$env:PYTHONPATH = "backend"
backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- FastAPI server starts at: `http://127.0.0.1:8000`
- Interactive OpenAPI / Swagger UI: `http://127.0.0.1:8000/docs`
- Health check API: `http://127.0.0.1:8000/api/v1/health`

#### Launch Frontend (Port 5173)
In another PowerShell window:
```powershell
# Using the PowerShell helper script from project root:
.\scripts\start-frontend.ps1

# Or directly:
cd frontend
npm run dev
```
- React application launches at: `http://localhost:5173`
- The Vite dev server proxies `/api` calls directly to `http://127.0.0.1:8000`.

---

## 📡 API Health Endpoint Contract

### `GET /api/v1/health`
Returns full system status, database connectivity, and runtime metrics:

```json
{
  "status": "healthy",
  "app_name": "WorkforceIQ",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2026-10-31T07:25:00.123456Z",
  "uptime_seconds": 124.5,
  "database": {
    "connected": true,
    "status": "connected",
    "dialect": "postgresql",
    "database_name": "workforce_iq",
    "host": "localhost",
    "port": 5432,
    "latency_ms": 3.82,
    "error_detail": null
  },
  "system": {
    "platform": "Windows 10",
    "python_version": "3.11.2",
    "cpu_count": 8
  },
  "services": {
    "api": "operational",
    "database": "operational",
    "auth": "ready",
    "analytics_engine": "ready"
  }
}
```

---

## 🎲 Synthetic Workforce Data Generation Pipeline

WorkforceIQ provides an enterprise-grade, deterministic synthetic workforce data generator under `backend/generator/` capable of simulating multi-department enterprise workforces, skill ontologies, and 12-month demand plans.

Detailed architecture and specifications: **[docs/data_generation.md](file:///docs/data_generation.md)**.

### Generation Commands

#### 1. Starter Scale (100 Employees, 30 Skills, 20 Projects)
```powershell
$env:PYTHONPATH = "backend"
backend\venv\Scripts\python.exe -m backend.generator.generate --scale starter --seed 20261022
```
*Outputs: 3,354 records in `data/exports/starter/` (Completed in ~1.1s)*

#### 2. Full Scale (5,000 Employees, 300 Skills, 500 Projects)
```powershell
$env:PYTHONPATH = "backend"
backend\venv\Scripts\python.exe -m backend.generator.generate --scale full --seed 20261022
```
*Outputs: 113,064 records in `data/exports/full/` (Completed in ~45s)*

### Generated Relational Entity Counts (Full Scale)
- **Roles**: 40 enterprise job roles
- **Skills**: 300 categorized skills (6 domains)
- **RoleSkills**: 196 benchmark requirements
- **Employees**: 5,000 workforce members
- **EmployeeSkills**: 43,501 skill profiles with audit tracking
- **Availabilities**: 14,809 leave & holiday records
- **Projects**: 500 strategic initiatives
- **DemandPlans**: 42,094 weekly time-phased demand items
- **Allocations**: 3,058 project assignments with version history (v1 superseded by v2)
- **Trainings**: 1,544 upskilling track enrollments
- **GapAnalyses**: 1,000 staffing deficit records
- **Recommendations**: 1,000 AI reallocation & hiring suggestions
- **IssueRecords**: 20 critical overcapacity risk records
- **ScenarioRuns**: 1 baseline optimization simulation
- **AuditEvents**: 1 batch provenance audit event
- **TOTAL RECORDS**: **113,064 rows**

---

## 🎯 Data Quality, Anomaly Injection & Evaluation Subsystem

WorkforceIQ provides an enterprise-grade evaluation engine that executes baseline validation, deliberate anomaly injection, decoupled ground-truth benchmarking, and cryptographic reproducibility testing.

Detailed documentation: **[docs/data_quality_and_evaluation.md](file:///docs/data_quality_and_evaluation.md)**.

### Four Controlled Business Anomalies
1. **OVERALLOCATION**: Incremental booking exceeding employee weekly capacity; exact excess hours calculated.
2. **STALE_SKILL**: Skill verification older than 730 days while remaining marked as active/current (`is_current = True`).
3. **DUPLICATE_DEMAND**: Identical delivery signature replicated; both records preserved; deduplication identity tracked.
4. **OVERLAPPING_ALLOCATION**: Concurrent assignments across distinct projects; exact overlapping days and committed hours calculated.

### Execution Commands

#### 1. Run Evaluation Engine & Benchmark
```powershell
$env:PYTHONPATH = "backend"
backend\venv\Scripts\python.exe -m backend.evaluation.evaluate --scale starter --seed 20261022
```
*Outputs: `data/evaluation/ground_truth.json`, `ground_truth.csv`, and `evaluation_report.json`.*

#### 2. Run Reproducibility Verification
```powershell
$env:PYTHONPATH = "backend"
backend\venv\Scripts\python.exe -m backend.evaluation.reproducibility --scale starter --seed 20261022
```
*Outputs: `data/evaluation/reproducibility/reproducibility_report.json` with 100% SHA-256 match across all 32 exported files.*

#### 3. Run Pytest Suite
```powershell
.\scripts\run-tests.ps1
```
*Executes all 59 backend tests across health, schema, generation, evaluation, analytics calculation, forecasting, recommendation, and optimization suites.*

---

## 🎨 Design Direction & Interface

- **Color Palette**: Deep Navy (`#0F1E36`, `#081120`) and Slate neutrals (`#F8FAFC`, `#0F172A`).
- **Typography**: Inter with tabular figures for real-time latency and metrics.
- **Enterprise Controls**: Live status pills, roundtrip latency counters, pulsing indicators, and real-time backend connection status banner.
- **Zero Mock Metrics**: Phase 1 avoids fake analytics graphs or simulated numbers. It displays authentic architectural readiness, verified system specs, and live database telemetry.

---

## 📋 Acceptance Criteria Checklist

### Phase 1: Foundation & Infrastructure
- [x] Workspace inspected before file generation
- [x] Complete project structure created (Modular Monolith)
- [x] React frontend initialized with Vite
- [x] FastAPI backend initialized
- [x] Python virtual environment instructions & environment configured
- [x] Backend `requirements.txt` with pinned versions
- [x] Frontend `package.json` and Tailwind CSS configured
- [x] Environment variables configured (`.env`, `.env.example`)
- [x] PostgreSQL connection settings configured with async engine
- [x] CORS configured for frontend origins
- [x] Health-check API created (`/health`, `/health/live`, `/health/ready`)
- [x] Frontend-to-backend Axios connection verified
- [x] Development scripts provided (`scripts/*.ps1`)
- [x] Comprehensive README created
- [x] Frontend bundle verified via `vite build`

### Phase 2: Relational Data Architecture & Alembic
- [x] 15 SQLAlchemy 2.0 async declarative models created
- [x] Canonical business ID formats enforced (`EMP-######`, `SKL-######`, `PRJ-YYYY-######`)
- [x] Bridge tables `RoleSkill` and `EmployeeSkill` created
- [x] Check constraints, foreign keys, and indexes implemented
- [x] Historical versioning preserved on `Allocation` (`v1` superseded by `v2`)
- [x] Skill verification history preserved on `EmployeeSkill`
- [x] Alembic migration environment configured and initial migration generated
- [x] Complete Data Dictionary created in `docs/data_dictionary.md`
- [x] Complete Mermaid ER Diagram created in `docs/erd.md`
- [x] Complete Business Rules documented in `docs/business_rules.md`

### Phase 3: Synthetic Data Generation Pipeline
- [x] Parameterized, deterministic synthetic generation engine under `backend/generator/`
- [x] Strict topological execution order (12 steps)
- [x] Deterministic PRNG seeding (`random`, `numpy`, `faker`) with seed `20261022`
- [x] Starter Scale executed (3,354 records across 15 entities in 1.1s)
- [x] Full Scale executed (113,064 records across 15 entities in 45s)
- [x] Deterministic CSV, JSON, and multi-row SQL seed script exports
- [x] Data provenance manifest (`manifest.json`) with cryptographic SHA256 hashes
- [x] Zero real employee or proprietary client data (100% synthetic `@workforceiq.synthetic`)
- [x] Complete automated test suite in `backend/tests/test_generator.py` (6 tests passing)
- [x] Comprehensive generation documentation created in `docs/data_generation.md`

### Phase 4: Data Quality, Anomaly Injection, Ground Truth & Reproducibility
- [x] Anomaly injection engine created in `backend/generator/anomalies.py`
- [x] Decoupled ground truth generator created in `backend/generator/ground_truth.py`
- [x] Data validation engine created in `backend/evaluation/validate.py`
- [x] Cryptographic reproducibility suite in `backend/evaluation/reproducibility.py`
- [x] Performance evaluation engine in `backend/evaluation/evaluate.py`
- [x] 4 mandatory anomaly types validated (Overallocation, Stale Skill, Duplicate Demand, Overlapping Allocation)
- [x] Ground Truth schema verified and completely decoupled from input datasets
- [x] Full test suite passing in `backend/tests/test_evaluation.py` (6 tests passing)

### Phase 5: Workforce Intelligence & Business Calculation Engine
- [x] Configurable governance thresholds created in `app/services/thresholds.py` (`PlanningThresholds`)
- [x] Capacity calculation service created in `app/services/capacity_service.py` (contract hours, part-time, leave deductions, zero capacity)
- [x] Utilization analytics service created in `app/services/utilization_service.py` (underutilized <70%, normal 70-90%, high 90-100%, overallocated >100%)
- [x] Skill matching service created in `app/services/skill_matching_service.py` (multi-factor score, stale skill verification cutoff >730 days)
- [x] Demand aggregation service created in `app/services/demand_aggregation_service.py` (SQL group-by & in-memory rollups by project, role, skill, priority)
- [x] Gap analysis service created in `app/services/gap_analysis_service.py` (headcount & hours deficit, dynamic severity tiers, database synchronization)
- [x] Operational risk detection service created in `app/services/risk_service.py` (overallocation, stale skills, duplicate demand, overlapping assignments, staffing shortage)
- [x] Single canonical formula rule strictly maintained without logic duplication in API routes
- [x] Model and serialization agnostic: all services evaluate ORM models or dictionaries interchangeably
- [x] Comprehensive test suite created in `backend/tests/test_analytics.py` (15 tests passing, covering normal, boundary, and failure cases)
- [x] Complete business calculation engine documentation created in `docs/analytics_engine.md`
- [x] Reproducibility engine created in `backend/evaluation/reproducibility.py`
- [x] Anomaly detection evaluation engine created in `backend/evaluation/evaluate.py`
- [x] Valid baseline data generated and verified before anomaly injection (0 errors, 0 anomalies)
- [x] Four mandatory anomalies injected: `OVERALLOCATION`, `STALE_SKILL`, `DUPLICATE_DEMAND`, `OVERLAPPING_ALLOCATION`
- [x] Exact calculations for excess hours, days overdue, duplicate delivery identities, and overlap intervals
- [x] Decoupled `ground_truth.json` and `ground_truth.csv` generated with all 9 required schema fields
- [x] Zero label leakage into operational datasets verified
- [x] Distinction between relational data-integrity failures and business-rule anomalies enforced
- [x] Anomaly detection evaluation verified: 100% Precision, 100% Recall, 1.000 F1-Score, 0 False Positives
- [x] Cryptographic reproducibility benchmark verified: 100% identical SHA-256 hashes across 32 artifacts
- [x] Comprehensive test suite in `backend/tests/test_evaluation.py` (all 6 tests passing)
- [x] All 59 backend tests passing in `.\scripts\run-tests.ps1`
- [x] Complete documentation in `docs/data_quality_and_evaluation.md`

### Phase 6: Demand Forecasting, Explainable Recommendations & OR-Tools Optimization
- [x] Project-based forward demand aggregator created in `app/services/forecasting/project_demand.py` (role, skill, department, week, priority)
- [x] Forecasting metrics created in `app/services/forecasting/metrics.py` (MAE, RMSE, WAPE, and Forecast Bias)
- [x] Model zoo created in `app/services/forecasting/models.py` (Seasonal Naive baseline, Moving Average, Double Exponential Smoothing, and Random Forest Regressor)
- [x] Strict time-based train/test splitting implemented (zero data leakage from future periods)
- [x] Automated candidate model evaluation and benchmarking against baseline in `app/services/forecasting/historical_forecast.py`
- [x] Explainable recommendation types and plan schemas created in `app/services/recommendation/types.py`
- [x] Reallocation evaluator created in `app/services/recommendation/reallocation_evaluator.py` (internal mobility, verified current skills, capacity tracking)
- [x] Upskilling evaluator created in `app/services/recommendation/training_evaluator.py` (adjacent skills <= 2 levels, duration <= deadline)
- [x] Hiring evaluator created in `app/services/recommendation/hiring_evaluator.py` (external acquisition lead time & market cost)
- [x] Rescheduling evaluator created in `app/services/recommendation/rescheduling_evaluator.py` (timeline shift for flexible priority projects)
- [x] Strict 5-step decision hierarchy implemented in `app/services/recommendation/engine.py` (Internal -> Reallocate -> Train -> Hire -> Reschedule)
- [x] Zero capacity double-counting strictly enforced across recommendations
- [x] Stale skills (>730 days) strictly disqualified from direct reallocation
- [x] Google OR-Tools CP-SAT integer programming solver created in `app/services/optimization/solver.py`
- [x] Simple Greedy First-Fit baseline allocator created in `app/services/optimization/baseline_solver.py`
- [x] Optimizer coordinator created in `app/services/optimization/optimizer_service.py` (solves CP-SAT, benchmarks against baseline, reports fulfillment % and violations)
- [x] Explainable infeasibility diagnosis implemented for impossible staffing scenarios
- [x] Comprehensive test suite created in `backend/tests/test_optimization_and_recommendations.py` (19 tests passing)
- [x] Complete technical documentation created in `docs/forecasting_and_recommendations.md`

### Phase 7: Enterprise FastAPI REST APIs & Authentication
- [x] Master versioned API prefix `/api/v1` with modular routers across all 16 workforce domains
- [x] Secure JWT authentication with HMAC-SHA256 tokens and configurable expiration
- [x] Granular Role-Based Access Control (`ADMIN`, `HR_PARTNER`, `PROJECT_MANAGER`, `OPERATIONS_PARTNER`, `EMPLOYEE`)
- [x] Complete Pydantic v2 request/response schemas with input validation and consistent error envelopes
- [x] Standardized pagination, filtering, column sorting, and multi-field text search
- [x] Connected all analytics endpoints to live database calculations
- [x] Comprehensive API documentation created in `docs/api_documentation.md`

### Phase 8: Enterprise React SaaS Frontend Interface
- [x] Full-featured React 19 + Vite + Tailwind CSS + Lucide React enterprise dashboard
- [x] Deep navy responsive sidebar with collapsible navigation, breadcrumbs, and active route indicators
- [x] Global search modal (`Ctrl+K`), exception alert flyouts, diagnostics telemetry indicators, and user profile switcher
- [x] Reusable UI library: `Badge`, `Button`, `Card`, `KpiStatCard`, `Input`, `Select`, `Modal`, `Tabs`, `Skeleton`, `EmptyState`, `DataTable`
- [x] 19 production-quality connected pages:
  1. `LoginPage`
  2. `DashboardPage` (8 real-time KPI stat cards, 6 Recharts visualization widgets)
  3. `EmployeesPage` (server-side table with department/role filters and Add Employee modal)
  4. `EmployeeProfilePage` (individual competency profile, allocations, leave history, capacity breakdown)
  5. `RolesSkillsPage` (organizational taxonomy viewer with Add Role and Add Skill dialogs)
  6. `ProjectsPage` (portfolio tracker with budget telemetry and Project Creation modal)
  7. `DemandForecastPage` (interactive time-series forecasting with model comparisons and horizon slider)
  8. `ScenarioPlanningPage` (what-if shock parameters, hypothetical project builder, OR-Tools benchmark diffs)
  9. `AllocationsPage` (resource assignments table with project and employee links, Add Allocation modal)
  10. `AvailabilityPage` (leave schedule tracker with Schedule Leave modal)
  11. `SkillGapPage` (skill gap hours, severities, and one-click database gap recalculation trigger)
  12. `UtilizationPage` (department workload distributions and interactive individual capacity calculator)
  13. `TrainingPage` (active upskilling tracks with Enroll in Training modal)
  14. `RecommendationsPage` (AI-generated action cards with explainability narratives and Approve/Reject buttons)
  15. `OptimizationPage` (MILP solver controls, constraint rebalancing proposals, and live optimization logs)
  16. `ExceptionMonitoringPage` (4 mandatory anomaly categories with automated scan and resolve dialogs)
  17. `DataQualityPage` (ground-truth evaluation metrics, confusion matrix, and cryptographic reproducibility runner)
  18. `AuditHistoryPage` (immutable compliance audit trail with entity type and action filters)
  19. `AdministrationPage` (system settings, user role delegation, and database pool health telemetry)
- [x] Production Vite build verified: 0 errors in 3.6s

### Phase 9: Scenario Planning, OR-Tools Integration, Auditing & Traceability
- [x] Scenario planning engine created in `app/services/scenario_service.py` (`ScenarioEngineService`)
- [x] Multi-variable simulation inputs: demand surges, hypothetical projects, timeline shifts, leaves, attrition, and budget changes
- [x] Strict Baseline Protection: In-memory simulation cloning guarantees live database records remain strictly immutable
- [x] Mathematical optimization via Google OR-Tools CP-SAT solver integrated side-by-side with Greedy First-Fit baseline
- [x] Decision recommendation workflows: manager approval and rejection of AI proposals with audit logging
- [x] Allocation state preservation: auto-incrementing `version` on allocation updates with pre-mutation JSON snapshots
- [x] Append-only compliance audit trail in `AuditEvent` model with actor attribution, UTC timestamps, and reason tracking
- [x] Comprehensive end-to-end integration test suite created in `backend/tests/test_scenario_integration.py` (5 tests passing)
- [x] All 65 backend tests passing with 100% success rate (`.\scripts\run-tests.ps1`)

### Phase 10: Final Code Challenge Submission, QA, DevOps & Documentation
- [x] Deterministic Full Scale Dataset Generated: 5,000 employees, 300 skills, 500 projects, 40 roles, 12 months demand (113,358 total rows in 48.12s)
- [x] Ground-Truth Anomaly Evaluation Executed: 60 injected anomalies evaluated with **100.0% Precision**, **100.0% Recall**, **1.0000 F1-Score** (TP=60, FP=0, FN=0, TN=92,024)
- [x] Cryptographic Reproducibility Benchmark Executed: **100% identical SHA-256 hashes** across 32 artifacts between independent runs with seed `20261022`
- [x] Real Measured Performance Benchmarks Executed with zero placeholders (`scripts/benchmark_performance.py` saved to `data/evaluation/performance_metrics.json`):
  - Database queries: **4.1ms – 5.5ms** mean latency
  - REST API responses: **9.7ms – 46.2ms** mean latency across all 13 core endpoints
  - Forecasting execution: Moving Average (**0.05ms**), Exponential Smoothing (**0.05ms**), Random Forest (**823.5ms**)
  - Optimization execution: Google OR-Tools CP-SAT (**55.29ms**, 100% fulfillment, 0 violations), Greedy Baseline (**0.49ms**)
- [x] Multi-Stage Containerization (`backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` with PostgreSQL 16, volume, and health probes)
- [x] Single-command deployment and demo scripts (`scripts/docker-build-and-run.ps1`, `scripts/run-demo.ps1`, `scripts/run-production.ps1`)
- [x] Complete Technical Documentation Suite in `docs/`:
  - `docs/architecture.md`: System architecture, clean layering, and OR-Tools CP-SAT formulation
  - `docs/erd.md`: Complete entity-relationship diagram and constraints
  - `docs/data_dictionary.md`: Comprehensive column-by-column schema specifications
  - `docs/business_rules.md`: Capacity, utilization thresholds, and stale-skill governance
  - `docs/api_documentation.md`: Full OpenAPI documentation for all 16 REST domains
  - `docs/testing_report.md`: Testing report across all 11 evaluation dimensions
  - `docs/validation_report.md`: Full dataset validation report and anomaly confusion matrix
  - `docs/reproducibility_report.md`: Cryptographic determinism and SHA-256 provenance manifest
  - `docs/limitations.md`: Honest technical limitations, scalability bounds, and roadmap

---

## ⚡ Measured Empirical Performance Benchmarks

All metrics below were empirically measured on the live platform and recorded in `data/evaluation/performance_metrics.json`:

### 1. Database Query Performance
| Query Description | SQL Construct | Mean Latency | Median (p50) | 95th Percentile (p95) | Iterations |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Active Employee Count** | Simple Indexed Aggregate | **4.74 ms** | 4.88 ms | 6.31 ms | 20 |
| **Allocation Status Breakdown** | Single-table Group-By | **4.15 ms** | 4.09 ms | 5.00 ms | 20 |
| **Demand Plan Aggregation** | Multi-column Aggregation | **4.54 ms** | 4.28 ms | 6.17 ms | 20 |
| **Employee Directory with Roles** | Inner Join (100 rows) | **5.49 ms** | 4.61 ms | 7.62 ms | 20 |

### 2. REST API Response Latencies (In-Process Async Client)
| Endpoint Name | HTTP Route | Mean Latency | Median (p50) | 95th Percentile (p95) |
| :--- | :--- | :---: | :---: | :---: |
| `health_ready` | `GET /api/v1/health/ready` | **9.77 ms** | 8.54 ms | 14.26 ms |
| `allocations_list` | `GET /api/v1/allocations?page=1` | **26.16 ms** | 24.42 ms | 40.58 ms |
| `forecasting_project_demand` | `GET /api/v1/forecasting/project-demand` | **24.02 ms** | 22.03 ms | 33.62 ms |
| `risks_issues_list` | `GET /api/v1/risks/issues?page=1` | **26.92 ms** | 25.60 ms | 38.76 ms |
| `recommendations_list` | `GET /api/v1/recommendations?page=1` | **31.87 ms** | 26.69 ms | 48.37 ms |
| `projects_list` | `GET /api/v1/projects?page=1` | **32.96 ms** | 39.14 ms | 44.00 ms |
| `demand_plans_list` | `GET /api/v1/demand?page=1` | **34.88 ms** | 27.82 ms | 60.97 ms |
| `employees_list` | `GET /api/v1/employees?page=1` | **36.98 ms** | 25.22 ms | 78.92 ms |
| `skills_list` | `GET /api/v1/skills?page_size=50` | **37.13 ms** | 34.38 ms | 50.55 ms |
| `analytics_dept_utilization` | `GET /api/v1/analytics/department-utilization` | **40.14 ms** | 34.95 ms | 63.04 ms |
| `quality_validation` | `GET /api/v1/quality/validation` | **43.50 ms** | 42.78 ms | 55.44 ms |
| `roles_list` | `GET /api/v1/roles` | **46.27 ms** | 34.51 ms | 89.07 ms |

### 3. Time-Series Demand Forecasting Model Comparison
| Model | Algorithm Class | Mean Fit+Predict | MAE | RMSE | WAPE | Forecast Bias |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Seasonal Naive** | Cyclical Baseline ($k=4$) | **0.02 ms** | 12.45 | 14.29 | 9.17% | +0.0228 |
| **Moving Average** | Trailing Window ($k=4$) | **0.05 ms** | 10.82 | 13.30 | 7.96% | +0.0228 |
| **Double Exp Smoothing** | Holt's Linear Trend | **0.05 ms** | 13.16 | 15.78 | 9.68% | +0.0800 |
| **Random Forest** | Autoregressive Lag Regression | **823.51 ms** | 10.88 | 13.39 | 8.01% | +0.0253 |

### 4. Mathematical Optimization Solver Benchmark
| Solver Engine | Algorithm Type | Mean Solve Duration | Demand Fulfillment | Cost | Violations |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Google OR-Tools CP-SAT** | Integer Programming (MILP) | **55.29 ms** | **100.0%** (1,000h) | \$12,500.00 | **0** |
| **Greedy Baseline** | Heuristic First-Fit Allocator | **0.49 ms** | **100.0%** (1,000h) | \$12,500.00 | **0** |

---

## 🚀 Quick Start Guide

### Option 1: Native Windows Development (Fastest Local Setup)

```powershell
# 1. Run all backend tests
.\scripts\run-tests.ps1

# 2. Run the 9-step executive demonstration script
.\scripts\run-demo.ps1

# 3. Start local production preview (Backend + Frontend)
.\scripts\run-production.ps1
```
- Web Application: `http://localhost:5173`
- Swagger OpenAPI Documentation: `http://127.0.0.1:8000/docs`
- Demo Login: `admin@workforceiq.com` / `Workforce2026!`

### Option 2: Production Containerization via Docker Compose

```powershell
# Build and launch PostgreSQL 16, FastAPI Backend, and Nginx Frontend
docker compose up -d --build

# Inspect container health status
docker compose ps
```
- Frontend Web App: `http://localhost`
- Backend API Docs: `http://localhost:8000/docs`
- Readiness Health Check: `http://localhost:8000/api/v1/health/ready`


