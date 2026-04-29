"""add first_name and last_name to users

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default="" allows the migration to run on tables with existing rows.
    # The Pydantic schema enforces min_length=1 at the API boundary.
    op.add_column(
        "users",
        sa.Column("first_name", sa.String(50), nullable=False, server_default=sa.text("''")),
    )
    op.add_column(
        "users",
        sa.Column("last_name", sa.String(50), nullable=False, server_default=sa.text("''")),
    )


def downgrade() -> None:
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
