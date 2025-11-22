"""Add organizations and update users

Revision ID: 2cc58ca97800
Revises: ddef93c02177
Create Date: 2025-11-22 19:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2cc58ca97800'
down_revision: Union[str, None] = 'ddef93c02177'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create subscription tier and status enums
    subscription_tier_enum = postgresql.ENUM('FREE', 'PRO', name='subscription_tier', create_type=False)
    subscription_tier_enum.create(op.get_bind(), checkfirst=True)
    
    subscription_status_enum = postgresql.ENUM('ACTIVE', 'CANCELED', 'EXPIRED', name='subscription_status', create_type=False)
    subscription_status_enum.create(op.get_bind(), checkfirst=True)
    
    user_role_enum = postgresql.ENUM('USER', 'ADMIN', name='user_role', create_type=False)
    user_role_enum.create(op.get_bind(), checkfirst=True)
    
    # Create organizations table
    op.create_table('organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('subscription_tier', subscription_tier_enum, nullable=False, server_default='FREE'),
        sa.Column('subscription_status', subscription_status_enum, nullable=False, server_default='ACTIVE'),
        sa.Column('lemonsqueezy_customer_id', sa.String(length=255), nullable=True),
        sa.Column('lemonsqueezy_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lemonsqueezy_customer_id'),
        sa.UniqueConstraint('lemonsqueezy_subscription_id')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_lemonsqueezy_customer_id'), 'organizations', ['lemonsqueezy_customer_id'], unique=True)
    op.create_index(op.f('ix_organizations_lemonsqueezy_subscription_id'), 'organizations', ['lemonsqueezy_subscription_id'], unique=True)
    
    # Add new columns to users table
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('role', user_role_enum, nullable=False, server_default='USER'))
    op.add_column('users', sa.Column('profile_image_url', sa.String(length=500), nullable=True))
    
    # Make full_name non-nullable (update existing NULL values first)
    op.execute("UPDATE users SET full_name = 'User' WHERE full_name IS NULL")
    op.alter_column('users', 'full_name',
                    existing_type=sa.String(length=255),
                    nullable=False)
    
    # Add organization_id column (temporarily nullable)
    op.add_column('users', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create a default organization for existing users
    op.execute("""
        INSERT INTO organizations (id, name, subscription_tier, subscription_status, created_at, updated_at)
        VALUES (gen_random_uuid(), 'Default Organization', 'FREE', 'ACTIVE', now(), now())
    """)
    
    # Update existing users to reference the default organization
    op.execute("""
        UPDATE users 
        SET organization_id = (SELECT id FROM organizations WHERE name = 'Default Organization' LIMIT 1)
        WHERE organization_id IS NULL
    """)
    
    # Now make organization_id non-nullable and add foreign key
    op.alter_column('users', 'organization_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=False)
    op.create_foreign_key('users_organization_id_fkey', 'users', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('ix_users_organization_id'), 'users', ['organization_id'], unique=False)
    
    # Remove old is_superuser column
    op.drop_column('users', 'is_superuser')


def downgrade() -> None:
    # Add back is_superuser column
    op.add_column('users', sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'))
    
    # Drop new columns from users
    op.drop_index(op.f('ix_users_organization_id'), table_name='users')
    op.drop_constraint('users_organization_id_fkey', 'users', type_='foreignkey')
    op.drop_column('users', 'organization_id')
    op.drop_column('users', 'profile_image_url')
    op.drop_column('users', 'role')
    op.drop_column('users', 'is_verified')
    
    # Make full_name nullable again
    op.alter_column('users', 'full_name',
                    existing_type=sa.String(length=255),
                    nullable=True)
    
    # Drop organizations table
    op.drop_index(op.f('ix_organizations_lemonsqueezy_subscription_id'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_lemonsqueezy_customer_id'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')
    
    # Drop enums
    sa.Enum(name='user_role').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='subscription_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='subscription_tier').drop(op.get_bind(), checkfirst=True)
