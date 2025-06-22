"""add replies column to posts

Revision ID: 725e3e549d22
Revises: 2d77690128ce
Create Date: 2025-06-22 14:56:22.955983

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "725e3e549d22"
down_revision: Union[str, None] = "2d77690128ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("replies", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("posts", "replies")
