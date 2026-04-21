"""
Workflow Engine — configurable state machine for all GMP record lifecycles.

Every GMP record (CAPA, batch record, change control, deviation, SOP) goes through
a defined lifecycle. This engine drives all of them from one place.

Example lifecycle for a CAPA:
  draft -> under_review -> approved -> in_progress -> completed -> closed
       QA review^     ^QA Manager sig    ^Owner sig    ^QA verify

The workflow engine enforces:
  - Only valid state transitions (no jumping from draft to closed)
  - Required electronic signatures before transition
  - Required roles to perform each transition
  - Automatic notifications on transition
  - Due date tracking per state
"""
from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


class WorkflowDefinition(Base):
    """
    A reusable workflow template. One per record type.
    e.g. "CAPA Workflow v2", "Batch Record Workflow v1"
    """
    __tablename__ = "workflow_definitions"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    record_type: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    initial_state: Mapped[str] = mapped_column(String(100), nullable=False)

    states: Mapped[list["WorkflowState"]] = relationship("WorkflowState", back_populates="definition")
    transitions: Mapped[list["WorkflowTransition"]] = relationship("WorkflowTransition", back_populates="definition")
    instances: Mapped[list["WorkflowInstance"]] = relationship("WorkflowInstance", back_populates="definition")


class WorkflowState(Base):
    """A single state within a workflow (e.g. 'draft', 'approved', 'closed')."""
    __tablename__ = "workflow_states"

    definition_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflow_definitions.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False)
    is_initial: Mapped[bool] = mapped_column(Boolean, default=False)
    colour: Mapped[str] = mapped_column(String(20), nullable=True)  # UI badge colour
    default_due_days: Mapped[int | None] = mapped_column(Integer, nullable=True)  # SLA for this state
    requires_overdue_justification: Mapped[bool] = mapped_column(Boolean, default=False)

    definition: Mapped["WorkflowDefinition"] = relationship("WorkflowDefinition", back_populates="states")


class WorkflowTransition(Base):
    """
    A valid state change, with required roles and signature meanings.
    """
    __tablename__ = "workflow_transitions"

    definition_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflow_definitions.id"), nullable=False)
    from_state: Mapped[str] = mapped_column(String(100), nullable=False)
    to_state: Mapped[str] = mapped_column(String(100), nullable=False)
    action_label: Mapped[str] = mapped_column(String(200), nullable=False)  # Button text e.g. "Submit for Review"
    required_roles: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    required_signature_meaning: Mapped[str | None] = mapped_column(String(100), nullable=True)
    requires_reason: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_roles: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    conditions: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Optional rule conditions

    definition: Mapped["WorkflowDefinition"] = relationship("WorkflowDefinition", back_populates="transitions")


class WorkflowInstance(Base):
    """
    A live workflow tracking a specific GMP record through its lifecycle.
    One instance per record.
    """
    __tablename__ = "workflow_instances"

    definition_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflow_definitions.id"), nullable=False)
    record_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    record_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    current_state: Mapped[str] = mapped_column(String(100), nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_overdue: Mapped[bool] = mapped_column(Boolean, default=False)

    definition: Mapped["WorkflowDefinition"] = relationship("WorkflowDefinition", back_populates="instances")
    history: Mapped[list["WorkflowHistoryEntry"]] = relationship("WorkflowHistoryEntry", back_populates="instance")


class WorkflowHistoryEntry(Base):
    """Immutable record of every state transition for a workflow instance."""
    __tablename__ = "workflow_history"

    instance_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflow_instances.id"), nullable=False)
    from_state: Mapped[str] = mapped_column(String(100), nullable=False)
    to_state: Mapped[str] = mapped_column(String(100), nullable=False)
    transitioned_by_id: Mapped[str] = mapped_column(String(36), nullable=False)
    transitioned_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    transitioned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    signature_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("electronic_signatures.id"), nullable=True)

    instance: Mapped["WorkflowInstance"] = relationship("WorkflowInstance", back_populates="history")
