"""Add cpc_bid and fix permissions

Revision ID: b4fb2644d4b6
Revises: 57acb621c397
Create Date: 2026-08-20 23:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4fb2644d4b6'
down_revision: Union[str, Sequence[str], None] = '57acb621c397'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # 1. Add cpc_bid to ads if it doesn't exist
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('ads')]
    if 'cpc_bid' not in columns:
        op.add_column('ads', sa.Column('cpc_bid', sa.DECIMAL(precision=10, scale=2), server_default='0.00', nullable=True))
        
    # 2. Fix permissions for newly added tables by granting all privileges to the current connected user
    op.execute('''
    DO $$ 
    DECLARE
        cur_user text;
    BEGIN
        SELECT current_user INTO cur_user;
        EXECUTE 'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ' || quote_ident(cur_user);
        EXECUTE 'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ' || quote_ident(cur_user);
    END $$;
    ''')

def downgrade() -> None:
    pass
