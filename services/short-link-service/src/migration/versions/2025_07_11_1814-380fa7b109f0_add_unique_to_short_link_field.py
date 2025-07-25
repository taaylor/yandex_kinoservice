"""add unique to short link field

Revision ID: 380fa7b109f0
Revises: 08af4348970d
Create Date: 2025-07-11 18:14:45.323812+00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "380fa7b109f0"
down_revision: Union[str, None] = "08af4348970d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_link_short_link_short_url", table_name="short_link", schema="link")
    op.create_index(
        op.f("ix_link_short_link_short_url"),
        "short_link",
        ["short_url"],
        unique=True,
        schema="link",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        op.f("ix_link_short_link_short_url"),
        table_name="short_link",
        schema="link",
    )
    op.create_index(
        "ix_link_short_link_short_url",
        "short_link",
        ["short_url"],
        unique=False,
        schema="link",
    )
    # ### end Alembic commands ###
