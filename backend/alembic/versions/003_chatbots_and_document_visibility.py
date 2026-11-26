"""Add chatbot configuration and public document visibility."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("is_publicly_searchable", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "chatbots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("public_id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False, server_default="Support Assistant"),
        sa.Column("description", sa.String(length=300), nullable=False, server_default="Ask questions about our services."),
        sa.Column("welcome_message", sa.Text(), nullable=False, server_default="Hello! How can I help you today?"),
        sa.Column("placeholder", sa.String(length=150), nullable=False, server_default="Type your question..."),
        sa.Column("primary_color", sa.String(length=7), nullable=False, server_default="#2563EB"),
        sa.Column("position", sa.String(length=20), nullable=False, server_default="bottom-right"),
        sa.Column("launcher_label", sa.String(length=50), nullable=False, server_default="Chat with us"),
        sa.Column("suggested_questions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("allowed_domains", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("show_sources", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", name="uq_chatbots_company"),
        sa.UniqueConstraint("public_id", name="uq_chatbots_public_id"),
        sa.CheckConstraint("position IN ('bottom-right','bottom-left')", name="ck_chatbots_position"),
        sa.CheckConstraint("char_length(primary_color) = 7", name="ck_chatbots_primary_color"),
    )
    op.create_index("ix_chatbots_company_id", "chatbots", ["company_id"])
    op.create_index("ix_chatbots_public_id", "chatbots", ["public_id"])


def downgrade() -> None:
    op.drop_index("ix_chatbots_public_id", table_name="chatbots")
    op.drop_index("ix_chatbots_company_id", table_name="chatbots")
    op.drop_table("chatbots")
    op.drop_column("documents", "is_publicly_searchable")
