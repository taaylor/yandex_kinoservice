"""Create schema

Revision ID: bf0ce157b753
Revises:
Create Date: 2025-04-19 16:02:09.210528

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bf0ce157b753"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS profile")
    op.execute("CREATE SCHEMA IF NOT EXISTS session")
    op.execute("SET search_path TO profile,session,public;")


def downgrade():
    op.execute("DROP SCHEMA IF EXISTS profile")
    op.execute("DROP SCHEMA IF EXISTS session")
