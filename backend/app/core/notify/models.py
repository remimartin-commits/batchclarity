"""
Notification models — email, WhatsApp, SMS alerts for GMP events.
All notifications are logged for audit trail purposes.
"""
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


class NotificationTemplate(Base):
    """
    Reusable templates for GMP event notifications.
    e.g. "CAPA overdue", "Batch record ready for QA review", "Calibration due in 7 days"
    """
    __tablename__ = "notification_templates"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # Event types: capa.overdue | capa.approved | deviation.created | batch.ready_for_review
    # calibration.due | training.overdue | change_control.approved | document.effective

    channels: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Channels: ["email", "whatsapp", "sms"]

    subject_template: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    # Template variables: {record_number}, {record_title}, {assignee_name}, {due_date}, {site_name}

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class NotificationRule(Base):
    """
    Configures who gets notified for a given event at a given site.
    """
    __tablename__ = "notification_rules"

    template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notification_templates.id"), nullable=False
    )
    site_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sites.id"), nullable=True)
    recipient_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: role | user | department | fixed_address

    recipient_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recipient_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    recipient_address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # For fixed_address: email address or WhatsApp number

    channel: Mapped[str] = mapped_column(String(50), nullable=False, default="email")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    template: Mapped["NotificationTemplate"] = relationship("NotificationTemplate")


class NotificationLog(Base):
    """Immutable record of every notification sent — part of the audit trail."""
    __tablename__ = "notification_logs"

    template_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("notification_templates.id"), nullable=True
    )
    recipient_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    recipient_address: Mapped[str] = mapped_column(String(300), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)

    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    record_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    record_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    # Statuses: pending | sent | failed | bounced

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)
