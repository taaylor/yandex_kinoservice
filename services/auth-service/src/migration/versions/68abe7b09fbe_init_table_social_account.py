"""init_table_social_account

Revision ID: 68abe7b09fbe
Revises: 715c40ff5e28
Create Date: 2025-05-14 00:21:53.874507

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "68abe7b09fbe"
down_revision: Union[str, None] = "715c40ff5e28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "social_account",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "social_id",
            sa.String(length=255),
            nullable=False,
            comment="Уникальный идентификатор пользователя в социальной сети",
        ),
        sa.Column(
            "social_name",
            sa.String(length=255),
            nullable=False,
            comment="Наименование поставщика услуг",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["profile.user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("social_name", "social_id", name="social_idx"),
        sa.UniqueConstraint("user_id", "social_name", name="user_social_idx"),
        schema="profile",
    )
    op.add_column(
        "user_cred",
        sa.Column(
            "is_fictional_email",
            sa.Boolean(),
            server_default=sa.text("'false'"),
            nullable=False,
        ),
        schema="profile",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user_cred", "is_fictional_email", schema="profile")
    op.drop_table("social_account", schema="profile")
    # ### end Alembic commands ###
