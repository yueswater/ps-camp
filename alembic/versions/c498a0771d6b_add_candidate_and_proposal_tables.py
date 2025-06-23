"""add candidate and proposal tables

Revision ID: c498a0771d6b
Revises: d5be4de87a74
Create Date: 2025-06-24 04:49:37.499697
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c498a0771d6b"
down_revision: Union[str, None] = "d5be4de87a74"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "candidates",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("party_id", postgresql.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.ForeignKeyConstraint(["party_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "proposals",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("group_id", postgresql.UUID(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.ForeignKeyConstraint(["group_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.alter_column(
        "referendum_votes",
        "timestamp",
        existing_type=postgresql.TIMESTAMP(),
        nullable=False,
        existing_server_default=sa.text("now()"),
    )

    op.create_foreign_key(None, "referendum_votes", "users", ["user_id"], ["id"])

    op.alter_column(
        "votes",
        "timestamp",
        existing_type=postgresql.TIMESTAMP(),
        nullable=False,
        existing_server_default=sa.text("now()"),
    )

    op.create_foreign_key(None, "votes", "users", ["user_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint(None, "votes", type_="foreignkey")

    op.alter_column(
        "votes",
        "timestamp",
        existing_type=postgresql.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("now()"),
    )

    op.drop_constraint(None, "referendum_votes", type_="foreignkey")

    op.alter_column(
        "referendum_votes",
        "timestamp",
        existing_type=postgresql.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("now()"),
    )

    op.drop_table("proposals")
    op.drop_table("candidates")
