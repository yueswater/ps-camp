"""fix referendum_votes type to UUID

Revision ID: a043d1e085ae
Revises: c498a0771d6b
Create Date: 2025-06-24 05:08:26.348141

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a043d1e085ae"
down_revision: Union[str, None] = "c498a0771d6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # fix type: referendum_votes.id/user_id/referendum_id -> UUID with explicit cast
    op.execute("ALTER TABLE referendum_votes ALTER COLUMN id TYPE UUID USING id::uuid")
    op.execute(
        "ALTER TABLE referendum_votes ALTER COLUMN user_id TYPE UUID USING user_id::uuid"
    )
    op.execute(
        "ALTER TABLE referendum_votes ALTER COLUMN referendum_id TYPE UUID USING referendum_id::uuid"
    )

    # allow timestamp to be nullable
    op.alter_column(
        "referendum_votes",
        "timestamp",
        existing_type=sa.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("now()"),
    )

    # add foreign key
    op.create_foreign_key(
        "fk_referendum_votes_user_id_users",
        "referendum_votes",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_referendum_votes_user_id_users", "referendum_votes", type_="foreignkey"
    )

    op.alter_column(
        "referendum_votes",
        "timestamp",
        existing_type=sa.TIMESTAMP(),
        nullable=False,
        existing_server_default=sa.text("now()"),
    )

    op.alter_column(
        "referendum_votes",
        "referendum_id",
        existing_type=sa.UUID(),
        type_=sa.VARCHAR(),
        existing_nullable=False,
    )
    op.alter_column(
        "referendum_votes",
        "user_id",
        existing_type=sa.UUID(),
        type_=sa.VARCHAR(),
        existing_nullable=False,
    )
    op.alter_column(
        "referendum_votes",
        "id",
        existing_type=sa.UUID(),
        type_=sa.VARCHAR(),
        existing_nullable=False,
    )
