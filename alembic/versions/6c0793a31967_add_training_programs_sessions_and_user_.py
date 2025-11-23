"""add training programs sessions and user deletion grace period

Revision ID: 6c0793a31967
Revises: 59779afa0396
Create Date: 2025-11-23 13:09:48.285757+00:00

This migration adds:
1. deletion_requested_at column to users table (for 30-day grace period)
2. training_programs table with split types and structure configurations
3. workout_sessions table with exercises stored as JSONB
4. Comprehensive indexes for performance
5. Seed data for global exercises and program templates

"""
from typing import Sequence, Union
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6c0793a31967'
down_revision: Union[str, None] = '59779afa0396'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema.
    
    Steps:
    1. Add deletion_requested_at to users table
    2. Create training_programs table with indexes
    3. Create workout_sessions table with foreign key
    4. Add seed data for global exercises
    5. Add seed data for program templates
    """
    
    # ========================================================================
    # STEP 1: Add deletion_requested_at column to users table
    # ========================================================================
    print("Adding deletion_requested_at column to users table...")
    
    op.add_column(
        'users',
        sa.Column(
            'deletion_requested_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Timestamp when account deletion was requested (for 30-day grace period)'
        )
    )
    
    # Add partial index for efficient cleanup queries
    op.create_index(
        'ix_users_deletion_requested',
        'users',
        ['deletion_requested_at'],
        unique=False,
        postgresql_where=text('deletion_requested_at IS NOT NULL')
    )
    
    # ========================================================================
    # STEP 2: Create training_programs table
    # ========================================================================
    print("Creating training_programs table...")
    
    op.create_table(
        'training_programs',
        # Primary Key and Timestamps (from BaseModel)
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        
        # Basic Information
        sa.Column(
            'name',
            sa.String(200),
            nullable=False,
            comment="Program name (e.g., 'Upper/Lower 4-Day Split')"
        ),
        sa.Column(
            'description',
            sa.Text(),
            nullable=False,
            server_default='',
            comment='Program description and notes'
        ),
        
        # Program Configuration
        sa.Column(
            'split_type',
            sa.String(50),
            nullable=False,
            comment='Training split type enum (UPPER_LOWER, PUSH_PULL_LEGS, etc.)'
        ),
        sa.Column(
            'structure_type',
            sa.String(20),
            nullable=False,
            comment='Structure type enum (WEEKLY, CYCLIC)'
        ),
        sa.Column(
            'structure_config',
            postgresql.JSONB,
            nullable=False,
            comment='Structure configuration (WeeklyStructure or CyclicStructure as JSON)'
        ),
        
        # Ownership & Template Status
        sa.Column(
            'is_template',
            sa.Boolean(),
            nullable=False,
            server_default='false',
            comment='True if admin template, False if user program'
        ),
        sa.Column(
            'created_by_user_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='User who created program (None for templates)'
        ),
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Organization owning program (None for templates)'
        ),
        
        # Program Duration
        sa.Column(
            'duration_weeks',
            sa.Integer(),
            nullable=True,
            comment='Recommended program duration in weeks'
        ),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        
        # Table comment
        comment='Training programs with split types, structures, and sessions'
    )
    
    # Create indexes for training_programs
    print("Creating indexes for training_programs...")
    
    # Basic indexes
    op.create_index('ix_training_programs_id', 'training_programs', ['id'])
    op.create_index('ix_training_programs_name', 'training_programs', ['name'])
    op.create_index('ix_training_programs_split_type', 'training_programs', ['split_type'])
    op.create_index('ix_training_programs_structure_type', 'training_programs', ['structure_type'])
    op.create_index('ix_training_programs_is_template', 'training_programs', ['is_template'])
    op.create_index('ix_training_programs_created_by_user_id', 'training_programs', ['created_by_user_id'])
    op.create_index('ix_training_programs_organization_id', 'training_programs', ['organization_id'])
    
    # Composite index for templates
    op.create_index(
        'ix_training_programs_templates',
        'training_programs',
        ['is_template'],
        postgresql_where=text('is_template = true')
    )
    
    # Composite index for user programs by organization
    op.create_index(
        'ix_training_programs_org',
        'training_programs',
        ['organization_id', 'is_template'],
        postgresql_where=text('is_template = false')
    )
    
    # Composite index for user's programs
    op.create_index(
        'ix_training_programs_user',
        'training_programs',
        ['created_by_user_id', 'organization_id']
    )
    
    # GIN index for JSONB structure_config
    op.create_index(
        'ix_training_programs_structure_config',
        'training_programs',
        ['structure_config'],
        postgresql_using='gin'
    )
    
    # Full-text search index on name and description
    op.create_index(
        'ix_training_programs_search',
        'training_programs',
        [text("to_tsvector('english', name || ' ' || COALESCE(description, ''))")],
        postgresql_using='gin'
    )
    
    # ========================================================================
    # STEP 3: Create workout_sessions table
    # ========================================================================
    print("Creating workout_sessions table...")
    
    op.create_table(
        'workout_sessions',
        # Primary Key and Timestamps (from BaseModel)
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        
        # Foreign Key to training_programs
        sa.Column(
            'program_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('training_programs.id', ondelete='CASCADE'),
            nullable=False,
            comment='Reference to parent training program'
        ),
        
        # Basic Information
        sa.Column(
            'name',
            sa.String(200),
            nullable=False,
            comment="Session name (e.g., 'Upper Body A', 'Push Day 1')"
        ),
        sa.Column(
            'day_number',
            sa.Integer(),
            nullable=False,
            comment='Day number in program sequence (1-indexed)'
        ),
        sa.Column(
            'order_in_program',
            sa.Integer(),
            nullable=False,
            comment='Order of this session in the program'
        ),
        
        # Exercises (JSONB array)
        sa.Column(
            'exercises',
            postgresql.JSONB,
            nullable=False,
            server_default='[]',
            comment='Array of exercises with sets and order'
        ),
        
        # Computed field - stored for query performance
        sa.Column(
            'total_sets',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Total number of sets across all exercises (computed)'
        ),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['program_id'],
            ['training_programs.id'],
            ondelete='CASCADE'
        ),
        
        # Table comment
        comment='Workout sessions within training programs'
    )
    
    # Create indexes for workout_sessions
    print("Creating indexes for workout_sessions...")
    
    # Basic indexes
    op.create_index('ix_workout_sessions_id', 'workout_sessions', ['id'])
    op.create_index('ix_workout_sessions_program_id', 'workout_sessions', ['program_id'])
    op.create_index('ix_workout_sessions_name', 'workout_sessions', ['name'])
    op.create_index('ix_workout_sessions_day_number', 'workout_sessions', ['day_number'])
    op.create_index('ix_workout_sessions_order_in_program', 'workout_sessions', ['order_in_program'])
    op.create_index('ix_workout_sessions_total_sets', 'workout_sessions', ['total_sets'])
    
    # Composite indexes for efficient queries
    op.create_index(
        'ix_workout_sessions_program_order',
        'workout_sessions',
        ['program_id', 'order_in_program']
    )
    
    op.create_index(
        'ix_workout_sessions_program_day',
        'workout_sessions',
        ['program_id', 'day_number']
    )
    
    # GIN index for JSONB exercises
    op.create_index(
        'ix_workout_sessions_exercises',
        'workout_sessions',
        ['exercises'],
        postgresql_using='gin'
    )
    
    # ========================================================================
    # STEP 4: Seed data moved to separate script
    # ========================================================================
    print("\n" + "="*70)
    print("Migration complete! Run seed script to populate data:")
    print("python scripts/seed_data.py")
    print("="*70)


def downgrade() -> None:
    """Downgrade database schema.
    
    Removes all changes from upgrade() in reverse order.
    """
    
    print("Rolling back migration...")
    
    # Drop workout_sessions table (will cascade due to FK)
    print("Dropping workout_sessions table...")
    op.drop_index('ix_workout_sessions_exercises', table_name='workout_sessions')
    op.drop_index('ix_workout_sessions_program_day', table_name='workout_sessions')
    op.drop_index('ix_workout_sessions_program_order', table_name='workout_sessions')
    op.drop_index('ix_workout_sessions_total_sets', table_name='workout_sessions')
    op.drop_index('ix_workout_sessions_order_in_program', table_name='workout_sessions')
    op.drop_index('ix_workout_sessions_day_number', table_name='workout_sessions')
    op.drop_index('ix_workout_sessions_name', table_name='workout_sessions')
    op.drop_index('ix_workout_sessions_program_id', table_name='workout_sessions')
    op.drop_index('ix_workout_sessions_id', table_name='workout_sessions')
    op.drop_table('workout_sessions')
    
    # Drop training_programs table
    print("Dropping training_programs table...")
    op.drop_index('ix_training_programs_search', table_name='training_programs')
    op.drop_index('ix_training_programs_structure_config', table_name='training_programs')
    op.drop_index('ix_training_programs_user', table_name='training_programs')
    op.drop_index('ix_training_programs_org', table_name='training_programs')
    op.drop_index('ix_training_programs_templates', table_name='training_programs')
    op.drop_index('ix_training_programs_organization_id', table_name='training_programs')
    op.drop_index('ix_training_programs_created_by_user_id', table_name='training_programs')
    op.drop_index('ix_training_programs_is_template', table_name='training_programs')
    op.drop_index('ix_training_programs_structure_type', table_name='training_programs')
    op.drop_index('ix_training_programs_split_type', table_name='training_programs')
    op.drop_index('ix_training_programs_name', table_name='training_programs')
    op.drop_index('ix_training_programs_id', table_name='training_programs')
    op.drop_table('training_programs')
    
    # Remove deletion_requested_at from users
    print("Removing deletion_requested_at from users table...")
    op.drop_index('ix_users_deletion_requested', table_name='users')
    op.drop_column('users', 'deletion_requested_at')
    
    print("✓ Rollback complete")
