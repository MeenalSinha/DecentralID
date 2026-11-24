"""phase10_intelligence_document_extraction

Revision ID: e12fa4b68c01
Revises: d91ab2847c19
Create Date: 2026-11-24 14:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e12fa4b68c01'
down_revision: Union[str, None] = 'd91ab2847c19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'document_uploads',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('uploaded_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('storage_path', sa.String(length=512), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_document_uploads_organization_id'), 'document_uploads', ['organization_id'], unique=False)
    op.create_index(op.f('ix_document_uploads_file_hash'), 'document_uploads', ['file_hash'], unique=False)

    op.create_table(
        'extracted_credential_data',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('document_id', sa.String(length=36), sa.ForeignKey('document_uploads.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('schema_type', sa.String(length=100), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('extracted_fields_json', sa.Text(), nullable=False),
        sa.Column('anomaly_findings_json', sa.Text(), nullable=False),
        sa.Column('overall_confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('review_status', sa.String(length=50), nullable=False, server_default='PENDING_REVIEW'),
        sa.Column('reviewed_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('credential_id', sa.String(length=36), sa.ForeignKey('credentials.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_extracted_credential_data_document_id'), 'extracted_credential_data', ['document_id'], unique=True)

def downgrade() -> None:
    op.drop_table('extracted_credential_data')
    op.drop_table('document_uploads')
