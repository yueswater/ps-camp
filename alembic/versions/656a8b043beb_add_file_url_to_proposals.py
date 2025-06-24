"""add file_url to proposals

Revision ID: 656a8b043beb
Revises: 8566d65b2c30
Create Date: 2025-06-24 17:19:31.243491

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "656a8b043beb"
down_revision: Union[str, None] = "8566d65b2c30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("proposals", sa.Column("file_url", sa.String(), nullable=True))


def downgrade():
    op.drop_column("proposals", "file_url")
