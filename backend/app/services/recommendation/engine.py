"""
WorkforceIQ Explainable Recommendation Engine.

Executes strict hierarchical decision logic to remediate workforce deficits:
1. Evaluate eligible internal employees with verified, non-stale skills.
2. Assess REALLOCATION feasibility (internal transfer with available capacity).
3. Assess TRAINING feasibility (upskilling adjacent talent within deadline).
4. Estimate HIRING requirements (external recruitment for unmitigated deficits).
5. Evaluate RESCHEDULING when deadline conflicts arise on flexible projects.

Enforces zero capacity double-counting and comprehensive explainability.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Union

from app.models.enums import GapSeverity, GapStatus
from app.services.gap_analysis_service import GapAnalysisResult
from app.services.recommendation.hiring_evaluator import HiringEvaluator
from app.services.recommendation.reallocation_evaluator import ReallocationEvaluator
from app.services.recommendation.rescheduling_evaluator import ReschedulingEvaluator
from app.services.recommendation.training_evaluator import TrainingEvaluator
from app.services.recommendation.types import (
    RecommendationAction,
    RecommendationItem,
    RecommendationPlan,
)
from app.services.skill_matching_service import CandidateMatch


class RecommendationEngine:
    """
    Master Workforce Recommendation Engine.
    Processes gap analyses and candidate pools to construct optimal, explainable action plans.
    """

    @classmethod
    def generate_recommendations_for_gap(
        cls,
        gap: Union[GapAnalysisResult, Dict[str, Any]],
        candidate_pool: Sequence[CandidateMatch],
        committed_capacities: Dict[str, float],
        as_of_date: Optional[date] = None,
        project_priority: int = 2,
    ) -> List[RecommendationItem]:
        """
        Evaluate a single gap deficit through the strict decision hierarchy.
        Returns ordered list of recommended actions to resolve the gap.
        """
        ref_date = as_of_date or date.today()

        gap_id = gap.demand_plan_id if isinstance(gap, GapAnalysisResult) else gap.get("demand_plan_id", "GAP-UNKNOWN")
        proj_id = gap.project_id if isinstance(gap, GapAnalysisResult) else gap.get("project_id", "PRJ-UNKNOWN")
        skill_id = gap.skill_id if isinstance(gap, GapAnalysisResult) else gap.get("skill_id", "SKL-UNKNOWN")
        skill_name = gap.skill_name if isinstance(gap, GapAnalysisResult) else gap.get("skill_name", skill_id)
        start_date = gap.start_date if isinstance(gap, GapAnalysisResult) else gap.get("start_date")

        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)

        days_to_deadline = max(0, (start_date - ref_date).days) if start_date else 30

        # Unfilled hours to resolve
        unfilled_hours = (
            gap.unfilled_demand_hours
            if isinstance(gap, GapAnalysisResult)
            else float(gap.get("unfilled_demand_hours", 40.0))
        )

        recommendations: List[RecommendationItem] = []
        remaining_gap_hours = unfilled_hours

        # ---------------------------------------------------------------------
        # STEP 1 & 2: REALLOCATION EVALUATION (Eligible internal with verified skills)
        # ---------------------------------------------------------------------
        realloc_rec = ReallocationEvaluator.evaluate(
            candidates=candidate_pool,
            committed_capacities=committed_capacities,
            required_hours=remaining_gap_hours,
            days_to_deadline=days_to_deadline,
            gap_id=gap_id,
            project_id=proj_id,
            required_skill=skill_name,
        )

        if realloc_rec:
            recommendations.append(realloc_rec)
            remaining_gap_hours = max(0.0, remaining_gap_hours - realloc_rec.expected_shortage_reduction_hours)

        # ---------------------------------------------------------------------
        # STEP 3: TRAINING EVALUATION (Upskilling adjacent talent)
        # ---------------------------------------------------------------------
        if remaining_gap_hours > 0.0:
            train_rec = TrainingEvaluator.evaluate(
                candidates=candidate_pool,
                committed_capacities=committed_capacities,
                required_hours=remaining_gap_hours,
                days_to_deadline=days_to_deadline,
                gap_id=gap_id,
                project_id=proj_id,
                required_skill=skill_name,
            )
            if train_rec:
                recommendations.append(train_rec)
                remaining_gap_hours = max(0.0, remaining_gap_hours - train_rec.expected_shortage_reduction_hours)

        # ---------------------------------------------------------------------
        # STEP 4: HIRING EVALUATION (External acquisition for remaining deficit)
        # ---------------------------------------------------------------------
        hiring_rec: Optional[RecommendationItem] = None
        if remaining_gap_hours > 0.0:
            hiring_rec = HiringEvaluator.evaluate(
                required_hours=remaining_gap_hours,
                days_to_deadline=days_to_deadline,
                gap_id=gap_id,
                project_id=proj_id,
                required_skill=skill_name,
            )
            recommendations.append(hiring_rec)
            remaining_gap_hours = 0.0

        # ---------------------------------------------------------------------
        # STEP 5: RESCHEDULING EVALUATION (Schedule shift for infeasible deadlines)
        # ---------------------------------------------------------------------
        # If any generated recommendation breaches the target deadline, check if project can be rescheduled
        has_deadline_breach = any(not r.deadline_feasibility for r in recommendations)
        if has_deadline_breach and project_priority > 1:
            primary_breaching_action = hiring_rec.action if hiring_rec else (
                recommendations[0].action if recommendations else None
            )
            resched_rec = ReschedulingEvaluator.evaluate(
                required_hours=unfilled_hours,
                days_to_deadline=days_to_deadline,
                project_priority=project_priority,
                recommended_action=primary_breaching_action,
                gap_id=gap_id,
                project_id=proj_id,
                required_skill=skill_name,
            )
            if resched_rec:
                recommendations.append(resched_rec)

        return recommendations

    @classmethod
    def generate_portfolio_plan(
        cls,
        gaps: Sequence[Union[GapAnalysisResult, Dict[str, Any]]],
        candidate_pools_by_gap: Dict[str, Sequence[CandidateMatch]],
        as_of_date: Optional[date] = None,
        project_priorities_map: Optional[Dict[str, int]] = None,
    ) -> RecommendationPlan:
        """
        Generate complete, non-double-counted recommendation plan across all portfolio gaps.
        """
        prio_map = project_priorities_map or {}
        committed_capacities: Dict[str, float] = {}
        all_recommendations: List[RecommendationItem] = []
        mitigated_gaps_count = 0
        unmitigated_ids: List[str] = []

        total_cost = 0.0
        total_reduction = 0.0

        for gap in gaps:
            gap_id = gap.demand_plan_id if isinstance(gap, GapAnalysisResult) else gap.get("demand_plan_id", "GAP-UNKNOWN")
            proj_id = gap.project_id if isinstance(gap, GapAnalysisResult) else gap.get("project_id", "PRJ-UNKNOWN")
            prio = prio_map.get(proj_id, 2)

            candidates = candidate_pools_by_gap.get(gap_id, [])

            recs = cls.generate_recommendations_for_gap(
                gap=gap,
                candidate_pool=candidates,
                committed_capacities=committed_capacities,
                as_of_date=as_of_date,
                project_priority=prio,
            )

            if recs:
                mitigated_gaps_count += 1
                for r in recs:
                    all_recommendations.append(r)
                    total_cost += r.expected_cost
                    # Only add shortage reduction for capacity-adding actions (reallocate, train, hire)
                    if r.action != RecommendationAction.RESCHEDULE:
                        total_reduction += r.expected_shortage_reduction_hours
            else:
                unmitigated_ids.append(gap_id)

        return RecommendationPlan(
            recommendations=all_recommendations,
            total_expected_cost=round(total_cost, 2),
            total_shortage_reduction_hours=round(total_reduction, 2),
            gaps_analyzed_count=len(gaps),
            gaps_mitigated_count=mitigated_gaps_count,
            unmitigated_gap_ids=unmitigated_ids,
            rule_version="1.0.0",
        )

    @classmethod
    def generate_recommendations(
        cls,
        gaps: Sequence[Dict[str, Any]],
        employees: Sequence[Dict[str, Any]],
        employee_skills: Sequence[Dict[str, Any]],
        allocations: Sequence[Dict[str, Any]],
        training_budget: float = 50000.0,
        hiring_budget: float = 200000.0,
        hiring_lead_time_days: int = 45,
        as_of_date: Optional[date] = None,
    ) -> List[RecommendationItem]:
        """
        Synthesize explainable recommendations from in-memory workforce data structures
        (e.g., during scenario planning simulations).
        """
        ref_date = as_of_date or date.today()

        # Build allocated hours map
        allocated_map: Dict[str, float] = {}
        for a in allocations:
            eid = a.get("employee_id")
            if eid:
                allocated_map[eid] = allocated_map.get(eid, 0.0) + float(a.get("allocated_hours_per_week", 0.0))

        # Build skill map per employee: {emp_id: {skill_id: skill_dict}}
        emp_skills_map: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for es in employee_skills:
            eid = es.get("employee_id")
            sid = es.get("skill_id")
            if eid and sid:
                if eid not in emp_skills_map:
                    emp_skills_map[eid] = {}
                emp_skills_map[eid][sid] = es

        # Employee lookup
        emp_lookup = {e["id"]: e for e in employees if e.get("employment_status") == "ACTIVE"}

        committed_capacities: Dict[str, float] = {}
        all_recommendations: List[RecommendationItem] = []

        for gap in gaps:
            req_skill_id = gap.get("required_skill_id") or gap.get("skill_id")
            req_prof = int(gap.get("required_proficiency", 3))
            prio = int(gap.get("project_priority", 2))

            # Build candidate pool for this gap
            candidates: List[CandidateMatch] = []
            for eid, emp in emp_lookup.items():
                std_hours = float(emp.get("standard_hours_per_week", 40.0))
                alloc_hours = allocated_map.get(eid, 0.0)
                rem_hours = max(0.0, std_hours - alloc_hours)

                es = emp_skills_map.get(eid, {}).get(req_skill_id)
                if es:
                    prof = int(es.get("proficiency_level", 1))
                    verified_at = es.get("verified_at")
                    is_stale = False
                    if verified_at:
                        if isinstance(verified_at, str):
                            v_date = date.fromisoformat(verified_at[:10])
                        elif hasattr(verified_at, "date"):
                            v_date = verified_at.date()
                        else:
                            v_date = verified_at
                        if (ref_date - v_date).days > 730:
                            is_stale = True

                    eff_prof = 1 if is_stale else prof
                    is_qualified = (eff_prof >= req_prof) and not is_stale
                    score = min(100.0, max(0.0, (eff_prof / max(1, req_prof)) * 70.0 + (rem_hours / max(1.0, std_hours)) * 30.0))

                    cand = CandidateMatch(
                        employee_id=eid,
                        business_id=emp.get("business_id", eid),
                        employee_name=emp.get("name", "Unknown"),
                        role_id=emp.get("role_id"),
                        department=emp.get("department", "Engineering"),
                        skill_id=req_skill_id or "SKL-GENERIC",
                        skill_name=gap.get("required_skill_name") or gap.get("skill_name", "Technical Competency"),
                        assessed_proficiency=prof,
                        effective_certified_proficiency=eff_prof,
                        required_proficiency=req_prof,
                        proficiency_gap=max(0, req_prof - eff_prof),
                        verification_status=es.get("verification_status", "MANAGER_VERIFIED"),
                        verified_at=str(verified_at) if verified_at else None,
                        is_stale=is_stale,
                        available_hours=std_hours,
                        allocated_hours=alloc_hours,
                        remaining_capacity_hours=rem_hours,
                        is_fully_qualified=is_qualified,
                        match_score=score,
                        calculated_at=ref_date.isoformat(),
                        rule_version="1.0.0",
                    )
                    candidates.append(cand)

            # Sort candidates by suitability
            candidates.sort(key=lambda c: (c.is_fully_qualified, c.match_score), reverse=True)

            recs = cls.generate_recommendations_for_gap(
                gap=gap,
                candidate_pool=candidates,
                committed_capacities=committed_capacities,
                as_of_date=ref_date,
                project_priority=prio,
            )
            all_recommendations.extend(recs)

        return all_recommendations

