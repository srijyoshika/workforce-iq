"""
Project Master Record Generator.
Generates enterprise project initiatives with realistic budgets, timelines,
department alignment, delivery leads, and lifecycle states.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List
import numpy as np

from backend.generator.config import GeneratorConfig
from backend.generator.id_generator import generate_uuid, project_id

PROJECT_THEMES: List[str] = [
    "Enterprise Cloud Migration & Modernization",
    "Customer 360 AI Analytics Platform",
    "Omnichannel Digital Experience Portal",
    "Zero Trust Perimeter Architecture",
    "Data Lakehouse & Streaming Pipeline",
    "Automated CI/CD Delivery Pipeline",
    "Healthcare FHIR Interoperability Hub",
    "Next-Gen Core Banking Ledger Migration",
    "Supply Chain Logistics Optimization",
    "Global Workforce Intelligence Platform",
    "Microservices De-monolithization Initiative",
    "Predictive Equipment Maintenance Engine",
    "Regulatory Compliance & SOC 2 Automation",
    "Identity & Access Management Governance",
    "E-Commerce Payment Gateway Refactor",
    "Mobile Native Client Modernization",
    "Enterprise Knowledge Graph & Semantic RAG",
    "Global Network SD-WAN Rollout",
    "Automated Quality Assurance Test Mesh",
    "Telemetry Observability & SRE Modernization",
]

CLIENT_PORTFOLIO: List[str] = [
    "Apex Financial Holdings",
    "Vanguard Healthcare Network",
    "Starlight Global Logistics",
    "Pinnacle Retail Group",
    "Meridian Telecommunications",
    "OmniMedia Global Stream",
    "Horizon Energy Solutions",
    "Nexus Aerospace Corporation",
    "Internal Strategic Initiative",
    "Executive Innovation Program",
]


def generate_projects(
    config: GeneratorConfig,
    employees: List[Dict[str, Any]],
    rng: np.random.Generator,
) -> List[Dict[str, Any]]:
    """Generate enterprise project master records."""
    total_count = config.scale_config.project_count
    projects: List[Dict[str, Any]] = []

    # Qualified managers: Senior or Lead employees
    qualified_managers = [e["id"] for e in employees if e.get("experience_tier") in ["Senior", "Lead/Principal"]]
    if not qualified_managers:
        qualified_managers = [employees[0]["id"]]

    status_keys = list(config.project_status_weights.keys())
    status_probs = list(config.project_status_weights.values())

    durations_days = [90, 180, 270, 365]

    for seq in range(1, total_count + 1):
        biz_id = project_id(seq, year=2026)
        pk_id = generate_uuid("Project", biz_id)

        theme = PROJECT_THEMES[(seq - 1) % len(PROJECT_THEMES)]
        name = f"{theme} - Phase {((seq - 1) % 4) + 1}"
        acronym = "".join(w[0] for w in theme.split()[:4]).upper()
        code = f"PRJ-{acronym}-{seq:04d}"

        client = CLIENT_PORTFOLIO[rng.integers(0, len(CLIENT_PORTFOLIO))]
        department = rng.choice(config.departments)
        status = rng.choice(status_keys, p=status_probs)

        # Timeline generation
        duration = int(rng.choice(durations_days))
        # Start date staggered across the planning year
        start_offset_days = int(rng.integers(-60, 240))
        start_date = config.planning_start_date + timedelta(days=start_offset_days)
        end_date = start_date + timedelta(days=duration)

        # Budget: $250k to $2.5M
        budget_val = round(rng.uniform(250000.00, 2500000.00), -3)
        budget = Decimal(str(budget_val))

        manager_id = rng.choice(qualified_managers)

        created_at = datetime(start_date.year, max(1, start_date.month - 1), 1, 9, 0, 0, tzinfo=timezone.utc)
        updated_at = datetime(config.as_of_date.year, config.as_of_date.month, config.as_of_date.day, 12, 0, 0, tzinfo=timezone.utc)

        projects.append({
            "id": pk_id,
            "business_id": biz_id,
            "name": name,
            "code": code,
            "client_name": client,
            "department": department,
            "status": status,
            "start_date": start_date,
            "end_date": end_date,
            "budget": budget,
            "manager_id": manager_id,
            "created_at": created_at,
            "updated_at": updated_at,
        })

    return projects

