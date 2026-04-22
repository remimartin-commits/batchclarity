"""Notify module public API (alias; implementation lives in service.py)."""
from app.core.notify.service import NotificationService

__all__ = ["NotificationService"]
