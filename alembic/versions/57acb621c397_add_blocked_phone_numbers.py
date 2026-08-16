"""Add blocked_phone_numbers

Revision ID: 57acb621c397
Revises: a3eb2644d4b5
Create Date: 2026-08-16 21:16:42.362572

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57acb621c397'
down_revision: Union[str, Sequence[str], None] = 'a3eb2644d4b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
