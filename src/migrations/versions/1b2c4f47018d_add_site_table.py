"""Add site table

Revision ID: 1b2c4f47018d
Revises: 12886216a763
Create Date: 2023-04-01 20:08:01.631957

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1b2c4f47018d'
down_revision = '12886216a763'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sites',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_sites',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('permission', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_sites')
    op.drop_table('sites')
    # ### end Alembic commands ###
