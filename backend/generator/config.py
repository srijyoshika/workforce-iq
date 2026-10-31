"""
Generator Configuration Module.
Defines parameters for starter (100 emp, 30 skl, 20 prj) and full (5000 emp, 300 skl, 500 prj) scales,
deterministic random seeds, date anchors, and demographic distributions.
"""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class ScaleConfig:
    """Target entity scale parameters."""
    employee_count: int
    skill_count: int
    project_count: int
    role_count: int
    months_of_demand: int = 12


STARTER_CONFIG = ScaleConfig(
    employee_count=100,
    skill_count=30,
    project_count=20,
    role_count=15,
    months_of_demand=12,
)

FULL_CONFIG = ScaleConfig(
    employee_count=5000,
    skill_count=300,
    project_count=500,
    role_count=40,
    months_of_demand=12,
)


@dataclass
class GeneratorConfig:
    """Master runtime generator configuration."""
    scale: str = "starter"
    seed: int = 20261022
    as_of_date: date = date(2026, 10, 22)
    planning_start_date: date = date(2026, 1, 1)
    planning_end_date: date = date(2026, 12, 31)
    output_dir: Path = Path("data/exports")

    # Resolved scale parameters
    scale_config: ScaleConfig = field(default_factory=lambda: STARTER_CONFIG)

    # Enterprise Operating Units
    departments: List[str] = field(default_factory=lambda: [
        "Cloud & Platform Engineering",
        "Data & Applied AI",
        "Cybersecurity & Compliance",
        "Enterprise Architecture",
        "Core Software Engineering",
        "Product Management",
        "Digital Transformation & Consulting",
        "IT Service Operations",
    ])

    # Global Hub Locations
    locations: List[str] = field(default_factory=lambda: [
        "New York, NY",
        "Austin, TX",
        "San Francisco, CA",
        "Chicago, IL",
        "London, UK",
        "Berlin, DE",
        "Toronto, CA",
        "Remote - US",
        "Remote - EMEA",
    ])

    # Employment status distribution weights (must sum to 1.0)
    employment_status_weights: Dict[str, float] = field(default_factory=lambda: {
        "ACTIVE": 0.85,
        "CONTRACTOR": 0.08,
        "ON_LEAVE": 0.04,
        "PROBATION": 0.03,
    })

    # Full-time (40h) vs Part-time (20h/30h) split
    work_capacity_distribution: Dict[float, float] = field(default_factory=lambda: {
        40.0: 0.88,  # Full-Time
        30.0: 0.07,  # Part-Time 75%
        20.0: 0.05,  # Part-Time 50%
    })

    # Experience level tiers influencing hire dates and hourly cost benchmarks
    experience_level_weights: Dict[str, float] = field(default_factory=lambda: {
        "Junior": 0.20,      # 1-2 years exp, $45-$65/hr
        "Mid-Level": 0.40,    # 3-5 years exp, $70-$100/hr
        "Senior": 0.25,       # 6-9 years exp, $105-$145/hr
        "Lead/Principal": 0.15 # 10+ years exp, $150-$210/hr
    })

    # Project lifecycle status distribution
    project_status_weights: Dict[str, float] = field(default_factory=lambda: {
        "ACTIVE": 0.60,
        "APPROVED": 0.20,
        "PIPELINE": 0.10,
        "COMPLETED": 0.07,
        "ON_HOLD": 0.03,
    })

    # Seasonal quarterly demand weights
    quarterly_seasonality_multipliers: Dict[int, float] = field(default_factory=lambda: {
        1: 1.15,  # Q1 Planning & Kickoff surge
        2: 1.05,  # Q2 Stable execution
        3: 0.85,  # Q3 Summer holiday lull
        4: 1.20,  # Q4 Year-end push and delivery sprint
    })

    def __post_init__(self):
        """Validate and resolve scale configuration."""
        if self.scale.lower() == "full":
            self.scale_config = FULL_CONFIG
        elif self.scale.lower() == "starter":
            self.scale_config = STARTER_CONFIG
        else:
            raise ValueError(f"Unknown scale '{self.scale}'. Allowed values: 'starter', 'full'")

