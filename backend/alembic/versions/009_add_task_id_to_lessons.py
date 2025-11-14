"""add task_id to lessons

Revision ID: 009_add_task_id_to_lessons
Revises: 008_update_exports_table
Create Date: 2025-11-12 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009_add_task_id_to_lessons'
down_revision = '008_update_exports_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add task_id column to lessons table if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'lessons' AND column_name = 'task_id'
            ) THEN
                ALTER TABLE lessons ADD COLUMN task_id VARCHAR(255);
                CREATE INDEX idx_lessons_task_id ON lessons(task_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Remove task_id column and index
    op.drop_index('idx_lessons_task_id', table_name='lessons')
    op.drop_column('lessons', 'task_id')
