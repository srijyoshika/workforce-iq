"""
Workforce Gap Analysis Service for WorkforceIQ.

Calculates quantitative deficits between project demand requirements and available talent supply:
1. Required demand hours vs qualified talent supply hours.
2. Unfilled demand hours and fulfillment percentages.
3. Required headcount vs available qualified headcount.
4. Skill gap (headcount deficit) and capacity gap (hours deficit).
5. Dynamic risk severity categorization (CRITICAL, HIGH, MEDIUM, LOW).
6. Synchronization and persistence of GapAnalysis database entities.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Union
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import GapSeverity, GapStatus
from app.models.intelligence import GapAnalysis
from app.models.project import DemandPlan, Project
from app.models.skill import Skill
from app.services.skill_matching_service import CandidateMatch, SkillMatchingService
from app.services.thresholds import DEFAULT_THRESHOLDS, PlanningThresholds


@dataclass(frozen=True)
class GapAnalysisResult:
    """Quantitative talent and capacity deficit evaluation for a demand requirement."""
    demand_plan_id: str
    project_id: str
    project_name: str
    skill_id: str
    skill_name: str
    role_id: str
    start_date: date
    end_date: date
    required_proficiency: int
    required_headcount: int
    available_qualified_headcount: int
    headcount_deficit: int
    required_demand_hours: float
    qualified_supply_hours: float
    unfilled_demand_hours: float
    capacity_gap_hours: float
    fulfillment_percentage: float
    severity: str
    status: str
    calculated_at: str
    rule_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "demand_plan_id": self.demand_plan_id,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "role_id": self.role_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "required_proficiency": self.required_proficiency,
            "required_headcount": self.required_headcount,
            "available_qualified_headcount": self.available_qualified_headcount,
            "headcount_deficit": self.headcount_deficit,
            "required_demand_hours": self.required_demand_hours,
            "qualified_supply_hours": self.qualified_supply_hours,
            "unfilled_demand_hours": self.unfilled_demand_hours,
            "capacity_gap_hours": self.capacity_gap_hours,
            "fulfillment_percentage": self.fulfillment_percentage,
            "severity": self.severity,
            "status": self.status,
            "calculated_at": self.calculated_at,
            "rule_version": self.rule_version,
        }


class GapAnalysisService:
    """Canonical engine for capability, skill, and capacity gap intelligence."""

    @classmethod
    def determine_gap_severity(
        cls,
        headcount_deficit: int,
        unfilled_pct: float,
        priority: int = 3,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> GapSeverity:
        """
        Evaluate gap severity based on priority, headcount deficit, and unfilled demand ratio.
        """
        # Critical priority or severe deficit
        if priority == thresholds.critical_priority_level or headcount_deficit >= 3 or unfilled_pct >= thresholds.critical_gap_unfilled_pct:
            return GapSeverity.CRITICAL
        elif priority == 2 or headcount_deficit >= 2 or unfilled_pct >= thresholds.high_gap_unfilled_pct:
            return GapSeverity.HIGH
        elif headcount_deficit >= 1 or unfilled_pct >= thresholds.medium_gap_unfilled_pct:
            return GapSeverity.MEDIUM
        else:
            return GapSeverity.LOW

    @classmethod
    def calculate_demand_gap(
        cls,
        demand_plan: Union[DemandPlan, Dict[str, Any]],
        qualified_candidates: Sequence[CandidateMatch],
        project_name: str = "Target Project",
        skill_name: str = "Required Skill",
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> GapAnalysisResult:
        """
        Compute quantitative gap metrics comparing required demand against matched qualified supply.
        """
        if isinstance(demand_plan, dict):
            d_id = demand_plan.get("id", "UNKNOWN")
            p_id = demand_plan.get("project_id", "UNKNOWN")
            r_id = demand_plan.get("role_id", "UNKNOWN")
            s_id = demand_plan.get("primary_skill_id", "UNKNOWN")
            start_d = demand_plan.get("start_date")
            end_d = demand_plan.get("end_date")
            req_prof = int(demand_plan.get("min_proficiency") or 3)
            req_hc = int(demand_plan.get("required_headcount") or 1)
            req_hours = float(demand_plan.get("required_hours") or 40.0)
            ful_hours = float(demand_plan.get("fulfilled_hours") or 0.0)
            priority = int(demand_plan.get("priority") or 3)
        else:
            d_id = getattr(demand_plan, "id", "UNKNOWN")
            p_id = getattr(demand_plan, "project_id", "UNKNOWN")
            r_id = getattr(demand_plan, "role_id", "UNKNOWN")
            s_id = getattr(demand_plan, "primary_skill_id", "UNKNOWN")
            start_d = getattr(demand_plan, "start_date", None)
            end_d = getattr(demand_plan, "end_date", None)
            req_prof = int(getattr(demand_plan, "min_proficiency", 3) or 3)
            req_hc = int(getattr(demand_plan, "required_headcount", 1) or 1)
            req_hours = float(getattr(demand_plan, "required_hours", 40.0) or 40.0)
            ful_hours = float(getattr(demand_plan, "fulfilled_hours", 0.0) or 0.0)
            priority = int(getattr(demand_plan, "priority", 3) or 3)

        # Qualified available talent supply
        fully_qualified = [c for c in qualified_candidates if c.is_fully_qualified]
        avail_hc = len(fully_qualified)
        hc_deficit = max(0, req_hc - avail_hc)

        # Qualified supply hours
        supply_hours = sum(c.remaining_capacity_hours for c in fully_qualified)
        unfilled_hours = round(max(0.0, req_hours - ful_hours), 2)
        capacity_gap = round(max(0.0, req_hours - supply_hours), 2)

        unfilled_pct = round((unfilled_hours / req_hours * 100.0), 2) if req_hours > 0.0 else 0.0
        ful_pct = round(min(100.0, (ful_hours / req_hours * 100.0)), 2) if req_hours > 0.0 else 100.0

        severity = cls.determine_gap_severity(hc_deficit, unfilled_pct, priority, thresholds)
        status = GapStatus.RESOLVED.value if (unfilled_hours == 0.0 and hc_deficit == 0) else GapStatus.IDENTIFIED.value

        return GapAnalysisResult(
            demand_plan_id=d_id,
            project_id=p_id,
            project_name=project_name,
            skill_id=s_id,
            skill_name=skill_name,
            role_id=r_id,
            start_date=start_d,
            end_date=end_d,
            required_proficiency=req_prof,
            required_headcount=req_hc,
            available_qualified_headcount=avail_hc,
            headcount_deficit=hc_deficit,
            required_demand_hours=req_hours,
            qualified_supply_hours=round(supply_hours, 2),
            unfilled_demand_hours=unfilled_hours,
            capacity_gap_hours=capacity_gap,
            fulfillment_percentage=ful_pct,
            severity=severity.value,
            status=status,
            calculated_at=datetime.now(timezone.utc).isoformat(),
            rule_version=thresholds.rule_version,
        )

    @classmethod
    async def analyze_project_gaps_async(
        cls,
        session: AsyncSession,
        project_id: str,
        as_of_date: Optional[date] = None,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> List[GapAnalysisResult]:
        """Analyze capability and capacity gaps across all demand plans of a project."""
        p_stmt = select(Project).where(Project.id == project_id)
        p_res = await session.execute(p_stmt)
        project = p_res.scalar_one_or_none()
        if not project:
            return []

        d_stmt = select(DemandPlan).where(DemandPlan.project_id == project_id)
        d_res = await session.execute(d_stmt)
        demands = d_res.scalars().all()

        results: List[GapAnalysisResult] = []
        for d in demands:
            candidates = await SkillMatchingService.match_candidates_for_demand_async(
                session=session,
                demand_plan_id=d.id,
                as_of_date=as_of_date,
                top_n=20,
                thresholds=thresholds,
            )
            # Fetch skill name
            skill_name = "Primary Skill"
            if d.primary_skill_id:
                s_stmt = select(Skill).where(Skill.id == d.primary_skill_id)
                s_res = await session.execute(s_stmt)
                skl = s_res.scalar_one_or_none()
                if skl:
                    skill_name = skl.name

            gap = cls.calculate_demand_gap(
                demand_plan=d,
                qualified_candidates=candidates,
                project_name=project.name,
                skill_name=skill_name,
                thresholds=thresholds,
            )
            results.append(gap)

        return results

    @classmethod
    async def sync_gap_analyses_async(
        cls,
        session: AsyncSession,
        project_ids: Optional[List[str]] = None,
        as_of_date: Optional[date] = None,
        thresholds: PlanningThresholds = DEFAULT_THRESHOLDS,
    ) -> int:
        """
        Synchronize GapAnalysis database records with active project demands.
        Inserts new deficits or updates existing identified gap records.
        """
        proj_stmt = select(Project.id)
        if project_ids:
            proj_stmt = proj_stmt.where(Project.id.in_(project_ids))
        proj_res = await session.execute(proj_stmt)
        p_ids = [r[0] for r in proj_res.all()]

        created_count = 0
        now_dt = datetime.now(timezone.utc)
        ref_date = as_of_date or date.today()

        for p_id in p_ids:
            gaps = await cls.analyze_project_gaps_async(session, p_id, as_of_date=as_of_date, thresholds=thresholds)
            for g in gaps:
                # Check if GapAnalysis already exists for this demand plan
                existing_stmt = select(GapAnalysis).where(GapAnalysis.demand_plan_id == g.demand_plan_id)
                existing_res = await session.execute(existing_stmt)
                existing = existing_res.scalar_one_or_none()

                if existing:
                    existing.required_headcount = g.required_headcount
                    existing.available_headcount = g.available_qualified_headcount
                    existing.deficit_headcount = g.headcount_deficit
                    existing.severity = GapSeverity(g.severity)
                    existing.status = GapStatus(g.status)
                    existing.analysis_date = ref_date
                    existing.updated_at = now_dt
                else:
                    biz_id = f"GAP-{ref_date.year}-{created_count + 1:06d}"
                    import uuid
                    pk_id = str(uuid.uuid4())
                    new_gap = GapAnalysis(
                        id=pk_id,
                        business_id=biz_id,
                        project_id=g.project_id,
                        demand_plan_id=g.demand_plan_id,
                        skill_id=g.skill_id,
                        required_proficiency=g.required_proficiency,
                        required_headcount=g.required_headcount,
                        available_headcount=g.available_qualified_headcount,
                        deficit_headcount=g.headcount_deficit,
                        severity=GapSeverity(g.severity),
                        status=GapStatus(g.status),
                        target_fulfillment_date=g.start_date,
                        analysis_date=ref_date,
                        created_at=now_dt,
                        updated_at=now_dt,
                    )
                    session.add(new_gap)
                    created_count += 1

        await session.commit()
        return created_count

