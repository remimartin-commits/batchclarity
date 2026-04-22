"""Seed script — populates the GMP Platform database with initial data.

Usage (from the backend directory):
    uv run python -m scripts.seed
    # or
    uv run python scripts/seed.py

Creates:
  - Default site (Main Site / MAIN / Switzerland / EU GMP Annex 11)
  - All system permissions (grouped by module)
  - All system roles with permission assignments
  - Admin user (username=admin, password=Admin@GMP2024!)
  - Document types (SOP, WI, FRM, POL, VAL, SPEC, URS, RPT, MBR, QMP)
  - Workflow definitions (CAPA, Deviation, Change Control, Batch Record)
  - Notification templates for all key GMP events

SECURITY NOTE:
  The default admin password MUST be changed on first login.
  The system sets must_change_password=True to enforce this.
"""
import asyncio
import os
import sys

# Ensure the backend directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.database import Base, _async_postgres_url
from app.core.auth.models import (
    User,
    Role,
    Permission,
    Site,
    Organisation,
    role_permissions,
    user_roles,
)
from app.core.auth.service import AuthService
from app.core.workflow.models import WorkflowDefinition, WorkflowState, WorkflowTransition
from app.core.notify.models import NotificationRule, NotificationTemplate
from app.core.documents.models import DocumentType

# Import all models to ensure Base.metadata is fully populated
import app.core.auth.models  # noqa: F401
import app.core.audit.models  # noqa: F401
import app.core.esig.models  # noqa: F401
import app.core.workflow.models  # noqa: F401
import app.core.notify.models  # noqa: F401
import app.core.documents.models  # noqa: F401
import app.modules.qms.models  # noqa: F401
import app.modules.mes.models  # noqa: F401
import app.modules.equipment.models  # noqa: F401
import app.modules.training.models  # noqa: F401
import app.modules.env_monitoring.models  # noqa: F401
import app.modules.lims.models  # noqa: F401
import app.core.integration.models  # noqa: F401


# ── Permission definitions ─────────────────────────────────────────────────────
SYSTEM_PERMISSIONS: list[tuple[str, str]] = [
    # QMS
    ("qms.capa.view",                   "View CAPAs"),
    ("qms.capa.create",                 "Create CAPAs"),
    ("qms.capa.edit",                   "Edit CAPAs"),
    ("qms.capa.approve",                "Approve CAPAs"),
    ("qms.deviation.view",              "View Deviations"),
    ("qms.deviation.create",            "Create Deviations"),
    ("qms.deviation.approve",           "Approve Deviations"),
    ("qms.change_control.view",         "View Change Controls"),
    ("qms.change_control.create",       "Create Change Controls"),
    ("qms.change_control.approve",      "Approve Change Controls"),
    # MES
    ("mes.product.view",                "View Products"),
    ("mes.product.create",              "Create Products"),
    ("mes.mbr.view",                    "View Master Batch Records"),
    ("mes.mbr.create",                  "Create Master Batch Records"),
    ("mes.mbr.approve",                 "Approve Master Batch Records"),
    ("mes.batch.view",                  "View Batch Records"),
    ("mes.batch.create",                "Create Batch Records"),
    ("mes.batch.execute",               "Execute Batch Steps"),
    ("mes.batch.release",               "Release Batch Records"),
    # Equipment
    ("equipment.view",                  "View Equipment"),
    ("equipment.create",                "Create Equipment Records"),
    ("equipment.calibrate",             "Record Calibrations"),
    ("equipment.qualify",               "Record Qualifications (IQ/OQ/PQ)"),
    ("equipment.maintain",              "Record Maintenance Activities"),
    # Training
    ("training.curriculum.view",        "View Training Curricula"),
    ("training.curriculum.create",      "Create Training Curricula"),
    ("training.assignment.view",        "View Training Assignments"),
    ("training.assignment.create",      "Create Training Assignments"),
    ("training.completion.record",      "Record Training Completion"),
    # Documents
    ("documents.view",                  "View Controlled Documents"),
    ("documents.create",                "Create Documents and Versions"),
    ("documents.approve",               "Approve Document Versions"),
    # Environmental Monitoring
    ("env_monitoring.view",             "View Environmental Monitoring Results"),
    ("env_monitoring.create",           "Record EM Results"),
    ("env_monitoring.manage",           "Manage EM Locations and Alert Limits"),
    # LIMS
    ("lims.sample.view",                "View Samples"),
    ("lims.sample.create",              "Create Samples"),
    ("lims.result.create",              "Record Test Results"),
    ("lims.result.review",              "Review Test Results (OOS/OOT determination)"),
    ("lims.oos.investigate",            "Investigate OOS Results"),
    # Administration
    ("admin.users.manage",              "Manage User Accounts"),
    ("admin.roles.manage",              "Manage Roles and Permissions"),
    ("admin.system.configure",          "Configure System Settings"),
    ("admin.audit.view",                "View Full Audit Trail"),
    ("admin.workflow.manage",           "Manage Workflow Definitions"),
]


# ── Role definitions ───────────────────────────────────────────────────────────
SYSTEM_ROLES: list[dict] = [
    {
        "name": "Administrator",
        "code": "admin",
        "description": "Full system access — IT and System Administrator",
        "is_system_role": True,
        "permissions": [p[0] for p in SYSTEM_PERMISSIONS],  # all permissions
    },
    {
        "name": "QA Manager",
        "code": "qa_manager",
        "description": "Quality Assurance Manager — full QMS access and approval authority",
        "is_system_role": True,
        "permissions": [
            "qms.capa.view", "qms.capa.create", "qms.capa.edit", "qms.capa.approve",
            "qms.deviation.view", "qms.deviation.create", "qms.deviation.approve",
            "qms.change_control.view", "qms.change_control.create", "qms.change_control.approve",
            "mes.product.view", "mes.mbr.view", "mes.mbr.approve",
            "mes.batch.view", "mes.batch.release",
            "equipment.view", "equipment.qualify",
            "training.curriculum.view", "training.assignment.view",
            "documents.view", "documents.create", "documents.approve",
            "env_monitoring.view", "env_monitoring.manage",
            "lims.sample.view", "lims.result.review", "lims.oos.investigate",
            "admin.audit.view",
        ],
    },
    {
        "name": "QA Specialist",
        "code": "qa_specialist",
        "description": "Quality Assurance Specialist — investigation and documentation",
        "is_system_role": True,
        "permissions": [
            "qms.capa.view", "qms.capa.create", "qms.capa.edit",
            "qms.deviation.view", "qms.deviation.create",
            "qms.change_control.view", "qms.change_control.create",
            "mes.batch.view", "mes.mbr.view",
            "equipment.view",
            "training.curriculum.view", "training.assignment.view",
            "documents.view", "documents.create",
            "env_monitoring.view",
            "lims.sample.view", "lims.result.review", "lims.oos.investigate",
            "admin.audit.view",
        ],
    },
    {
        "name": "Manufacturing Operator",
        "code": "manufacturing_operator",
        "description": "Manufacturing floor operator — execute batch record steps",
        "is_system_role": True,
        "permissions": [
            "mes.product.view", "mes.mbr.view",
            "mes.batch.view", "mes.batch.create", "mes.batch.execute",
            "equipment.view",
            "training.curriculum.view", "training.assignment.view", "training.completion.record",
            "documents.view",
            "qms.deviation.create",
        ],
    },
    {
        "name": "Equipment Manager",
        "code": "equipment_manager",
        "description": "Equipment and Calibration Manager",
        "is_system_role": True,
        "permissions": [
            "equipment.view", "equipment.create",
            "equipment.calibrate", "equipment.qualify", "equipment.maintain",
            "documents.view",
            "qms.deviation.create",
            "training.curriculum.view", "training.assignment.view",
        ],
    },
    {
        "name": "Training Coordinator",
        "code": "training_coordinator",
        "description": "Training and Competency Coordinator",
        "is_system_role": True,
        "permissions": [
            "training.curriculum.view", "training.curriculum.create",
            "training.assignment.view", "training.assignment.create",
            "training.completion.record",
            "documents.view",
        ],
    },
    {
        "name": "LIMS Analyst",
        "code": "lims_analyst",
        "description": "Laboratory analyst — sample testing and result entry",
        "is_system_role": True,
        "permissions": [
            "lims.sample.view", "lims.sample.create",
            "lims.result.create", "lims.result.review",
            "lims.oos.investigate",
            "documents.view",
            "qms.deviation.create",
        ],
    },
    {
        "name": "Environmental Monitoring Technician",
        "code": "env_monitoring_tech",
        "description": "EM sampling and data entry technician",
        "is_system_role": True,
        "permissions": [
            "env_monitoring.view", "env_monitoring.create",
            "documents.view",
            "qms.deviation.create",
        ],
    },
]


# ── Document types ─────────────────────────────────────────────────────────────
DOCUMENT_TYPES: list[tuple[str, str, int | None]] = [
    ("SOP",   "Standard Operating Procedure",       24),
    ("WI",    "Work Instruction",                   24),
    ("FRM",   "Form / Template",                    12),
    ("POL",   "Policy",                             36),
    ("VAL",   "Validation Document",                60),
    ("SPEC",  "Specification",                      24),
    ("URS",   "User Requirements Specification",    60),
    ("RPT",   "Report",                             None),
    ("MBR",   "Master Batch Record",                12),
    ("QMP",   "Quality Manual / Plan",              36),
    ("PV",    "Process Validation Protocol",        60),
    ("STP",   "Stability Testing Protocol",         12),
]


# ── Workflow definitions ───────────────────────────────────────────────────────
WORKFLOW_DEFINITIONS: list[dict] = [
    {
        "name": "CAPA Lifecycle",
        "entity_type": "capa",
        "version": "1.0",
        "states": [
            {"name": "Draft",                "code": "draft",               "is_initial": True,  "is_final": False, "color": "#6B7280"},
            {"name": "Under Review",          "code": "under_review",        "is_initial": False, "is_final": False, "color": "#F59E0B"},
            {"name": "Approved",              "code": "approved",            "is_initial": False, "is_final": False, "color": "#3B82F6"},
            {"name": "Work In Progress",      "code": "wip",                 "is_initial": False, "is_final": False, "color": "#8B5CF6"},
            {"name": "Effectiveness Check",   "code": "effectiveness_check", "is_initial": False, "is_final": False, "color": "#F97316"},
            {"name": "Closed",                "code": "closed",              "is_initial": False, "is_final": True,  "color": "#10B981"},
            {"name": "Cancelled",             "code": "cancelled",           "is_initial": False, "is_final": True,  "color": "#EF4444"},
        ],
        "transitions": [
            {"from": "draft",               "to": "under_review",        "trigger": "submit_for_review",    "roles": ["qa_specialist","qa_manager","admin"],                              "reason": False},
            {"from": "under_review",        "to": "approved",            "trigger": "approve",              "roles": ["qa_manager","admin"],                                             "reason": False, "sig": "approved"},
            {"from": "under_review",        "to": "draft",               "trigger": "return_to_draft",      "roles": ["qa_manager","admin"],                                             "reason": True},
            {"from": "approved",            "to": "wip",                 "trigger": "start_actions",        "roles": ["qa_specialist","qa_manager","manufacturing_operator","admin"],    "reason": False},
            {"from": "wip",                 "to": "effectiveness_check", "trigger": "actions_complete",     "roles": ["qa_specialist","qa_manager","admin"],                             "reason": False},
            {"from": "effectiveness_check", "to": "closed",              "trigger": "close",                "roles": ["qa_manager","admin"],                                             "reason": False, "sig": "approved"},
            {"from": "effectiveness_check", "to": "wip",                 "trigger": "reopen",               "roles": ["qa_manager","admin"],                                             "reason": True},
            {"from": "draft",               "to": "cancelled",           "trigger": "cancel",               "roles": ["qa_manager","admin"],                                             "reason": True},
        ],
    },
    {
        "name": "Deviation Lifecycle",
        "entity_type": "deviation",
        "version": "1.0",
        "states": [
            {"name": "Open",                  "code": "open",                "is_initial": True,  "is_final": False, "color": "#EF4444"},
            {"name": "Under Investigation",   "code": "under_investigation", "is_initial": False, "is_final": False, "color": "#F59E0B"},
            {"name": "Pending Review",        "code": "pending_review",      "is_initial": False, "is_final": False, "color": "#3B82F6"},
            {"name": "Closed",                "code": "closed",              "is_initial": False, "is_final": True,  "color": "#10B981"},
        ],
        "transitions": [
            {"from": "open",               "to": "under_investigation", "trigger": "start_investigation", "roles": ["qa_specialist","qa_manager","admin"], "reason": False},
            {"from": "under_investigation","to": "pending_review",      "trigger": "submit_for_review",   "roles": ["qa_specialist","qa_manager","admin"], "reason": False},
            {"from": "pending_review",     "to": "closed",              "trigger": "close",               "roles": ["qa_manager","admin"],                 "reason": False, "sig": "approved"},
            {"from": "pending_review",     "to": "under_investigation", "trigger": "return",              "roles": ["qa_manager","admin"],                 "reason": True},
        ],
    },
    {
        "name": "Change Control Lifecycle",
        "entity_type": "change_control",
        "version": "1.0",
        "states": [
            {"name": "Draft",              "code": "draft",            "is_initial": True,  "is_final": False, "color": "#6B7280"},
            {"name": "Pending Approval",   "code": "pending_approval", "is_initial": False, "is_final": False, "color": "#F59E0B"},
            {"name": "Approved",           "code": "approved",         "is_initial": False, "is_final": False, "color": "#3B82F6"},
            {"name": "Implementation",     "code": "implementation",   "is_initial": False, "is_final": False, "color": "#8B5CF6"},
            {"name": "Closed",             "code": "closed",           "is_initial": False, "is_final": True,  "color": "#10B981"},
            {"name": "Rejected",           "code": "rejected",         "is_initial": False, "is_final": True,  "color": "#EF4444"},
        ],
        "transitions": [
            {"from": "draft",          "to": "pending_approval", "trigger": "submit",                "roles": ["qa_specialist","qa_manager","admin"], "reason": False},
            {"from": "pending_approval","to": "approved",         "trigger": "approve",               "roles": ["qa_manager","admin"],                 "reason": False, "sig": "approved"},
            {"from": "pending_approval","to": "rejected",         "trigger": "reject",                "roles": ["qa_manager","admin"],                 "reason": True},
            {"from": "approved",       "to": "implementation",   "trigger": "start_implementation",  "roles": ["qa_specialist","qa_manager","admin"], "reason": False},
            {"from": "implementation", "to": "closed",           "trigger": "close",                 "roles": ["qa_manager","admin"],                 "reason": False, "sig": "approved"},
            {"from": "implementation", "to": "approved",         "trigger": "return_to_approved",    "roles": ["qa_manager","admin"],                 "reason": True},
        ],
    },
    {
        "name": "Batch Record Lifecycle",
        "entity_type": "batch_record",
        "version": "1.0",
        "states": [
            {"name": "In Progress",      "code": "in_progress",     "is_initial": True,  "is_final": False, "color": "#3B82F6"},
            {"name": "Pending Release",  "code": "pending_release", "is_initial": False, "is_final": False, "color": "#F59E0B"},
            {"name": "Released",         "code": "released",        "is_initial": False, "is_final": True,  "color": "#10B981"},
            {"name": "Rejected",         "code": "rejected",        "is_initial": False, "is_final": True,  "color": "#EF4444"},
        ],
        "transitions": [
            {"from": "in_progress",    "to": "pending_release", "trigger": "submit_for_release",   "roles": ["manufacturing_operator","qa_specialist","qa_manager","admin"], "reason": False},
            {"from": "pending_release","to": "released",        "trigger": "release",              "roles": ["qa_manager","admin"],                                         "reason": False, "sig": "approved"},
            {"from": "pending_release","to": "rejected",        "trigger": "reject",               "roles": ["qa_manager","admin"],                                         "reason": True},
            {"from": "pending_release","to": "in_progress",     "trigger": "return_for_correction","roles": ["qa_manager","admin"],                                         "reason": True},
        ],
    },
    {
        "name": "Document Version Lifecycle",
        "entity_type": "document_version",
        "version": "1.0",
        "states": [
            {"name": "Draft",       "code": "draft",     "is_initial": True,  "is_final": False, "color": "#6B7280"},
            {"name": "In Review",   "code": "in_review", "is_initial": False, "is_final": False, "color": "#F59E0B"},
            {"name": "Approved",    "code": "approved",  "is_initial": False, "is_final": True,  "color": "#10B981"},
            {"name": "Obsolete",    "code": "obsolete",  "is_initial": False, "is_final": True,  "color": "#9CA3AF"},
        ],
        "transitions": [
            {"from": "draft",     "to": "in_review", "trigger": "submit_for_review", "roles": ["qa_specialist","qa_manager","admin"],        "reason": False},
            {"from": "in_review", "to": "approved",  "trigger": "approve",           "roles": ["qa_manager","admin"],                         "reason": False, "sig": "approved"},
            {"from": "in_review", "to": "draft",     "trigger": "return_to_draft",   "roles": ["qa_manager","admin"],                         "reason": True},
            {"from": "approved",  "to": "obsolete",  "trigger": "obsolete",          "roles": ["qa_manager","admin"],                         "reason": True},
        ],
    },
]


# ── Notification templates ─────────────────────────────────────────────────────
NOTIFICATION_TEMPLATES: list[dict] = [
    {
        "code": "CAPA_CREATED",
        "event_type": "capa.created",
        "subject": "New CAPA: {{capa_number}} — {{title}}",
        "body": (
            "A new CAPA has been created and requires your attention.\n\n"
            "CAPA Number: {{capa_number}}\n"
            "Title: {{title}}\n"
            "Risk Level: {{risk_level}}\n"
            "Due Date: {{due_date}}\n"
            "Created By: {{created_by}}\n\n"
            "Please log in to review and take appropriate action."
        ),
        "channels": ["email"],
    },
    {
        "code": "CAPA_APPROVED",
        "event_type": "capa.approved",
        "subject": "CAPA Approved: {{capa_number}}",
        "body": (
            "CAPA {{capa_number}} has been approved. Actions may now begin.\n\n"
            "Title: {{title}}\n"
            "Approved By: {{approved_by}}\n"
            "Approved At: {{approved_at}}"
        ),
        "channels": ["email"],
    },
    {
        "code": "CAPA_OVERDUE",
        "event_type": "capa.overdue",
        "subject": "OVERDUE — CAPA {{capa_number}} requires immediate attention",
        "body": (
            "⚠ CAPA {{capa_number}} is OVERDUE.\n\n"
            "Title: {{title}}\n"
            "Due Date: {{due_date}}\n"
            "Current Status: {{status}}\n"
            "Owner: {{owner}}\n\n"
            "Immediate escalation required."
        ),
        "channels": ["email"],
    },
    {
        "code": "DEVIATION_CREATED",
        "event_type": "deviation.created",
        "subject": "New Deviation: {{deviation_number}}",
        "body": (
            "A new deviation has been recorded.\n\n"
            "Deviation Number: {{deviation_number}}\n"
            "Severity: {{severity}}\n"
"Description: {{description}}\n"
            "Detected By: {{detected_by}}\n"
            "Date: {{detected_date}}"
        ),
        "channels": ["email"],
    },
    {
        "code": "BATCH_RELEASED",
        "event_type": "batch_record.released",
        "subject": "Batch Released: {{batch_number}}",
        "body": (
            "Batch record {{batch_number}} has been released for distribution.\n\n"
            "Product: {{product_name}}\n"
            "Batch Size: {{batch_size}} {{batch_size_unit}}\n"
            "Released By: {{released_by}}\n"
            "Released At: {{released_at}}"
        ),
        "channels": ["email"],
    },
    {
        "code": "BATCH_REJECTED",
        "event_type": "batch_record.rejected",
        "subject": "BATCH REJECTED: {{batch_number}}",
        "body": (
            "⚠ Batch record {{batch_number}} has been REJECTED.\n\n"
            "Product: {{product_name}}\n"
            "Rejection Reason: {{reject_reason}}\n"
            "Rejected By: {{rejected_by}}\n"
            "Rejected At: {{rejected_at}}\n\n"
            "Initiate a deviation investigation immediately."
        ),
        "channels": ["email"],
    },
    {
        "code": "CALIBRATION_DUE",
        "event_type": "equipment.calibration_due",
        "subject": "Calibration Due: {{equipment_code}} — {{equipment_name}}",
        "body": (
            "Equipment calibration is due within 30 days.\n\n"
            "Equipment ID: {{equipment_code}}\n"
            "Equipment Name: {{equipment_name}}\n"
            "Calibration Due: {{due_date}}\n"
            "Last Calibrated: {{last_calibrated}}\n\n"
            "Schedule calibration with your metrology provider."
        ),
        "channels": ["email"],
    },
    {
        "code": "CALIBRATION_OVERDUE",
        "event_type": "equipment.calibration_overdue",
        "subject": "CALIBRATION OVERDUE: {{equipment_code}}",
        "body": (
            "⚠ Equipment calibration is OVERDUE. Equipment must not be used.\n\n"
            "Equipment ID: {{equipment_code}}\n"
            "Equipment Name: {{equipment_name}}\n"
            "Calibration Was Due: {{due_date}}\n\n"
            "Place equipment on hold and initiate a deviation."
        ),
        "channels": ["email"],
    },
    {
        "code": "OOS_RESULT",
        "event_type": "lims.oos_result",
        "subject": "OOS Result: Sample {{sample_number}} — {{test_name}}",
        "body": (
            "An Out-Of-Specification (OOS) result has been detected.\n\n"
            "Sample Number: {{sample_number}}\n"
            "Test: {{test_name}}\n"
            "Result: {{result_value}} {{unit}}\n"
            "Specification: {{lower_limit}} – {{upper_limit}} {{unit}}\n"
            "Analyst: {{analyst}}\n\n"
            "A Phase 1 OOS investigation has been opened automatically.\n"
            "Review the investigation and proceed per your OOS procedure."
        ),
        "channels": ["email"],
    },
    {
        "code": "ENV_ACTION_LIMIT",
        "event_type": "env_monitoring.action_limit_exceeded",
        "subject": "ACTION LIMIT EXCEEDED: {{location_code}} — {{parameter}}",
        "body": (
            "⚠ Environmental monitoring ACTION LIMIT exceeded.\n\n"
            "Location: {{location_code}} — {{location_name}}\n"
            "GMP Grade: {{gmp_grade}}\n"
            "Parameter: {{parameter}}\n"
            "Result: {{result_value}} {{unit}}\n"
            "Action Limit: {{action_limit}} {{unit}}\n"
            "Sampled By: {{sampled_by}}\n\n"
            "Immediate investigation required. Initiate a deviation."
        ),
        "channels": ["email"],
    },
    {
        "code": "ENV_ALERT_LIMIT",
        "event_type": "env_monitoring.alert_limit_exceeded",
        "subject": "Alert Limit Exceeded: {{location_code}} — {{parameter}}",
        "body": (
            "Environmental monitoring ALERT LIMIT exceeded.\n\n"
            "Location: {{location_code}} — {{location_name}}\n"
            "GMP Grade: {{gmp_grade}}\n"
            "Parameter: {{parameter}}\n"
            "Result: {{result_value}} {{unit}}\n"
            "Alert Limit: {{alert_limit}} {{unit}}\n"
            "Sampled By: {{sampled_by}}\n\n"
            "Investigate trending and document findings."
        ),
        "channels": ["email"],
    },
    {
        "code": "TRAINING_DUE",
        "event_type": "training.assignment_due",
        "subject": "Training Due: {{curriculum_name}}",
        "body": (
            "You have a training assignment due soon.\n\n"
            "Curriculum: {{curriculum_name}}\n"
            "Due Date: {{due_date}}\n"
            "Assigned By: {{assigned_by}}\n\n"
            "Please complete your training before the due date to maintain compliance."
        ),
        "channels": ["email"],
    },
    {
        "code": "TRAINING_OVERDUE",
        "event_type": "training.assignment_overdue",
        "subject": "TRAINING OVERDUE: {{curriculum_name}}",
        "body": (
            "⚠ Training assignment is OVERDUE.\n\n"
            "Employee: {{employee_name}}\n"
            "Curriculum: {{curriculum_name}}\n"
            "Due Date: {{due_date}}\n\n"
            "This may affect the employee's authorisation to perform GMP activities.\n"
            "Escalate to the Training Coordinator immediately."
        ),
        "channels": ["email"],
    },
    {
        "code": "DOCUMENT_APPROVED",
        "event_type": "documents.version_approved",
        "subject": "Document Approved: {{document_number}} v{{version_number}}",
        "body": (
            "A document version has been approved and is now effective.\n\n"
            "Document: {{document_number}} — {{title}}\n"
            "Version: {{version_number}}\n"
            "Effective Date: {{effective_date}}\n"
            "Approved By: {{approved_by}}\n\n"
            "Previous version has been superseded."
        ),
        "channels": ["email"],
    },
    {
        "code": "DOCUMENT_REVIEW_DUE",
        "event_type": "documents.review_due",
        "subject": "Document Review Due: {{document_number}}",
        "body": (
            "A controlled document is due for periodic review.\n\n"
            "Document: {{document_number}} — {{title}}\n"
            "Review Due: {{review_due_date}}\n"
            "Document Owner: {{owner}}\n\n"
            "Please initiate the document review process."
        ),
        "channels": ["email"],
    },
    # Codes below match NotificationService.send_rule_based(rule_code) used by scheduler hooks
    {
        "code": "qms_capa_overdue",
        "event_type": "capa.batch_overdue_check",
        "name": "CAPA overdue (batch scheduler)",
        "subject": "OVERDUE: {{count}} open CAPA(s) at site",
        "body": (
            "The periodic overdue check found {{count}} CAPA(s) past target completion "
            "and not in a terminal status.\n\n"
            "Site ID: {{site_id}}\n\n"
            "Review the CAPA register and assign owners where needed."
        ),
        "channels": ["email"],
    },
    {
        "code": "equipment_calibration_overdue",
        "event_type": "equipment.batch_calibration_overdue",
        "name": "Calibration overdue (batch scheduler)",
        "subject": "CALIBRATION OVERDUE: {{count}} equipment item(s)",
        "body": (
            "The periodic check found {{count}} calibration(s) that are past due.\n\n"
            "Site ID: {{site_id}}\n\n"
            "Place affected equipment on hold per procedure until calibration is current."
        ),
        "channels": ["email"],
    },
    {
        "code": "training_assignment_overdue",
        "event_type": "training.batch_assignment_overdue",
        "name": "Training overdue (batch scheduler)",
        "subject": "TRAINING OVERDUE: {{count}} assignment(s)",
        "body": (
            "The periodic check found {{count}} training assignment(s) that are past due.\n\n"
            "Site ID: {{site_id}}\n\n"
            "Notify supervisors and the training coordinator to restore compliance."
        ),
        "channels": ["email"],
    },
    {
        "code": "document_review_due",
        "event_type": "documents.batch_review_due",
        "name": "Document periodic review (batch scheduler)",
        "subject": "Document review attention: {{count}} item(s)",
        "body": (
            "The periodic check found {{count}} document review(s) that require action.\n\n"
            "Site ID: {{site_id}}\n\n"
            "Initiate or complete periodic reviews per your document control procedure."
        ),
        "channels": ["email"],
    },
    {
        "code": "env_monitoring_review_overdue",
        "event_type": "env_monitoring.batch_trend_review_overdue",
        "name": "EM trend review overdue (batch scheduler)",
        "subject": "ENV monitoring: {{count}} trend review(s) overdue",
        "body": (
            "The periodic check found {{count}} environmental monitoring trend period(s) "
            "that ended but are not yet reviewed.\n\n"
            "Site ID: {{site_id}}\n\n"
            "Complete trend reviews per your EM program."
        ),
        "channels": ["email"],
    },
    {
        "code": "lims_oos_investigation_stale",
        "event_type": "lims.oos_investigation_stale",
        "name": "LIMS: OOS investigation open more than 14 days",
        "subject": "LIMS: {{count}} OOS investigation(s) open past 14 days",
        "body": (
            "The LIMS OOS check found {{count}} out-of-specification investigation(s) "
            "that are not closed and are older than 14 days.\n\n"
            "Site scope: {{site_id}}\n\n"
            "Review, escalate, or close per laboratory investigation SOP."
        ),
        "channels": ["email"],
    },
]


# ── Seed function ──────────────────────────────────────────────────────────────
async def seed() -> None:
    engine = create_async_engine(_async_postgres_url(settings.DATABASE_URL), echo=False)

    # Create all tables (idempotent — does not drop existing data)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  ✓ Database schema verified / created")

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:

        # ── 0. Default Organisation (multi-tenant root) ─────────────────────────
        existing = await session.execute(select(Organisation).where(Organisation.code == "DEFAULT"))
        org = existing.scalar_one_or_none()
        if not org:
            org = Organisation(
                name="Default Organisation",
                code="DEFAULT",
                legal_name=None,
                is_active=True,
            )
            session.add(org)
            await session.flush([org])
            print(f"  ✓ Organisation created: {org.name} ({org.code})")
        else:
            print(f"  · Organisation exists: {org.name}")

        # ── 1. Default Site ───────────────────────────────────────────────────
        existing = await session.execute(select(Site).where(Site.code == "MAIN"))
        site = existing.scalar_one_or_none()
        if not site:
            site = Site(
                organisation_id=org.id,
                name="Main Site",
                code="MAIN",
                country="CH",
                gmp_license_number="EU GMP Annex 11 / ICH Q10",
            )
            session.add(site)
            await session.flush([site])
            print(f"  ✓ Site created: {site.name} ({site.code})")
        else:
            print(f"  · Site exists: {site.name}")

        # ── 2. Permissions ────────────────────────────────────────────────────
        perm_map: dict[str, Permission] = {}
        new_perms = 0
        for code, description in SYSTEM_PERMISSIONS:
            existing = await session.execute(select(Permission).where(Permission.code == code))
            perm = existing.scalar_one_or_none()
            if not perm:
                _parts = code.split(".")
                perm = Permission(
                    code=code,
                    description=description,
                    module=_parts[0],
                    resource=_parts[1] if len(_parts) >= 3 else "",
                    action=_parts[-1] if len(_parts) >= 2 else "",
                )
                session.add(perm)
                await session.flush([perm])
                new_perms += 1
            perm_map[code] = perm
        print(f"  ✓ Permissions: {len(perm_map)} total ({new_perms} new)")

        # ── 3. Roles ──────────────────────────────────────────────────────────
        role_map: dict[str, Role] = {}
        for role_def in SYSTEM_ROLES:
            existing = await session.execute(select(Role).where(Role.name == role_def["name"]))
            role = existing.scalar_one_or_none()
            if not role:
                role = Role(
                    name=role_def["name"],
                    description=role_def["description"],
                    is_system_role=role_def.get("is_system_role", False),
                )
                session.add(role)
                await session.flush([role])
                for perm_code in role_def["permissions"]:
                    if perm_code in perm_map:
                        await session.execute(
                            role_permissions.insert().values(
                                role_id=role.id,
                                permission_id=perm_map[perm_code].id,
                            )
                        )
                print(f"  ✓ Role created: {role.name}")
            else:
                print(f"  · Role exists:  {role.name}")
            role_map[role_def["code"]] = role
        await session.flush()

        # ── 4. Admin User ─────────────────────────────────────────────────────
        existing = await session.execute(select(User).where(User.username == "admin"))
        admin = existing.scalar_one_or_none()
        if not admin:
            admin = User(
                username="admin",
                email="admin@gmp-platform.local",
                full_name="System Administrator",
                hashed_password=AuthService.hash_password("Admin@GMP2024!"),
                site_id=site.id,
                is_active=True,
                must_change_password=True,
            )
            session.add(admin)
            await session.flush([admin])
            if "admin" in role_map:
                await session.execute(
                    user_roles.insert().values(
                        user_id=admin.id,
                        role_id=role_map["admin"].id,
                    )
                )
            print("  ✓ Admin user created (username=admin, password=Admin@GMP2024!)")
            print("    ⚠  must_change_password=True — change on first login!")
        else:
            print("  · Admin user exists")

        # ── 5. Document Types ─────────────────────────────────────────────────
        new_types = 0
        for prefix, name, review_months in DOCUMENT_TYPES:
            existing = await session.execute(
                select(DocumentType).where(DocumentType.prefix == prefix)
            )
            if not existing.scalar_one_or_none():
                session.add(DocumentType(
                    code=prefix,
                    name=name,
                    prefix=prefix,
                    review_period_months=review_months if review_months is not None else 0,
                ))
                new_types += 1
        await session.flush()
        print(f"  ✓ Document types: {len(DOCUMENT_TYPES)} total ({new_types} new)")

        # ── 6. Workflow Definitions ───────────────────────────────────────────
        for wf_def in WORKFLOW_DEFINITIONS:
            existing = await session.execute(
                select(WorkflowDefinition).where(
                    WorkflowDefinition.record_type == wf_def["entity_type"]
                )
            )
            if existing.scalar_one_or_none():
                print(f"  · Workflow exists: {wf_def['name']}")
                continue

            # Determine initial state code
            initial_code = next(
                (s["code"] for s in wf_def["states"] if s.get("is_initial")),
                wf_def["states"][0]["code"] if wf_def["states"] else "draft"
            )

            wf = WorkflowDefinition(
                name=wf_def["name"],
                code=wf_def["entity_type"],
                record_type=wf_def["entity_type"],
                version=wf_def["version"],
                initial_state=initial_code,
                is_active=True,
            )
            session.add(wf)
            await session.flush([wf])

            for s in wf_def["states"]:
                state = WorkflowState(
                    definition_id=wf.id,
                    display_name=s["name"],
                    code=s["code"],
                    is_initial=s["is_initial"],
                    is_terminal=s["is_final"],
                    colour=s.get("color", "#6B7280"),
                )
                session.add(state)
            await session.flush()

            for t in wf_def["transitions"]:
                session.add(WorkflowTransition(
                    definition_id=wf.id,
                    from_state=t["from"],
                    to_state=t["to"],
                    action_label=t["trigger"],
                    required_roles=t.get("roles", []),
                    requires_reason=t.get("reason", False),
                    required_signature_meaning=t.get("sig"),
                    notify_roles=[],
                ))
            await session.flush()
            print(f"  ✓ Workflow created: {wf_def['name']} ({len(wf_def['states'])} states, {len(wf_def['transitions'])} transitions)")

        # ── 7. Notification Templates ─────────────────────────────────────────
        new_tmpls = 0
        for tmpl_def in NOTIFICATION_TEMPLATES:
            existing = await session.execute(
                select(NotificationTemplate).where(NotificationTemplate.code == tmpl_def["code"])
            )
            if not existing.scalar_one_or_none():
                session.add(NotificationTemplate(
                    code=tmpl_def["code"],
                    name=tmpl_def.get("name", tmpl_def["code"]),
                    event_type=tmpl_def["event_type"],
                    subject_template=tmpl_def.get("subject"),
                    body_template=tmpl_def.get("body", tmpl_def.get("subject", "")),
                    channels=tmpl_def["channels"],
                    is_active=True,
                ))
                new_tmpls += 1
        await session.flush()
        print(f"  ✓ Notification templates: {len(NOTIFICATION_TEMPLATES)} total ({new_tmpls} new)")

        # ── 7b. Rules for scheduler rule_code keys (fixed address → admin email) ──
        scheduler_rule_codes = (
            "qms_capa_overdue",
            "equipment_calibration_overdue",
            "training_assignment_overdue",
            "document_review_due",
            "env_monitoring_review_overdue",
            "lims_oos_investigation_stale",
        )
        admin_user = (
            await session.execute(select(User).where(User.username == "admin"))
        ).scalar_one_or_none()
        if admin_user and admin_user.email:
            new_rules = 0
            for code in scheduler_rule_codes:
                tmpl_row = await session.execute(
                    select(NotificationTemplate).where(NotificationTemplate.code == code)
                )
                tmpl = tmpl_row.scalar_one_or_none()
                if not tmpl:
                    continue
                existing_rule = await session.execute(
                    select(NotificationRule).where(NotificationRule.template_id == tmpl.id)
                )
                if existing_rule.scalars().first():
                    continue
                session.add(
                    NotificationRule(
                        template_id=tmpl.id,
                        site_id=None,
                        recipient_type="fixed_address",
                        recipient_address=admin_user.email,
                        channel="email",
                        is_active=True,
                    )
                )
                new_rules += 1
            await session.flush()
            print(f"  ✓ Scheduler notification rules: {len(scheduler_rule_codes)} templates ({new_rules} new)")

        # ── Commit everything ─────────────────────────────────────────────────
        await session.commit()

    await engine.dispose()

    print("\n" + "=" * 60)
    print("✅  GMP PLATFORM SEED COMPLETE")
    print("=" * 60)
    print(f"   Site:          Main Site (MAIN)")
    print(f"   Permissions:   {len(SYSTEM_PERMISSIONS)}")
    print(f"   Roles:         {len(SYSTEM_ROLES)}")
    print(f"   Workflows:     {len(WORKFLOW_DEFINITIONS)}")
    print(f"   Doc Types:     {len(DOCUMENT_TYPES)}")
    print(f"   Notif. Tmpls:  {len(NOTIFICATION_TEMPLATES)}")
    print()
    print("   Default login: username=admin  password=Admin@GMP2024!")
    print("   ⚠  CHANGE THE ADMIN PASSWORD IMMEDIATELY AFTER FIRST LOGIN")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  GMP PLATFORM — DATABASE SEED")
    print("=" * 60 + "\n")
    asyncio.run(seed())
