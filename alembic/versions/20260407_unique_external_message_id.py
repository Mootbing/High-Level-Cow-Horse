"""Add unique partial index on external_message_id for message deduplication.

Revision ID: 20260407_dedup
Revises: 20260406_imsg
Create Date: 2026-04-07
"""

from alembic import op
from sqlalchemy import text

revision = "20260407_dedup"
down_revision = "20260406_imsg"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_messages_external_message_id",
        "messages",
        ["external_message_id"],
        unique=True,
        postgresql_where=text("external_message_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_messages_external_message_id", table_name="messages")
