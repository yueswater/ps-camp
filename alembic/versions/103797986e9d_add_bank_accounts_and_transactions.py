"""add bank accounts and transactions

Revision ID: 103797986e9d
Revises: 0284a911ee15
Create Date: 2025-06-23 00:22:23.354182

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '103797986e9d'
down_revision: Union[str, None] = '0284a911ee15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'bank_accounts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('owner_id', sa.String(), nullable=False),
        sa.Column('owner_type', sa.Enum('user', 'party', 'group', 'admin', name='ownertype'), nullable=False),
        sa.Column('account_number', sa.String(), nullable=False, unique=True),
        sa.Column('balance', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'transactions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('from_account_id', sa.String(), sa.ForeignKey('bank_accounts.id')), 
        sa.Column('to_account_id', sa.String(), sa.ForeignKey('bank_accounts.id')),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('transaction_type', sa.Enum('transfer', 'post_penalty', 'initial_grant', 'system_adjustment', name='transactiontype'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('transactions')
    op.drop_table('bank_accounts')
    op.execute("DROP TYPE IF EXISTS transactiontype")
    op.execute("DROP TYPE IF EXISTS ownertype")