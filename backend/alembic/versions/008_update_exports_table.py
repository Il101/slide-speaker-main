"""Update exports table with missing columns

Revision ID: 008_update_exports_table
Revises: 007_add_subscriptions
Create Date: 2025-11-02 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_update_exports_table'
down_revision = '007_add_subscriptions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing columns to exports table"""
    
    # Add user_id column
    op.add_column('exports', sa.Column('user_id', sa.String(36), nullable=True))
    op.create_index('ix_exports_user_id', 'exports', ['user_id'])
    
    # Add quality column
    op.add_column('exports', sa.Column('quality', sa.String(20), server_default='high'))
    
    # Add file_size column
    op.add_column('exports', sa.Column('file_size', sa.Integer(), nullable=True))
    
    # Add duration column
    op.add_column('exports', sa.Column('duration', sa.Float(), nullable=True))
    
    # Add progress column
    op.add_column('exports', sa.Column('progress', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Add error_message column
    op.add_column('exports', sa.Column('error_message', sa.Text(), nullable=True))
    
    # Add completed_at column
    op.add_column('exports', sa.Column('completed_at', sa.DateTime(), nullable=True))
    
    # Update existing records to set user_id from lessons table
    op.execute("""
        UPDATE exports e
        SET user_id = l.user_id
        FROM lessons l
        WHERE e.lesson_id = l.id
    """)


def downgrade() -> None:
    """Remove added columns from exports table"""
    
    op.drop_column('exports', 'completed_at')
    op.drop_column('exports', 'error_message')
    op.drop_column('exports', 'progress')
    op.drop_column('exports', 'duration')
    op.drop_column('exports', 'file_size')
    op.drop_column('exports', 'quality')
    op.drop_index('ix_exports_user_id', 'exports')
    op.drop_column('exports', 'user_id')
