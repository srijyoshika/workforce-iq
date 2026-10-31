"""
WorkforceIQ Forecasting, Recommendation, and Optimization Test Suite.

Verifies:
1. Forecasting:
   - Time-based train/test splitting (zero data leakage from future).
   - Metrics: MAE, RMSE, WAPE, and Forecast Bias.
   - Models: Seasonal Naive, Moving Average, Exponential Smoothing, and Random Forest.
   - Automated model comparison against baseline.
   - Project-based planned demand aggregation across role, skill, department, week, and priority.
2. Recommendation Engine:
   - REALLOCATE (eligible internal with verified current skill and available capacity).
   - TRAIN (adjacent skill upskilling within deadline window).
   - HIRE (external acquisition when internal supply is exhausted).
   - RESCHEDULE (timeline shift for flexible priority projects when deadlines are breached).
   - Stale skill guard: Stale skills (>730d) strictly excluded from direct reallocation.
   - Capacity exclusivity: Zero capacity double-counting across projects.
   - Impossible staffing scenarios: Transparent explainability and diagnostic warnings.
3. Optimization Engine:
   - Google OR-Tools CP-SAT mathematical programming solver.
   - Capacity, skill proficiency, status, and deadline constraints.
   - Explainable infeasibility diagnosis without silently discarding constraints.
   - Comparative benchmark against Greedy Baseline allocator.
"""

from datetime import date, datetime, timedelta, timezone
import pytest

from app.services.forecasting import (
    ExponentialSmoothingModel,
    HistoricalDemandForecastService,
    ModelComparisonItem,
    MovingAverageModel,
    ProjectDemandAggregator,
    RandomForestForecastModel,
    SeasonalNaiveModel,
    calculate_forecast_metrics,
)
from app.services.optimization import (
    GreedyBaselineSolver,
    OptimizationStatus,
    OrToolsWorkforceSolver,
    WorkforceOptimizerService,
)
from app.services.recommendation import (
    RecommendationAction,
    RecommendationEngine,
    RecommendationItem,
    RecommendationPlan,
)
from app.services.skill_matching_service import CandidateMatch


# =============================================================================
# 1. FORECASTING TESTS
# =============================================================================

def test_forecast_metrics_calculation():
    """Verify calculation of MAE, RMSE, WAPE, and Forecast Bias."""
    y_true = [100.0, 120.0, 110.0, 130.0]
    y_pred = [105.0, 115.0, 115.0, 125.0]

    # errors: +5, -5, +5, -5 -> abs_errors: 5, 5, 5, 5
    # total actual = 460.0
    # total abs error = 20.0
    # total error = 0.0
    metrics = calculate_forecast_metrics(y_true, y_pred)

    assert metrics.mae == 5.0
    assert metrics.rmse == 5.0
    assert metrics.wape == round(20.0 / 460.0, 4)
    assert metrics.bias == 0.0
    assert metrics.sample_size == 4


def test_forecast_metrics_positive_bias():
    """Verify that consistent over-forecasting yields positive bias."""
    y_true = [50.0, 50.0]
    y_pred = [60.0, 60.0]
    metrics = calculate_forecast_metrics(y_true, y_pred)
    assert metrics.mae == 10.0
    assert metrics.bias == 0.2  # (120 - 100) / 100 = +20%


def test_time_based_split_no_leakage():
    """Verify that time-based splitting strictly preserves chronological order with zero leakage."""
    series = [float(i) for i in range(20)]  # 0.0 to 19.0
    train, test = HistoricalDemandForecastService.time_based_split(series, test_ratio=0.25)

    assert len(train) == 15
    assert len(test) == 5
    assert max(train) < min(test), "Training observations must strictly precede test observations"
    assert train == [float(i) for i in range(15)]
    assert test == [float(i) for i in range(15, 20)]


def test_seasonal_naive_baseline_model():
    """Verify Seasonal Naive baseline repeats values from identical seasonal lag."""
    # 4-week seasonal pattern: [10, 20, 30, 40, 12, 22, 32, 42]
    history = [10.0, 20.0, 30.0, 40.0, 12.0, 22.0, 32.0, 42.0]
    model = SeasonalNaiveModel(seasonality=4)
    model.fit(history)

    preds = model.predict(horizon=4)
    # Expected: repeats last 4 observations [12.0, 22.0, 32.0, 42.0]
    assert preds == [12.0, 22.0, 32.0, 42.0]


def test_moving_average_model():
    """Verify Moving Average calculates mean of trailing window."""
    history = [10.0, 20.0, 30.0, 40.0]
    model = MovingAverageModel(window_size=3)
    model.fit(history)

    preds = model.predict(horizon=3)
    # Trailing 3 are [20.0, 30.0, 40.0] -> mean = 30.0
    assert preds == [30.0, 30.0, 30.0]


def test_exponential_smoothing_model():
    """Verify Holt's linear exponential smoothing captures upward trend."""
    # Strictly increasing linear trend
    history = [10.0, 20.0, 30.0, 40.0, 50.0]
    model = ExponentialSmoothingModel(alpha=0.5, beta=0.5)
    model.fit(history)

    preds = model.predict(horizon=3)
    assert len(preds) == 3
    # Consecutive forward predictions must increase
    assert preds[0] < preds[1] < preds[2]


def test_random_forest_forecast_model():
    """Verify Random Forest autoregressive forecast executes without error."""
    # Synthetic series with 24 periods
    history = HistoricalDemandForecastService.generate_synthetic_history(periods=24, seed=20261022)
    model = RandomForestForecastModel(n_estimators=20, random_state=20261022)
    model.fit(history)

    preds = model.predict(horizon=4)
    assert len(preds) == 4
    for p in preds:
        assert p >= 0.0


def test_historical_forecast_workflow_and_baseline_comparison():
    """Verify end-to-end forecasting pipeline: training, baseline comparison, and selection."""
    history = HistoricalDemandForecastService.generate_synthetic_history(periods=40, seed=20261022)
    result = HistoricalDemandForecastService.forecast_demand(
        series=history,
        prediction_horizon=6,
        series_identifier="Role:DataEngineer",
        start_period_label="2026W45",
        seasonality=4,
    )

    assert result.series_identifier == "Role:DataEngineer"
    assert len(result.prediction_periods) == 6
    assert len(result.forecast_values) == 6
    assert result.selected_model_name is not None
    assert result.evaluation_metrics.wape >= 0.0

    # Ensure baseline is included in comparison benchmarks
    baseline_bench = next((b for b in result.comparison_benchmarks if b.is_baseline), None)
    assert baseline_bench is not None
    assert baseline_bench.model_name == "Seasonal Naive Baseline"
    assert len(result.comparison_benchmarks) >= 3


def test_project_demand_aggregation():
    """Verify forward planned demand aggregation across role, skill, department, week, and priority."""
    demands = [
        {
            "id": "DEM-1",
            "project_id": "PRJ-101",
            "role_id": "ROL-CLOUD",
            "primary_skill_id": "SKL-AWS",
            "start_date": date(2026, 11, 2),
            "end_date": date(2026, 11, 8),
            "required_headcount": 2,
            "required_hours": 80.0,
            "priority": 1,
            "status": "COMMITTED",
        },
        {
            "id": "DEM-2",
            "project_id": "PRJ-102",
            "role_id": "ROL-CLOUD",
            "primary_skill_id": "SKL-AWS",
            "start_date": date(2026, 11, 2),
            "end_date": date(2026, 11, 8),
            "required_headcount": 1,
            "required_hours": 40.0,
            "priority": 1,
            "status": "COMMITTED",
        },
    ]
    projects = [
        {"id": "PRJ-101", "name": "Cloud Native Migration", "department": "Platform"},
        {"id": "PRJ-102", "name": "Infra Modernization", "department": "Platform"},
    ]

    aggregates = ProjectDemandAggregator.aggregate_project_demands(
        demand_plans=demands,
        projects=projects,
    )

    assert len(aggregates) == 1
    agg = aggregates[0]
    assert agg.role_id == "ROL-CLOUD"
    assert agg.skill_id == "SKL-AWS"
    assert agg.department == "Platform"
    assert agg.total_required_headcount == 3
    assert agg.total_required_hours == 120.0
    assert agg.active_projects_count == 2


# =============================================================================
# 2. RECOMMENDATION ENGINE TESTS
# =============================================================================

def test_recommendation_reallocate():
    """Verify REALLOCATE is generated when internal employee has verified current skill and capacity."""
    as_of = date(2026, 10, 22)
    gap = {
        "demand_plan_id": "DEM-REALLOC",
        "project_id": "PRJ-ALPHA",
        "skill_id": "SKL-PYTHON",
        "skill_name": "Python",
        "start_date": date(2026, 11, 15),
        "unfilled_demand_hours": 40.0,
    }

    # Qualified candidate with 40h available capacity
    candidates = [
        CandidateMatch(
            employee_id="EMP-AVAIL",
            business_id="EMP-000001",
            employee_name="Alice Smith",
            role_id="ROL-DEV",
            department="Engineering",
            skill_id="SKL-PYTHON",
            skill_name="Python",
            assessed_proficiency=4,
            effective_certified_proficiency=4,
            required_proficiency=3,
            proficiency_gap=0,
            verification_status="ASSESSMENT_CERTIFIED",
            verified_at="2026-09-01",
            is_stale=False,
            available_hours=40.0,
            allocated_hours=0.0,
            remaining_capacity_hours=40.0,
            is_fully_qualified=True,
            match_score=95.0,
            calculated_at="2026-10-22T00:00:00Z",
            rule_version="1.0.0",
        )
    ]

    recs = RecommendationEngine.generate_recommendations_for_gap(
        gap=gap,
        candidate_pool=candidates,
        committed_capacities={},
        as_of_date=as_of,
        project_priority=1,
    )

    assert len(recs) == 1
    rec = recs[0]
    assert rec.action == RecommendationAction.REALLOCATE
    assert "Alice Smith" in rec.explanation
    assert rec.expected_shortage_reduction_hours == 40.0
    assert rec.deadline_feasibility is True
    assert rec.expected_cost == 500.0


def test_recommendation_train():
    """Verify TRAIN is generated when internal employee has adjacent skill suitable for upskilling."""
    as_of = date(2026, 10, 22)
    gap = {
        "demand_plan_id": "DEM-TRAIN",
        "project_id": "PRJ-BETA",
        "skill_id": "SKL-K8S",
        "skill_name": "Kubernetes",
        "start_date": date(2026, 11, 30),  # 39 days to deadline
        "unfilled_demand_hours": 40.0,
    }

    # Candidate has level 2, requires level 3 (deficit = 1 level; 14 days training)
    candidates = [
        CandidateMatch(
            employee_id="EMP-LEARNER",
            business_id="EMP-000002",
            employee_name="Bob Jones",
            role_id="ROL-DEV",
            department="Engineering",
            skill_id="SKL-K8S",
            skill_name="Kubernetes",
            assessed_proficiency=2,
            effective_certified_proficiency=2,
            required_proficiency=3,
            proficiency_gap=1,
            verification_status="MANAGER_VERIFIED",
            verified_at="2026-08-01",
            is_stale=False,
            available_hours=40.0,
            allocated_hours=0.0,
            remaining_capacity_hours=40.0,
            is_fully_qualified=False,  # Not qualified today, but trainable
            match_score=65.0,
            calculated_at="2026-10-22T00:00:00Z",
            rule_version="1.0.0",
        )
    ]

    recs = RecommendationEngine.generate_recommendations_for_gap(
        gap=gap,
        candidate_pool=candidates,
        committed_capacities={},
        as_of_date=as_of,
        project_priority=2,
    )

    assert len(recs) == 1
    rec = recs[0]
    assert rec.action == RecommendationAction.TRAIN
    assert "Bob Jones" in rec.explanation
    assert rec.estimated_time_to_resolve_days == 14
    assert rec.deadline_feasibility is True
    assert rec.expected_cost == 2500.0


def test_recommendation_hire():
    """Verify HIRE is generated when candidate pool has no qualified or trainable employees."""
    as_of = date(2026, 10, 22)
    gap = {
        "demand_plan_id": "DEM-HIRE",
        "project_id": "PRJ-GAMMA",
        "skill_id": "SKL-RUST",
        "skill_name": "Rust Systems",
        "start_date": date(2026, 12, 15),  # 54 days to deadline
        "unfilled_demand_hours": 40.0,
    }

    recs = RecommendationEngine.generate_recommendations_for_gap(
        gap=gap,
        candidate_pool=[],  # No internal talent
        committed_capacities={},
        as_of_date=as_of,
        project_priority=1,
    )

    assert len(recs) == 1
    rec = recs[0]
    assert rec.action == RecommendationAction.HIRE
    assert rec.expected_cost == 12000.0
    assert rec.estimated_time_to_resolve_days == 45
    assert rec.deadline_feasibility is True


def test_recommendation_reschedule_on_tight_deadline():
    """Verify RESCHEDULE is generated when hiring lead time breaches deadline on flexible project."""
    as_of = date(2026, 10, 22)
    gap = {
        "demand_plan_id": "DEM-RESCHED",
        "project_id": "PRJ-FLEX",
        "skill_id": "SKL-AI",
        "skill_name": "Deep Learning",
        "start_date": date(2026, 11, 1),  # Only 10 days away; hiring takes 45 days
        "unfilled_demand_hours": 40.0,
    }

    recs = RecommendationEngine.generate_recommendations_for_gap(
        gap=gap,
        candidate_pool=[],  # No internal talent
        committed_capacities={},
        as_of_date=as_of,
        project_priority=3,  # Non-critical flexible project
    )

    # Must contain HIRE and complementary RESCHEDULE
    actions = [r.action for r in recs]
    assert RecommendationAction.HIRE in actions
    assert RecommendationAction.RESCHEDULE in actions

    resched_rec = next(r for r in recs if r.action == RecommendationAction.RESCHEDULE)
    assert resched_rec.estimated_time_to_resolve_days >= 14
    assert resched_rec.deadline_feasibility is True


def test_stale_skills_excluded_from_reallocation():
    """
    CRITICAL RULE: Employees with stale skills must NOT be recommended for reallocation.
    Must be directed to training / recertification.
    """
    as_of = date(2026, 10, 22)
    gap = {
        "demand_plan_id": "DEM-STALE",
        "project_id": "PRJ-SEC",
        "skill_id": "SKL-SEC",
        "skill_name": "Cybersecurity",
        "start_date": date(2026, 11, 20),
        "unfilled_demand_hours": 40.0,
    }

    # Candidate holds skill level 5, but verified 800 days ago (> 730 days -> STALE)
    stale_cand = CandidateMatch(
        employee_id="EMP-STALE",
        business_id="EMP-000099",
        employee_name="Charlie Stale",
        role_id="ROL-SEC",
        department="Security",
        skill_id="SKL-SEC",
        skill_name="Cybersecurity",
        assessed_proficiency=5,
        effective_certified_proficiency=0,  # Zeroed out
        required_proficiency=3,
        proficiency_gap=3,
        verification_status="ASSESSMENT_CERTIFIED",
        verified_at="2024-08-01",
        is_stale=True,  # Stale
        available_hours=40.0,
        allocated_hours=0.0,
        remaining_capacity_hours=40.0,
        is_fully_qualified=False,
        match_score=45.0,
        calculated_at="2026-10-22T00:00:00Z",
        rule_version="1.0.0",
    )

    recs = RecommendationEngine.generate_recommendations_for_gap(
        gap=gap,
        candidate_pool=[stale_cand],
        committed_capacities={},
        as_of_date=as_of,
        project_priority=1,
    )

    # Must NOT be REALLOCATE; must be TRAIN (recertification)
    actions = [r.action for r in recs]
    assert RecommendationAction.REALLOCATE not in actions
    assert RecommendationAction.TRAIN in actions
    assert "Charlie Stale" in recs[0].explanation


def test_capacity_not_double_counted():
    """Verify that committed capacity is tracked so an employee is not double-counted across gaps."""
    as_of = date(2026, 10, 22)
    gap1 = {
        "demand_plan_id": "DEM-G1",
        "project_id": "PRJ-1",
        "skill_id": "SKL-DEV",
        "skill_name": "Dev",
        "start_date": date(2026, 12, 15),  # 54 days away (>45d hire lead time)
        "unfilled_demand_hours": 40.0,
    }
    gap2 = {
        "demand_plan_id": "DEM-G2",
        "project_id": "PRJ-2",
        "skill_id": "SKL-DEV",
        "skill_name": "Dev",
        "start_date": date(2026, 12, 15),  # 54 days away (>45d hire lead time)
        "unfilled_demand_hours": 40.0,
    }

    # Only one employee with 40h capacity
    cand = CandidateMatch(
        employee_id="EMP-SOLO",
        business_id="EMP-000001",
        employee_name="Solo Performer",
        role_id="ROL-DEV",
        department="Engineering",
        skill_id="SKL-DEV",
        skill_name="Dev",
        assessed_proficiency=4,
        effective_certified_proficiency=4,
        required_proficiency=3,
        proficiency_gap=0,
        verification_status="ASSESSMENT_CERTIFIED",
        verified_at="2026-09-01",
        is_stale=False,
        available_hours=40.0,
        allocated_hours=0.0,
        remaining_capacity_hours=40.0,
        is_fully_qualified=True,
        match_score=95.0,
        calculated_at="2026-10-22T00:00:00Z",
        rule_version="1.0.0",
    )

    plan = RecommendationEngine.generate_portfolio_plan(
        gaps=[gap1, gap2],
        candidate_pools_by_gap={"DEM-G1": [cand], "DEM-G2": [cand]},
        as_of_date=as_of,
    )

    assert len(plan.recommendations) == 2
    r1 = plan.recommendations[0]
    r2 = plan.recommendations[1]

    # Gap 1 takes the 40h capacity of Solo Performer
    assert r1.action == RecommendationAction.REALLOCATE
    assert r1.affected_employees == ["EMP-SOLO"]

    # Gap 2 CANNOT take Solo Performer because capacity is exhausted -> must route to HIRE
    assert r2.action == RecommendationAction.HIRE
    assert r2.affected_employees == []


# =============================================================================
# 3. OPTIMIZATION TESTS (OR-TOOLS & BASELINE COMPARISON)
# =============================================================================

def test_ortools_solver_optimal_allocation():
    """Verify Google OR-Tools CP-SAT finds valid optimal allocation satisfying capacity & skills."""
    demands = [
        {"id": "DEM-OPT-1", "project_id": "PRJ-1", "primary_skill_id": "SKL-PY", "min_proficiency": 3, "required_hours": 40.0, "priority": 1},
        {"id": "DEM-OPT-2", "project_id": "PRJ-2", "primary_skill_id": "SKL-JS", "min_proficiency": 3, "required_hours": 40.0, "priority": 2},
    ]
    employees = [
        {"id": "EMP-1", "first_name": "Dev", "last_name": "Py", "standard_hours_per_week": 40.0, "employment_status": "ACTIVE"},
        {"id": "EMP-2", "first_name": "Dev", "last_name": "Js", "standard_hours_per_week": 40.0, "employment_status": "ACTIVE"},
    ]
    skills = [
        {"employee_id": "EMP-1", "skill_id": "SKL-PY", "proficiency_level": 4, "is_current": True, "verified_at": "2026-09-01"},
        {"employee_id": "EMP-2", "skill_id": "SKL-JS", "proficiency_level": 4, "is_current": True, "verified_at": "2026-09-01"},
    ]

    result = OrToolsWorkforceSolver.solve(
        demand_items=demands,
        employees=employees,
        employee_skills=skills,
    )

    assert result.status == OptimizationStatus.OPTIMAL
    assert result.demand_fulfillment_percentage == 100.0
    assert result.total_allocated_hours == 80.0
    assert result.total_unfilled_hours == 0.0
    assert result.constraint_violations_count == 0
    assert len(result.allocations) == 2

    # Verify matching correctness
    d1_alloc = next(a for a in result.allocations if a.demand_id == "DEM-OPT-1")
    d2_alloc = next(a for a in result.allocations if a.demand_id == "DEM-OPT-2")
    assert d1_alloc.employee_id == "EMP-1"
    assert d2_alloc.employee_id == "EMP-2"


def test_ortools_enforces_stale_skill_constraint():
    """Verify OR-Tools does not directly allocate an employee whose skill is stale."""
    as_of = date(2026, 10, 22)
    demands = [
        {
            "id": "DEM-STALE-OPT",
            "project_id": "PRJ-SEC",
            "primary_skill_id": "SKL-SEC",
            "min_proficiency": 3,
            "required_hours": 40.0,
            "priority": 1,
            "start_date": "2026-12-01",  # 40 days to start; allows training
        }
    ]
    employees = [
        {"id": "EMP-OLD", "first_name": "Old", "last_name": "Timer", "standard_hours_per_week": 40.0, "employment_status": "ACTIVE"}
    ]
    # Verified 800 days ago -> STALE
    skills = [
        {"employee_id": "EMP-OLD", "skill_id": "SKL-SEC", "proficiency_level": 4, "is_current": True, "verified_at": "2024-08-01"}
    ]

    result = OrToolsWorkforceSolver.solve(
        demand_items=demands,
        employees=employees,
        employee_skills=skills,
        as_of_date=as_of,
    )

    assert result.demand_fulfillment_percentage == 100.0
    alloc = result.allocations[0]
    # Direct internal allocation is forbidden; must be TRAINING_AND_ALLOCATE or EXTERNAL_HIRE
    assert alloc.action_type in ("TRAINING_AND_ALLOCATE", "EXTERNAL_HIRE")
    assert alloc.action_type != "INTERNAL_ALLOCATION"


def test_ortools_infeasible_scenario_diagnosis():
    """Verify explainable infeasibility diagnosis when constraints prevent full internal staffing."""
    demands = [
        {"id": "DEM-IMPOSSIBLE", "project_id": "PRJ-IMP", "primary_skill_id": "SKL-QUANTUM", "min_proficiency": 5, "required_hours": 40.0, "priority": 1}
    ]
    # Empty employee pool
    result = OrToolsWorkforceSolver.solve(
        demand_items=demands,
        employees=[],
        employee_skills=[],
    )

    # When internal resources are absent, solver routes to external hire or diagnoses unfilled
    assert result.infeasibility_diagnosis is not None
    assert len(result.allocations) == 1
    assert result.allocations[0].action_type in ("EXTERNAL_HIRE", "UNFILLED")


def test_benchmark_comparison_ortools_vs_greedy():
    """Verify WorkforceOptimizerService executes comparative benchmark against Greedy Baseline."""
    demands = [
        {"id": "DEM-1", "project_id": "PRJ-1", "primary_skill_id": "SKL-JAVA", "min_proficiency": 3, "required_hours": 40.0, "priority": 1},
        {"id": "DEM-2", "project_id": "PRJ-2", "primary_skill_id": "SKL-JAVA", "min_proficiency": 3, "required_hours": 40.0, "priority": 2},
    ]
    employees = [
        {"id": "EMP-JAVA-1", "first_name": "Java", "last_name": "One", "standard_hours_per_week": 40.0, "employment_status": "ACTIVE"},
        {"id": "EMP-JAVA-2", "first_name": "Java", "last_name": "Two", "standard_hours_per_week": 40.0, "employment_status": "ACTIVE"},
    ]
    skills = [
        {"employee_id": "EMP-JAVA-1", "skill_id": "SKL-JAVA", "proficiency_level": 4, "is_current": True, "verified_at": "2026-09-01"},
        {"employee_id": "EMP-JAVA-2", "skill_id": "SKL-JAVA", "proficiency_level": 4, "is_current": True, "verified_at": "2026-09-01"},
    ]

    opt_result = WorkforceOptimizerService.optimize_allocations(
        demand_items=demands,
        employees=employees,
        employee_skills=skills,
        compare_with_baseline=True,
    )

    assert opt_result.status == OptimizationStatus.OPTIMAL
    assert opt_result.demand_fulfillment_percentage == 100.0
    assert opt_result.baseline_benchmark is not None
    assert opt_result.baseline_benchmark.solver_name == "Greedy First-Fit Baseline"
    assert opt_result.baseline_benchmark.demand_fulfillment_percentage >= 0.0
