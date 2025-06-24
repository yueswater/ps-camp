from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0349f30efffc"
down_revision: Union[str, None] = "4d127314cf12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "candidates", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_candidates_user_id_users", "candidates", "users", ["user_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_candidates_user_id_users", "candidates", type_="foreignkey")
    op.drop_column("candidates", "user_id")
