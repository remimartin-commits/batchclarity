"""Decouple cross-module foreign keys and MES deviation link.

Revision ID: 20260423_decouple_cross_module_fks
Revises: 20260422_auth_mfa_refresh
Create Date: 2026-04-23
"""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260423_decouple_cross_module_fks"
down_revision = "20260422_auth_mfa_refresh"
branch_labels = None
depends_on = None


def _drop_fk_if_exists(table: str, constraint: str) -> None:
    try:
        op.drop_constraint(constraint, table_name=table, type_="foreignkey")
    except Exception:
        # Safe for environments where the FK name differs or was never created.
        pass


def upgrade() -> None:
    # Widen alembic_version.version_num first — default VARCHAR(32) is too
    # short for revision IDs like this one (35 chars). Must run before Alembic
    # writes the new version_num at the end of this migration.
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)")

    # MES -> QMS
    _drop_fk_if_exists("batch_record_steps", "batch_record_steps_deviation_id_fkey")
    op.alter_column("batch_record_steps", "deviation_id", new_column_name="linked_deviation_id")

    # LIMS -> Documents/MES(QMS)
    _drop_fk_if_exists("test_methods", "test_methods_document_id_fkey")
    _drop_fk_if_exists("specifications", "specifications_product_id_fkey")
    _drop_fk_if_exists("specifications", "specifications_document_id_fkey")
    _drop_fk_if_exists("samples", "samples_product_id_fkey")
    _drop_fk_if_exists("oos_investigations", "oos_investigations_linked_capa_id_fkey")

    # ENV monitoring -> QMS
    _drop_fk_if_exists("monitoring_results", "monitoring_results_linked_deviation_id_fkey")
    _drop_fk_if_exists("monitoring_trends", "monitoring_trends_linked_capa_id_fkey")

    # Training -> Documents
    _drop_fk_if_exists("curriculum_items", "curriculum_items_document_id_fkey")
    _drop_fk_if_exists(
        "training_assignments",
        "training_assignments_triggered_by_document_version_id_fkey",
    )

    # Equipment -> Documents
    _drop_fk_if_exists("qualification_records", "qualification_records_protocol_id_fkey")
    _drop_fk_if_exists("qualification_records", "qualification_records_report_id_fkey")


def downgrade() -> None:
    # Column rename rollback
    op.alter_column("batch_record_steps", "linked_deviation_id", new_column_name="deviation_id")

    # Recreate FKs as they existed before decoupling.
    op.create_foreign_key(
        "batch_record_steps_deviation_id_fkey",
        "batch_record_steps",
        "deviations",
        ["deviation_id"],
        ["id"],
    )
    op.create_foreign_key(
        "test_methods_document_id_fkey", "test_methods", "documents", ["document_id"], ["id"]
    )
    op.create_foreign_key(
        "specifications_product_id_fkey", "specifications", "products", ["product_id"], ["id"]
    )
    op.create_foreign_key(
        "specifications_document_id_fkey",
        "specifications",
        "documents",
        ["document_id"],
        ["id"],
    )
    op.create_foreign_key(
        "samples_product_id_fkey", "samples", "products", ["product_id"], ["id"]
    )
    op.create_foreign_key(
        "oos_investigations_linked_capa_id_fkey",
        "oos_investigations",
        "capas",
        ["linked_capa_id"],
        ["id"],
    )
    op.create_foreign_key(
        "monitoring_results_linked_deviation_id_fkey",
        "monitoring_results",
        "deviations",
        ["linked_deviation_id"],
        ["id"],
    )
    op.create_foreign_key(
        "monitoring_trends_linked_capa_id_fkey",
        "monitoring_trends",
        "capas",
        ["linked_capa_id"],
        ["id"],
    )
    op.create_foreign_key(
        "curriculum_items_document_id_fkey",
        "curriculum_items",
        "documents",
        ["document_id"],
        ["id"],
    )
    op.create_foreign_key(
        "training_assignments_triggered_by_document_version_id_fkey",
        "training_assignments",
        "document_versions",
        ["triggered_by_document_version_id"],
        ["id"],
    )
    op.create_foreign_key(
        "qualification_records_protocol_id_fkey",
        "qualification_records",
        "documents",
        ["protocol_id"],
        ["id"],
    )
    op.create_foreign_key(
        "qualification_records_report_id_fkey",
        "qualification_records",
        "documents",
        ["report_id"],
        ["id"],
    )
