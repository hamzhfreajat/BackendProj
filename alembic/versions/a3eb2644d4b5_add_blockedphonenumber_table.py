"""Add BlockedPhoneNumber table

Revision ID: a3eb2644d4b5
Revises: f44940494461
Create Date: 2026-08-09 11:19:40.554512

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3eb2644d4b5'
down_revision: Union[str, Sequence[str], None] = 'f44940494461'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('blocked_phone_numbers',
    sa.Column('phone_number', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('phone_number')
    )
    op.create_index(op.f('ix_blocked_phone_numbers_phone_number'), 'blocked_phone_numbers', ['phone_number'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_blocked_phone_numbers_phone_number'), table_name='blocked_phone_numbers')
    op.drop_table('blocked_phone_numbers')
