"""init

Revision ID: 8fdcee82efb7
Revises: 
Create Date: 2022-07-19 11:03:13.889649

"""
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from p2p.application import UserAction

# revision identifiers, used by Alembic.
revision = "8fdcee82efb7"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("login", sa.String(length=255), primary_key=True),
        sa.Column("password", sa.String(length=255)),
        sa.Column("merchant_name", sa.String(length=255)),
        sa.Column("active_until", sa.DateTime),
        sa.Column("registered_at", sa.DateTime, default=datetime.now),
        sa.Column("updated_at", sa.DateTime, default=datetime.now),
        sa.Column("presentation_id", sa.String(length=255), index=True),
    )

    op.create_table(
        "auth_data",
        sa.Column(
            "login",
            sa.String(length=255),
            sa.ForeignKey("user.login"),
            primary_key=True,
        ),
        sa.Column("data", sa.JSON, nullable=False),
        sa.Column("updated_at", sa.DateTime, default=datetime.now),
    )


def downgrade() -> None:
    op.drop_table("auth_data")
    op.drop_table("user")
