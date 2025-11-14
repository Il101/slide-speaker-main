"""Add username and email_verified fields to users

Revision ID: 006_add_user_fields
Revises: 005_add_playlists
Create Date: 2025-01-15 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_add_user_fields'
down_revision = '005_add_playlists'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add username column (nullable, unique)
    op.add_column('users', sa.Column('username', sa.String(100), nullable=True))
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Add email_verified column (default False)
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add email_verified_at column (nullable)
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Drop added columns
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_column('users', 'username')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'email_verified_at')
