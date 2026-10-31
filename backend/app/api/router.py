"""
Master API Router for WorkforceIQ.
Aggregates versioned domain routers into a unified namespace.
"""

from fastapi import APIRouter
from app.api.v1 import (
    allocations,
    analytics,
    audit,
    auth,
    availability,
    demand,
    employees,
    evaluation,
    forecasting,
    health,
    projects,
    quality,
    recommendations,
    risks,
    roles,
    scenarios,
    skills,
    training,
)

api_router = APIRouter()

# Include version 1 domain routes
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(employees.router)
api_router.include_router(roles.router)
api_router.include_router(skills.router)
api_router.include_router(projects.router)
api_router.include_router(demand.router)
api_router.include_router(allocations.router)
api_router.include_router(availability.router)
api_router.include_router(training.router)
api_router.include_router(analytics.router)
api_router.include_router(forecasting.router)
api_router.include_router(recommendations.router)
api_router.include_router(scenarios.router)
api_router.include_router(risks.router)
api_router.include_router(quality.router)
api_router.include_router(evaluation.router)
api_router.include_router(audit.router)
