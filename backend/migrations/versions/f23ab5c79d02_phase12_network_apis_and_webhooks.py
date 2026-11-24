"""phase12_network_apis_and_webhooks

Revision ID: f23ab5c79d02
Revises: e12fa4b68c01
Create Date: 2026-11-24 14:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f23ab5c79d02'
down_revision: Union[str, None] = 'e12fa4b68c01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('key_prefix', sa.String(length=16), nullable=False),
        sa.Column('hashed_key', sa.String(length=64), nullable=False, unique=True),
        sa.Column('scopes', sa.JSON(), nullable=False),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_api_keys_org_id', 'api_keys', ['organization_id'])
    op.create_index('ix_api_keys_hashed_key', 'api_keys', ['hashed_key'])

    op.create_table(
        'webhook_subscriptions',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_url', sa.String(length=512), nullable=False),
        sa.Column('secret_key', sa.String(length=128), nullable=False),
        sa.Column('event_types', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_webhook_subs_org_id', 'webhook_subscriptions', ['organization_id'])

    op.create_table(
        'webhook_deliveries',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('subscription_id', sa.String(length=36), sa.ForeignKey('webhook_subscriptions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_webhook_deliveries_sub_id', 'webhook_deliveries', ['subscription_id'])

    op.create_table(
        'storage_records',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('cid', sa.String(length=128), nullable=False, unique=True),
        sa.Column('content_type', sa.String(length=64), nullable=False, server_default='application/json+encrypted'),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('encryption_algorithm', sa.String(length=32), nullable=False, server_default='AES-256-GCM'),
        sa.Column('provider', sa.String(length=32), nullable=False, server_default='local'),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_storage_records_cid', 'storage_records', ['cid'])


def downgrade() -> None:
    op.drop_table('storage_records')
    op.drop_table('webhook_deliveries')
    op.drop_table('webhook_subscriptions')
    op.drop_table('api_keys')
