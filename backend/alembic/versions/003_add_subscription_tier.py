"""add subscription_tier to users

Revision ID: 003_add_subscription_tier
Revises: 002_add_analytics_tables
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_subscription_tier'
down_revision = '002_add_analytics_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Add subscription_tier column to users table
    op.add_column('users', sa.Column('subscription_tier', sa.String(50), nullable=False, server_default='free'))


def downgrade():
    # Remove subscription_tier column
    op.drop_column('users', 'subscription_tier')
