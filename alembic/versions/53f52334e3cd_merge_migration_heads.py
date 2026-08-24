"""merge migration heads

Revision ID: 53f52334e3cd
Revises: 1a2b3c4d5e6f, 700dc9104d71
Create Date: 2026-08-24 12:54:43.014230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = '53f52334e3cd'
down_revision: Union[str, Sequence[str], None] = ('1a2b3c4d5e6f', '700dc9104d71')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
