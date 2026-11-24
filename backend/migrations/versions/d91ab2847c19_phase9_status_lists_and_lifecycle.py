"""phase9_status_lists_and_lifecycle

Revision ID: d91ab2847c19
Revises: c83fe5d91a42
Create Date: 2026-11-24 10:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd91ab2847c19'
down_revision: Union[str, None] = 'c83fe5d91a42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create status_lists table
    op.create_table(
        'status_lists',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('list_number', sa.Integer(), unique=True, nullable=False),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('purpose', sa.String(length=50), nullable=False, server_default='revocation'),
        sa.Column('bit_length', sa.Integer(), nullable=False, server_default='16384'),
        sa.Column('current_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('raw_bits', sa.LargeBinary(), nullable=False),
        sa.Column('encoded_list', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_status_lists_list_number', 'status_lists', ['list_number'])
    op.create_index('ix_status_lists_organization_id', 'status_lists', ['organization_id'])

    # 2. Add columns to credentials table using batch_alter_table for SQLite compatibility
    with op.batch_alter_table('credentials') as batch_op:
        batch_op.add_column(sa.Column('status_list_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('status_list_index', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('revocation_reason', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('supersedes_id', sa.String(length=66), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('credentials') as batch_op:
        batch_op.drop_column('supersedes_id')
        batch_op.drop_column('revoked_at')
        batch_op.drop_column('revocation_reason')
        batch_op.drop_column('status_list_index')
        batch_op.drop_column('status_list_id')

    op.drop_index('ix_status_lists_organization_id', table_name='status_lists')
    op.drop_index('ix_status_lists_list_number', table_name='status_lists')
    op.drop_table('status_lists')
