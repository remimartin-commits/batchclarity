"""
MES Work Order Models
=====================
ALCOA+ compliant SQLAlchemy models for manufacturing execution system
work order management and material dispensing tracking.

Work orders are the operational instructions issued to the shop floor for
a specific manufacturing run.  They link back to the Master Batch Record,
track planned vs actual timelines, and capture every material dispensed
against the order with full lot traceability.

Tables
------
- work_orders              : Work order header records
- work_order_materials     : Material / component line items per work order
"""

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    Integer,
    Text,
    ForeignKey,
    Enum,
    Float,
    Date,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
import enum
import uuid
from datetime import datetime, timezone

Base = declarative_base()


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    """Return a new UUID4 string."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class WorkOrderStatus(str, enum.Enum):
    PLANNED = "planned"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class WorkOrderPriority(str, enum.Enum):
    NORMAL = "normal"
    URGENT = "urgent"
    CRITICAL = "critical"


class MaterialStatus(str, enum.Enum):
    PENDING = "pending"
    DISPENSED = "dispensed"
    RETURNED = "returned"
    RECONCILED = "reconciled"
    DESTROYED = "destroyed"


# ---------------------------------------------------------------------------
# WorkOrder
# ---------------------------------------------------------------------------


class WorkOrder(Base):
    """
    Work order header record representing a single planned manufacturing run.

    A WorkOrder is derived from the MasterBatchRecord and provides the
    shop-floor team with the formal authorisation to manufacture a specific
    product batch.  The record tracks both the planned schedule and the
    actual execution times to support OEE and deviation detection.

    Status lifecycle:
      PLANNED → RELEASED → IN_PROGRESS → COMPLETED
                                       ↘ CANCELLED / ON_HOLD

    ``work_order_number`` is unique within an organisation and follows the
    site's numbering convention (e.g. "WO-2026-00456").
    """

    __tablename__ = "work_orders"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=new_uuid,
        nullable=False,
        comment="Surrogate primary key (UUID4)",
    )

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------
    work_order_number = Column(
        String(100),
        nullable=False,
        comment="Unique work order reference number within the organisation",
    )
    batch_number = Column(
        String(100),
        nullable=True,
        comment="Assigned batch / lot number (may be allocated on release)",
    )

    # ------------------------------------------------------------------
    # Product details
    # ------------------------------------------------------------------
    product_name = Column(
        String(255),
        nullable=False,
        comment="Full name of the product to be manufactured",
    )
    product_code = Column(
        String(100),
        nullable=False,
        comment="Internal product code or SKU",
    )

    # ------------------------------------------------------------------
    # Quantity
    # ------------------------------------------------------------------
    planned_quantity = Column(
        Float,
        nullable=False,
        comment="Planned manufactured quantity",
    )
    quantity_unit = Column(
        String(50),
        nullable=False,
        comment="Unit of measure for the planned quantity (e.g. 'kg', 'L', 'units')",
    )
    actual_yield = Column(
        Float,
        nullable=True,
        comment="Actual quantity produced at completion",
    )
    yield_percentage = Column(
        Float,
        nullable=True,
        comment="Percentage yield = (actual_yield / planned_quantity) * 100",
    )

    # ------------------------------------------------------------------
    # Schedule
    # ------------------------------------------------------------------
    scheduled_start = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Planned start date and time (UTC)",
    )
    scheduled_end = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Planned end date and time (UTC)",
    )
    actual_start = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Actual start date and time recorded by the operator (UTC)",
    )
    actual_end = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Actual completion date and time recorded by the operator (UTC)",
    )

    # ------------------------------------------------------------------
    # Status & priority
    # ------------------------------------------------------------------
    status = Column(
        Enum(WorkOrderStatus, name="work_order_status_enum"),
        nullable=False,
        default=WorkOrderStatus.PLANNED,
        comment="Current lifecycle status of the work order",
    )
    priority = Column(
        Enum(WorkOrderPriority, name="work_order_priority_enum"),
        nullable=False,
        default=WorkOrderPriority.NORMAL,
        comment="Manufacturing priority level",
    )

    # ------------------------------------------------------------------
    # Assignment
    # ------------------------------------------------------------------
    assigned_team = Column(
        String(200),
        nullable=True,
        comment="Name or code of the manufacturing team / shift assigned to this WO",
    )
    manufacturing_line = Column(
        String(100),
        nullable=True,
        comment="Equipment line or room where manufacturing takes place",
    )

    # ------------------------------------------------------------------
    # Master Batch Record link
    # ------------------------------------------------------------------
    master_batch_record_id = Column(
        UUID(as_uuid=False),
        ForeignKey("master_batch_records.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Master Batch Record from which this work order is derived",
    )

    # ------------------------------------------------------------------
    # Cancellation / hold
    # ------------------------------------------------------------------
    hold_reason = Column(
        Text,
        nullable=True,
        comment="Reason for placing the work order on hold",
    )
    cancellation_reason = Column(
        Text,
        nullable=True,
        comment="Reason for cancellation (populated when status = cancelled)",
    )

    # ------------------------------------------------------------------
    # Organisational context
    # ------------------------------------------------------------------
    organisation_id = Column(
        UUID(as_uuid=False),
        nullable=False,
        comment="Owning organisation UUID",
    )
    site_id = Column(
        UUID(as_uuid=False),
        nullable=True,
        comment="Manufacturing site UUID",
    )

    # ------------------------------------------------------------------
    # Personnel
    # ------------------------------------------------------------------
    created_by_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="User who created this work order",
    )
    released_by_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        comment="User who released the work order to the shop floor",
    )
    released_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of work order release",
    )

    # ------------------------------------------------------------------
    # Flexible metadata store
    # ------------------------------------------------------------------
    metadata_ = Column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
        comment="Arbitrary key-value metadata (ERP order ref, customer order, etc.)",
    )

    # ------------------------------------------------------------------
    # ALCOA+ audit timestamps
    # ------------------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Soft-delete flag",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    materials = relationship(
        "WorkOrderMaterial",
        back_populates="work_order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="WorkOrderMaterial.material_name",
    )

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        UniqueConstraint(
            "organisation_id",
            "work_order_number",
            name="uq_work_orders_org_number",
        ),
        CheckConstraint(
            "scheduled_end >= scheduled_start",
            name="ck_work_orders_schedule_order",
        ),
        CheckConstraint(
            "planned_quantity > 0",
            name="ck_work_orders_positive_quantity",
        ),
        Index("ix_work_orders_org_status", "organisation_id", "status"),
        Index("ix_work_orders_scheduled_start", "scheduled_start"),
        Index("ix_work_orders_product", "product_code", "status"),
        Index("ix_work_orders_mbr", "master_batch_record_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<WorkOrder id={self.id!r} "
            f"number={self.work_order_number!r} "
            f"product={self.product_name!r} status={self.status!r}>"
        )


# ---------------------------------------------------------------------------
# WorkOrderMaterial
# ---------------------------------------------------------------------------


class WorkOrderMaterial(Base):
    """
    Material / component line item associated with a WorkOrder.

    Captures the full dispensing audit trail for every material used in a
    manufacturing run:
      - What was planned (material_name, material_code, quantity_required)
      - What was actually dispensed (quantity_dispensed, dispensed_by_id, dispensed_at)
      - Lot traceability (lot_number) for forward/backward traceability
      - Reconciliation status (returned / destroyed quantities)

    GMP requirement: every material consumed must be uniquely identified by
    its internal material code AND the supplier lot/batch number.  Both
    fields are therefore required before dispensing can be recorded.
    """

    __tablename__ = "work_order_materials"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=new_uuid,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Foreign key
    # ------------------------------------------------------------------
    work_order_id = Column(
        UUID(as_uuid=False),
        ForeignKey("work_orders.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent work order",
    )

    # ------------------------------------------------------------------
    # Material identity
    # ------------------------------------------------------------------
    material_name = Column(
        String(255),
        nullable=False,
        comment="Full name of the material or component",
    )
    material_code = Column(
        String(100),
        nullable=False,
        comment="Internal material / item code from the materials master",
    )
    lot_number = Column(
        String(100),
        nullable=False,
        comment="Supplier or internal lot / batch number for full traceability",
    )
    supplier_id = Column(
        UUID(as_uuid=False),
        nullable=True,
        comment="Optional FK to the Supplier record for this material lot",
    )

    # ------------------------------------------------------------------
    # Quantities
    # ------------------------------------------------------------------
    quantity_required = Column(
        Float,
        nullable=False,
        comment="Quantity called for by the batch record formula",
    )
    quantity_dispensed = Column(
        Float,
        nullable=True,
        comment="Actual quantity weighed / measured and dispensed",
    )
    quantity_returned = Column(
        Float,
        nullable=True,
        default=0.0,
        comment="Quantity returned to stock after use (reconciliation)",
    )
    quantity_destroyed = Column(
        Float,
        nullable=True,
        default=0.0,
        comment="Quantity destroyed / discarded (reconciliation)",
    )
    unit = Column(
        String(50),
        nullable=False,
        comment="Unit of measure (e.g. 'kg', 'g', 'mL', 'units')",
    )

    # ------------------------------------------------------------------
    # Dispensing details
    # ------------------------------------------------------------------
    dispensed_by_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        comment="User who performed the dispensing",
    )
    dispensed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of dispensing (populated when material is issued)",
    )
    verified_by_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Second person who independently verified the dispensed quantity",
    )
    verified_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of independent verification",
    )
    status = Column(
        Enum(MaterialStatus, name="material_status_enum"),
        nullable=False,
        default=MaterialStatus.PENDING,
        comment="Current dispensing / reconciliation status",
    )

    # ------------------------------------------------------------------
    # Tolerance check
    # ------------------------------------------------------------------
    tolerance_percent = Column(
        Float,
        nullable=True,
        comment="Allowed dispensing tolerance as a percentage of quantity_required",
    )
    tolerance_breach = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="True if the dispensed quantity falls outside the allowed tolerance",
    )

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------
    notes = Column(
        Text,
        nullable=True,
        comment="Any operator notes relating to this material line",
    )

    # ------------------------------------------------------------------
    # ALCOA+ audit timestamps
    # ------------------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    is_active = Column(Boolean, nullable=False, default=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    work_order = relationship("WorkOrder", back_populates="materials")

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        CheckConstraint(
            "quantity_required > 0",
            name="ck_wo_materials_positive_required",
        ),
        CheckConstraint(
            "quantity_dispensed IS NULL OR quantity_dispensed >= 0",
            name="ck_wo_materials_non_negative_dispensed",
        ),
        Index(
            "ix_work_order_materials_work_order",
            "work_order_id",
        ),
        Index(
            "ix_work_order_materials_lot",
            "material_code",
            "lot_number",
        ),
        Index(
            "ix_work_order_materials_status",
            "work_order_id",
            "status",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<WorkOrderMaterial id={self.id!r} "
            f"material={self.material_code!r} "
            f"lot={self.lot_number!r} status={self.status!r}>"
        )
