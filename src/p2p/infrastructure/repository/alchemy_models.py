from datetime import datetime

from p2p.application import AdsFlow
from sqlalchemy import Column, Enum, Integer, MetaData, String, Table
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import JSON
from sqlalchemy.types import DateTime

metadata = MetaData()


UserModel = Table(
    "user",
    metadata,
    Column("login", String(length=255), primary_key=True),
    Column("password", String(length=255)),
    Column("nick_name", String(length=255)),
    Column("active_until", DateTime),
    Column("presentation_id", String(length=255)),
    Column("registered_at", DateTime, default=datetime.now),
    Column("updated_at", DateTime, default=datetime.now),
)


AuthDataModel = Table(
    "auth_data",
    metadata,
    Column("login", String(length=255), ForeignKey("user.login"), primary_key=True),
    Column("data", JSON, nullable=False),
    Column("updated_at", DateTime, default=datetime.now),
)

IntentionModel = Table(
    "intention",
    metadata,
    Column(
        "intention_id",
        Integer,
        primary_key=True,
    ),
    Column(
        "login",
        String(length=255),
        ForeignKey("user.login"),
    ),
    Column("data", JSON, nullable=False),
    Column("status", Enum(AdsFlow), default=AdsFlow.NEW),
    Column("updated_at", DateTime, default=datetime.now),
)
