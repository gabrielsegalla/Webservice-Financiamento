"""empty message

Revision ID: 3492ab43a7ad
Revises: 2bdddd91ad18
Create Date: 2018-11-17 23:15:24.509865

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3492ab43a7ad'
down_revision = '2bdddd91ad18'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('usuario', sa.Column('email', sa.String(length=120), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('usuario', 'email')
    # ### end Alembic commands ###
