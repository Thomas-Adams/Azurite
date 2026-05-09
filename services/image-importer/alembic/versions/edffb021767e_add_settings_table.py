"""add settings table

Revision ID: edffb021767e
Revises: ec677a2f0757
Create Date: 2026-05-09 14:44:07.272351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'edffb021767e'
down_revision: Union[str, Sequence[str], None] = 'ec677a2f0757'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'settings',
        sa.Column('image_root', sa.Text(), nullable=False),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='pony_image',
    )


def downgrade() -> None:
    op.drop_table('settings', schema='pony_image')
