from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'indexes'
down_revision = 'unindexed'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('psystem_idx_id64', 'populated_systems', ['id64'], unique=True)
    op.create_index('psystem_idx_systemid64', 'populated_systems', ['name'], unique=False)
    op.create_index('system_idx_id64', 'systems', ['id64'], unique=True)
    op.create_index('system_idx_name_btree', 'systems', ['name'], unique=False, postgresql_using='btree')
    op.create_index('system_idx_name_gin', 'systems', ['name'], unique=False, postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
    # op.create_index('system_idx_name_soundex', 'systems', ['name'], unique=False, postgresql_using='soundex')
    op.create_index('body_idx_id64', 'bodies', ['id64'], unique=True)
    op.create_index('body_idx_systemid64', 'bodies', ['systemId64'], unique=False)
    op.create_index('star_idx_id64', 'stars', ['id64'], unique=True)
    op.create_index('star_idx_systemid64', 'stars', ['systemId64'], unique=False)


def downgrade():
    op.drop_index('star_idx_systemid64', table_name='stars')
    op.drop_index('star_idx_id64', table_name='stars')
    op.drop_index('body_idx_systemid64', table_name='bodies')
    op.drop_index('body_idx_id64', table_name='bodies')
    # op.drop_index('system_idx_name_soundex', table_name='systems')
    op.drop_index('system_idx_name_gin', table_name='systems')
    op.drop_index('system_idx_name_btree', table_name='systems')
    op.drop_index('system_idx_id64', table_name='systems')
    op.drop_index('psystem_idx_systemid64', table_name='populated_systems')
    op.drop_index('psystem_idx_id64', table_name='populated_systems')
