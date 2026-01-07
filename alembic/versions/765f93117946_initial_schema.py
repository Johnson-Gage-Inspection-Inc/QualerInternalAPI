"""Initial schema

Revision ID: 765f93117946
Revises:
Create Date: 2026-01-07 14:50:44.605137

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "765f93117946"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create datadump table with JSONB columns."""
    op.create_table(
        "datadump",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("service", sa.String(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("request_header", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("response_header", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("parsed", sa.Boolean(), server_default=sa.text("false"), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url", "service", "method", name="uq_api_response"),
    )


def downgrade() -> None:
    """Drop datadump table."""
    op.drop_table("datadump")
