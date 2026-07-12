"""add_visualization_column_to_reports

Revision ID: 7a0f7f1f9c21
Revises: 6faf9c3a868b
Create Date: 2026-07-03 12:26:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7a0f7f1f9c21"
down_revision: Union[str, None] = "6faf9c3a868b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column(
            "visualization",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.alter_column("reports", "visualization", server_default=None)


def downgrade() -> None:
    op.drop_column("reports", "visualization")
