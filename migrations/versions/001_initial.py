"""initial

Revision ID: 001
Revises: 
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from app.models.document import DocumentType, DocumentStatus

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create folders table
    op.create_table(
        'folders',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('parent_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['folders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create unique constraint and indexes for folders
    op.create_unique_constraint('uix_folder_path', 'folders', ['path'])
    op.create_index('ix_folder_name', 'folders', ['name'])
    op.create_index('ix_folder_parent_id', 'folders', ['parent_id'])

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_type', sa.Enum(DocumentType), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False),
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('sentiment_polarity', sa.Float(), nullable=True),
        sa.Column('sentiment_subjectivity', sa.Float(), nullable=True),
        sa.Column('sentiment_label', sa.String(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum(DocumentStatus), nullable=False),
        sa.Column('folder_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create unique constraint and indexes for documents
    op.create_unique_constraint('uix_document_path_folder', 'documents', ['path', 'folder_id'])
    op.create_index('ix_document_filename', 'documents', ['filename'])
    op.create_index('ix_document_file_type', 'documents', ['file_type'])
    op.create_index('ix_document_status', 'documents', ['status'])
    op.create_index('ix_document_modified_at', 'documents', ['modified_at'])

    # Create classifications table
    op.create_table(
        'classifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create unique constraint and indexes for classifications
    op.create_unique_constraint('uix_classification_document', 'classifications', ['document_id'])
    op.create_index('ix_classification_category', 'classifications', ['category'])

def downgrade() -> None:
    # Drop indexes and constraints first
    op.drop_index('ix_classification_category')
    op.drop_constraint('uix_classification_document', 'classifications')
    
    op.drop_index('ix_document_modified_at')
    op.drop_index('ix_document_status')
    op.drop_index('ix_document_file_type')
    op.drop_index('ix_document_filename')
    op.drop_constraint('uix_document_path_folder', 'documents')
    
    op.drop_index('ix_folder_parent_id')
    op.drop_index('ix_folder_name')
    op.drop_constraint('uix_folder_path', 'folders')

    # Drop tables
    op.drop_table('classifications')
    op.drop_table('documents')
    op.drop_table('folders') 