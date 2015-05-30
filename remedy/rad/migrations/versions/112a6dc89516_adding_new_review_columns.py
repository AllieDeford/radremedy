"""Adding new review columns.

Revision ID: 112a6dc89516
Revises: 17929a019cff
Create Date: 2015-05-26 22:48:12.883000

"""

# revision identifiers, used by Alembic.
revision = '112a6dc89516'
down_revision = '17929a019cff'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('review', sa.Column('composite_rating', sa.Float(), nullable=True))
    op.add_column('review', sa.Column('intake_rating', sa.Integer(), nullable=True))
    op.add_column('review', sa.Column('staff_rating', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('review', 'staff_rating')
    op.drop_column('review', 'intake_rating')
    op.drop_column('review', 'composite_rating')
    ### end Alembic commands ###
