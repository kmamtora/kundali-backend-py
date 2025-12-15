"""Initial user model

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table with all required fields and indexes."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique user identifier'),
        sa.Column('email', sa.String(length=255), nullable=False, comment="User's email address (unique)"),
        sa.Column('hashed_password', sa.String(length=255), nullable=False, comment='Bcrypt hashed password'),
        sa.Column('full_name', sa.String(length=255), nullable=False, comment="User's full name"),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Whether the user account is active'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, comment='Whether the user has superuser privileges'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when the record was last updated'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create indexes
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_index('ix_users_email_active', 'users', ['email', 'is_active'], unique=False)
    op.create_index('ix_users_is_active', 'users', ['is_active'], unique=False)


def downgrade() -> None:
    """Drop users table and all associated indexes."""
    # Drop indexes
    op.drop_index('ix_users_is_active', table_name='users')
    op.drop_index('ix_users_email_active', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    
    # Drop table
    op.drop_table('users')
