"""Add playlists tables

Revision ID: 005_add_playlists
Revises: 004_add_quiz_tables
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_add_playlists'
down_revision = '004_add_quiz_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create playlists table
    op.create_table('playlists',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('share_token', sa.String(100), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_playlists_user_id'), 'playlists', ['user_id'])
    op.create_index(op.f('ix_playlists_share_token'), 'playlists', ['share_token'], unique=True)
    
    # Create playlist_items table (junction table)
    op.create_table('playlist_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('playlist_id', sa.String(), nullable=False),
        sa.Column('lesson_id', sa.String(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['playlist_id'], ['playlists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('playlist_id', 'lesson_id', name='uq_playlist_lesson')
    )
    op.create_index(op.f('ix_playlist_items_playlist_id'), 'playlist_items', ['playlist_id', 'order_index'])
    
    # Create playlist_views table (analytics)
    op.create_table('playlist_views',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('playlist_id', sa.String(), nullable=False),
        sa.Column('viewer_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('videos_watched', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_watch_time', sa.Integer(), nullable=True),
        sa.Column('viewed_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['playlist_id'], ['playlists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['viewer_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_playlist_views_playlist_id'), 'playlist_views', ['playlist_id', 'viewed_at'])


def downgrade() -> None:
    op.drop_index(op.f('ix_playlist_views_playlist_id'), table_name='playlist_views')
    op.drop_table('playlist_views')
    
    op.drop_index(op.f('ix_playlist_items_playlist_id'), table_name='playlist_items')
    op.drop_table('playlist_items')
    
    op.drop_index(op.f('ix_playlists_share_token'), table_name='playlists')
    op.drop_index(op.f('ix_playlists_user_id'), table_name='playlists')
    op.drop_table('playlists')
