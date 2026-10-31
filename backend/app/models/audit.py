"""
Audit Domain Model for WorkforceIQ.
Provides tamper-evident compliance audit trail for all workforce and allocation mutations.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin
from app.models.enums import AuditAction

if TYPE_CHECKING:
    from app.models.employee import Employee


class AuditEvent(Base, UUIDMixin):
    """
    Append-only audit trail logging data mutations, skill verifications,
    and allocation approvals.
    """
    __tablename__ = "audit_events"

    # Immutable Business Identifier convention: AUD-2026-000001
    business_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="Business identifier convention e.g. AUD-2026-000001",
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Target entity class e.g. Allocation, EmployeeSkill, DemandPlan",
    )

    entity_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="Target record UUID or business ID",
    )

    action: Mapped[AuditAction] = mapped_column(
        SAEnum(AuditAction, native_enum=False),
        nullable=False,
        index=True,
        comment="Mutation type: INSERT, UPDATE, DELETE, VERIFY, ALLOCATE, SIMULATE",
    )

    performed_by_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Actor employee responsible for mutation",
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        comment="UTC event timestamp",
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="Client IP address for security auditing",
    )

    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Pre-mutation field state JSON snapshot",
    )

    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Post-mutation field state JSON snapshot",
    )

    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Business justification or change-ticket reference",
    )

    # Relationships
    performed_by: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        back_populates="audit_events",
    )

    @property
    def created_at(self) -> datetime:
        """Alias for timestamp for consistent created_at contract."""
        return self.timestamp

