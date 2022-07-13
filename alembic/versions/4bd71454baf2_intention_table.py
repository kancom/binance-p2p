"""intention table

Revision ID: 4bd71454baf2
Revises: 8fdcee82efb7
Create Date: 2022-07-26 17:05:53.084166

"""
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from p2p.application import AdsFlow

# revision identifiers, used by Alembic.
revision = "4bd71454baf2"
down_revision = "8fdcee82efb7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "intention",
        sa.Column("intention_id", sa.Integer, primary_key=True),
        sa.Column("login", sa.String(length=255), sa.ForeignKey("user.login")),
        sa.Column("data", sa.JSON, nullable=False),
        sa.Column("status", sa.Enum(AdsFlow), default=AdsFlow.NEW),
        sa.Column("updated_at", sa.DateTime, default=datetime.now),
    )


def downgrade() -> None:
    op.drop_table("intention")
