"""add daily record tables

Revision ID: d41c81af0e02
Revises: c87f68ff9203
"""

from alembic import op
import sqlalchemy as sa

revision = "d41c81af0e02"
down_revision = "c87f68ff9203"
branch_labels = None
depends_on = None


def _base_columns() -> list[sa.Column]:
    return [
        sa.Column("pet_id", sa.String(length=36), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["pet_id"], ["pets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    ]


def upgrade() -> None:
    op.create_table("feeding_records", *_base_columns(), sa.Column("food_type", sa.String(length=100), nullable=False), sa.Column("amount", sa.Float(), nullable=True), sa.Column("source", sa.String(length=20), nullable=False))
    op.create_table("excretion_records", *_base_columns(), sa.Column("type", sa.String(length=30), nullable=False), sa.Column("consistency", sa.String(length=30), nullable=True))
    op.create_table("behavior_records", *_base_columns(), sa.Column("behavior_type", sa.String(length=100), nullable=False), sa.Column("duration_minutes", sa.Integer(), nullable=True), sa.Column("mood", sa.String(length=50), nullable=True))
    for table in ("feeding_records", "excretion_records", "behavior_records"):
        op.create_index(f"ix_{table}_id", table, ["id"])
        op.create_index(f"ix_{table}_pet_id", table, ["pet_id"])
        op.create_index(f"ix_{table}_recorded_at", table, ["recorded_at"])


def downgrade() -> None:
    for table in ("behavior_records", "excretion_records", "feeding_records"):
        op.drop_index(f"ix_{table}_recorded_at", table_name=table)
        op.drop_index(f"ix_{table}_pet_id", table_name=table)
        op.drop_index(f"ix_{table}_id", table_name=table)
        op.drop_table(table)
