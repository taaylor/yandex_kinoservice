"""Первая миграция

Revision ID: 3099bf76582c
Revises: eda20bd2a873
Create Date: 2025-04-16 23:31:46.770587

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3099bf76582c'
down_revision: Union[str, None] = 'eda20bd2a873'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('example_2',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('some_column', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('example_2')
    # ### end Alembic commands ###
