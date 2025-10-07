"""Add username to users table

Revision ID: 002_add_username
Revises: 001_initial
Create Date: 2024-12-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_username'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add username column to users table"""
    # Add username column
    op.add_column('users', sa.Column('username', sa.String(length=100), nullable=True))
    
    # Create unique constraint
    op.create_unique_constraint('uq_users_username', 'users', ['username'])
    
    # Create index for faster lookups
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade() -> None:
    """Remove username column from users table"""
    # Drop index
    op.drop_index(op.f('ix_users_username'), table_name='users')
    
    # Drop unique constraint
    op.drop_constraint('uq_users_username', 'users', type_='unique')
    
    # Drop column
    op.drop_column('users', 'username')
