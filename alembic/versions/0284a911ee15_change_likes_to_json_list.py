"""change likes to JSON list

Revision ID: 0284a911ee15
Revises: 65048261d097
Create Date: 2025-06-22 23:32:03.599128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0284a911ee15'
down_revision: Union[str, None] = '65048261d097'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("posts", "likes", server_default=None)
    op.execute("ALTER TABLE posts ALTER COLUMN likes TYPE JSON USING '[]'::json")
    op.alter_column("posts", "likes", server_default=sa.text("'[]'::json"))


def downgrade() -> None:
    op.alter_column("posts", "likes", server_default=None)
    op.execute("ALTER TABLE posts ALTER COLUMN likes TYPE INTEGER USING 0")
    op.alter_column("posts", "likes", server_default=sa.text("0"))
