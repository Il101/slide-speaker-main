"""Add analytics tables

Revision ID: 002_add_analytics_tables
Revises: 001_initial
Create Date: 2025-01-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_analytics_tables'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create analytics_events table
    op.create_table(
        'analytics_events',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('event_name', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('properties', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('device', sa.String(50), nullable=True),
        sa.Column('browser', sa.String(100), nullable=True),
        sa.Column('os', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analytics_events_event_name', 'analytics_events', ['event_name'])
    op.create_index('ix_analytics_events_user_id', 'analytics_events', ['user_id'])
    op.create_index('ix_analytics_events_session_id', 'analytics_events', ['session_id'])
    op.create_index('ix_analytics_events_timestamp', 'analytics_events', ['timestamp'])

    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('last_activity', sa.DateTime(), nullable=False),
        sa.Column('page_views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('landing_page', sa.String(500), nullable=True),
        sa.Column('referrer', sa.String(500), nullable=True),
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index('ix_user_sessions_session_id', 'user_sessions', ['session_id'])
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])

    # Create daily_metrics table
    op.create_table(
        'daily_metrics',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('total_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('new_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('active_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lectures_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('presentations_uploaded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('downloads_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('new_subscriptions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cancelled_subscriptions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('mrr', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_costs', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('ocr_costs', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('ai_costs', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('tts_costs', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('signup_to_lecture_rate', sa.Float(), nullable=True),
        sa.Column('free_to_paid_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date')
    )
    op.create_index('ix_daily_metrics_date', 'daily_metrics', ['date'])

    # Create cost_logs table
    op.create_table(
        'cost_logs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('operation', sa.String(50), nullable=False),
        sa.Column('cost', sa.Float(), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('lesson_id', sa.String(36), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cost_logs_operation', 'cost_logs', ['operation'])
    op.create_index('ix_cost_logs_user_id', 'cost_logs', ['user_id'])
    op.create_index('ix_cost_logs_timestamp', 'cost_logs', ['timestamp'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_cost_logs_timestamp', table_name='cost_logs')
    op.drop_index('ix_cost_logs_user_id', table_name='cost_logs')
    op.drop_index('ix_cost_logs_operation', table_name='cost_logs')
    op.drop_index('ix_daily_metrics_date', table_name='daily_metrics')
    op.drop_index('ix_user_sessions_user_id', table_name='user_sessions')
    op.drop_index('ix_user_sessions_session_id', table_name='user_sessions')
    op.drop_index('ix_analytics_events_timestamp', table_name='analytics_events')
    op.drop_index('ix_analytics_events_session_id', table_name='analytics_events')
    op.drop_index('ix_analytics_events_user_id', table_name='analytics_events')
    op.drop_index('ix_analytics_events_event_name', table_name='analytics_events')
    
    # Drop tables
    op.drop_table('cost_logs')
    op.drop_table('daily_metrics')
    op.drop_table('user_sessions')
    op.drop_table('analytics_events')
