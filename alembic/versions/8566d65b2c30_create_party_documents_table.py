"""create party_documents table

Revision ID: 8566d65b2c30
Revises: 0349f30efffc
Create Date: 2025-06-24 17:01:54.038885

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8566d65b2c30"
down_revision: Union[str, None] = "0349f30efffc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "party_documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "party_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("cabinet_url", sa.String(), nullable=True),
        sa.Column("alliance_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("party_documents")
