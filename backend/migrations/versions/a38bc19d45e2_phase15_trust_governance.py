"""phase15_trust_governance

Revision ID: a38bc19d45e2
Revises: f23ab5c79d02
Create Date: 2026-11-24 18:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a38bc19d45e2'
down_revision: Union[str, None] = 'f23ab5c79d02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'institution_accreditations',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='APPLIED'),
        sa.Column('authorized_schemas', sa.JSON(), nullable=False),
        sa.Column('evidence_urls', sa.JSON(), nullable=False),
        sa.Column('reviewer_id', sa.String(length=36), nullable=True),
        sa.Column('senior_approver_id', sa.String(length=36), nullable=True),
        sa.Column('rejection_reason', sa.String(length=256), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('risk_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_inst_accreditations_org_id', 'institution_accreditations', ['organization_id'])

    op.create_table(
        'governance_audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('accreditation_id', sa.String(length=36), sa.ForeignKey('institution_accreditations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('actor_id', sa.String(length=36), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_gov_audit_logs_acc_id', 'governance_audit_logs', ['accreditation_id'])


def downgrade() -> None:
    op.drop_table('governance_audit_logs')
    op.drop_table('institution_accreditations')
