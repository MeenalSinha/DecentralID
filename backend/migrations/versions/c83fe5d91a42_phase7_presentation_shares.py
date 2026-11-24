"""phase7_presentation_shares

Revision ID: c83fe5d91a42
Revises: b42ce3f7b623
Create Date: 2026-11-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c83fe5d91a42'
down_revision: Union[str, None] = 'b42ce3f7b623'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'presentation_shares',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('token', sa.String(length=64), unique=True, nullable=False),
        sa.Column('holder_address', sa.String(length=42), nullable=False),
        sa.Column('credential_id', sa.String(length=66), nullable=False),
        sa.Column('disclosed_claims', sa.JSON(), nullable=False),
        sa.Column('presentation_document', sa.JSON(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('access_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_access', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_presentation_shares_token', 'presentation_shares', ['token'])
    op.create_index('ix_presentation_shares_holder_address', 'presentation_shares', ['holder_address'])
    op.create_index('ix_presentation_shares_credential_id', 'presentation_shares', ['credential_id'])


def downgrade() -> None:
    op.drop_index('ix_presentation_shares_credential_id', table_name='presentation_shares')
    op.drop_index('ix_presentation_shares_holder_address', table_name='presentation_shares')
    op.drop_index('ix_presentation_shares_token', table_name='presentation_shares')
    op.drop_table('presentation_shares')
