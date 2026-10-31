"""
Deterministic Identifier Generator for WorkforceIQ.
Enforces canonical enterprise business ID standards and generates deterministic UUID primary keys.
"""

import uuid

# Namespace for deterministic UUIDv5 generation
NAMESPACE_WORKFORCEIQ = uuid.UUID("3c7a2b9e-6481-4b10-a29d-9e6b5413f281")


def generate_uuid(entity_type: str, business_id: str) -> str:
    """
    Generate a deterministic, reproducible UUIDv5 string based on entity type and business ID.
    Guarantees consistent primary keys across generator runs.
    """
    name = f"workforceiq:{entity_type.lower()}:{business_id.upper()}"
    return str(uuid.uuid5(NAMESPACE_WORKFORCEIQ, name))


def employee_id(seq: int) -> str:
    """Format: EMP-###### (e.g. EMP-000001)"""
    return f"EMP-{seq:06d}"


def skill_id(seq: int) -> str:
    """Format: SKL-###### (e.g. SKL-000001)"""
    return f"SKL-{seq:06d}"


def role_id(seq: int) -> str:
    """Format: ROL-###### (e.g. ROL-000001)"""
    return f"ROL-{seq:06d}"


def role_skill_id(seq: int) -> str:
    """Format: ROLSKL-###### (e.g. ROLSKL-000001)"""
    return f"ROLSKL-{seq:06d}"


def employee_skill_id(seq: int) -> str:
    """Format: EMPSKL-###### (e.g. EMPSKL-000001)"""
    return f"EMPSKL-{seq:06d}"


def project_id(seq: int, year: int = 2026) -> str:
    """Format: PRJ-YYYY-###### (e.g. PRJ-2026-000001)"""
    return f"PRJ-{year}-{seq:06d}"


def demand_plan_id(project_business_id: str, week_num: str) -> str:
    """Format: DEM-<project-id>-YYYYWww (e.g. DEM-PRJ-2026-000001-2026W01)"""
    return f"DEM-{project_business_id}-{week_num}"


def allocation_id(seq: int, year: int = 2026) -> str:
    """Format: ALLOC-YYYY-###### (e.g. ALLOC-2026-000001)"""
    return f"ALLOC-{year}-{seq:06d}"


def availability_id(seq: int, year: int = 2026) -> str:
    """Format: AVL-YYYY-###### (e.g. AVL-2026-000001)"""
    return f"AVL-{year}-{seq:06d}"


def training_id(seq: int, year: int = 2026) -> str:
    """Format: TRN-YYYY-###### (e.g. TRN-2026-000001)"""
    return f"TRN-{year}-{seq:06d}"


def gap_analysis_id(seq: int, year: int = 2026) -> str:
    """Format: GAP-YYYY-###### (e.g. GAP-2026-000001)"""
    return f"GAP-{year}-{seq:06d}"


def recommendation_id(seq: int, year: int = 2026) -> str:
    """Format: REC-YYYY-###### (e.g. REC-2026-000001)"""
    return f"REC-{year}-{seq:06d}"


def scenario_run_id(seq: int, year: int = 2026) -> str:
    """Format: SCN-YYYY-###### (e.g. SCN-2026-000001)"""
    return f"SCN-{year}-{seq:06d}"


def issue_record_id(seq: int, year: int = 2026) -> str:
    """Format: ISS-YYYY-###### (e.g. ISS-2026-000001)"""
    return f"ISS-{year}-{seq:06d}"


def audit_event_id(seq: int, year: int = 2026) -> str:
    """Format: AUD-YYYY-###### (e.g. AUD-2026-000001)"""
    return f"AUD-{year}-{seq:06d}"

