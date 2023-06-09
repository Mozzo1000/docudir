"""Add site_id to folder table

Revision ID: 2745f71d1518
Revises: f1f93547e279
Create Date: 2023-04-04 20:39:07.482484

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2745f71d1518'
down_revision = 'f1f93547e279'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('folders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=False))
        batch_op.create_foreign_key(None, 'sites', ['site_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('folders', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('site_id')

    # ### end Alembic commands ###
