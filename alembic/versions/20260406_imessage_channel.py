"""Generalize message model for iMessage: add channel, rename wa_message_id.

Revision ID: 20260406_imsg
Revises:
Create Date: 2026-04-06
"""

from alembic import op
import sqlalchemy as sa

revision = "20260406_imsg"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add channel column with default for existing rows
    op.add_column(
        "messages",
        sa.Column("channel", sa.String(16), server_default="whatsapp", nullable=False),
    )
    # Rename wa_message_id → external_message_id
    op.alter_column(
        "messages",
        "wa_message_id",
        new_column_name="external_message_id",
    )


def downgrade() -> None:
    op.alter_column(
        "messages",
        "external_message_id",
        new_column_name="wa_message_id",
    )
    op.drop_column("messages", "channel")
