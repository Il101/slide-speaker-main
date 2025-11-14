"""Add quiz tables

Revision ID: 004_add_quiz_tables
Revises: 003_add_subscription_tier
Create Date: 2025-01-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_quiz_tables'
down_revision = '003_add_subscription_tier'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create quizzes table
    op.create_table(
        'quizzes',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('lesson_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_quizzes_lesson_id', 'quizzes', ['lesson_id'])
    op.create_index('ix_quizzes_user_id', 'quizzes', ['user_id'])

    # Create quiz_questions table
    op.create_table(
        'quiz_questions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('quiz_id', sa.String(36), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(50), nullable=False),
        sa.Column('difficulty', sa.String(20), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('points', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.CheckConstraint("question_type IN ('multiple_choice', 'multiple_select', 'true_false', 'short_answer')", name='ck_question_type'),
        sa.CheckConstraint("difficulty IN ('easy', 'medium', 'hard') OR difficulty IS NULL", name='ck_difficulty'),
    )
    op.create_index('ix_quiz_questions_quiz_id', 'quiz_questions', ['quiz_id', 'order_index'])

    # Create quiz_answers table
    op.create_table(
        'quiz_answers',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('question_id', sa.String(36), nullable=False),
        sa.Column('answer_text', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['question_id'], ['quiz_questions.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_quiz_answers_question_id', 'quiz_answers', ['question_id', 'order_index'])

    # Create quiz_attempts table (for analytics)
    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('quiz_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('max_score', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_quiz_attempts_quiz_id', 'quiz_attempts', ['quiz_id'])
    op.create_index('ix_quiz_attempts_user_id', 'quiz_attempts', ['user_id'])


def downgrade() -> None:
    op.drop_table('quiz_attempts')
    op.drop_table('quiz_answers')
    op.drop_table('quiz_questions')
    op.drop_table('quizzes')
