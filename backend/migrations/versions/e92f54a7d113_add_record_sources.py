"""add source to excretion and behavior records

Revision ID: e92f54a7d113
Revises: d41c81af0e02
"""

from alembic import op
import sqlalchemy as sa

revision = "e92f54a7d113"
down_revision = "d41c81af0e02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("excretion_records", "behavior_records"):
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(
                sa.Column("source", sa.String(length=20), nullable=False, server_default="manual")
            )
        # Keep the application-level default while avoiding a permanent SQLite server default.
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column("source", server_default=None)


def downgrade() -> None:
    for table in ("behavior_records", "excretion_records"):
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_column("source")
