"""rename user field

Revision ID: 160a2b921996
Revises: 4bd71454baf2
Create Date: 2022-09-12 12:55:46.516154

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "160a2b921996"
down_revision = "4bd71454baf2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "user",
        column_name="merchant_name",
        existing_type=sa.String(255),
        new_column_name="nick_name",
    )


def downgrade() -> None:
    op.alter_column(
        "user",
        column_name="nick_name",
        existing_type=sa.String(255),
        new_column_name="merchant_name",
    )
