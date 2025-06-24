"""add photo_url to candidate

Revision ID: 4d127314cf12
Revises: a043d1e085ae
Create Date: 2025-06-24 12:23:54.757651

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4d127314cf12"
down_revision: Union[str, None] = "a043d1e085ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("photo_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("candidates", "photo_url")
