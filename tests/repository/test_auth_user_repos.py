from typing import cast

import pytest
from p2p.application import User
from p2p.infrastructure import AlchemyAuthRepo, AlchemyUserRepo
from p2p.infrastructure.repository.alchemy_models import metadata
from sqlalchemy import Column, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

sqlite_dsn = "sqlite+aiosqlite:///test.db"
sync_sqlite_dsn = "sqlite:///test.db"


def get_async_db_engine(dsn: str) -> AsyncEngine:
    engine = cast(
        AsyncEngine,
        create_async_engine(dsn, echo=True),
    )
    return engine


@pytest.fixture
def sync_engine():
    return create_engine(sync_sqlite_dsn, echo=True)


@pytest.fixture
def engine():
    return get_async_db_engine(sqlite_dsn)


@pytest.fixture
def make_db(sync_engine):
    metadata.create_all(sync_engine)
    yield
    metadata.drop_all(sync_engine)


@pytest.fixture
def auth_repo(engine, make_db):
    return AlchemyAuthRepo(engine)


@pytest.fixture
def user_repo(engine, make_db):
    return AlchemyUserRepo(engine)


@pytest.mark.asyncio
async def test_user(user_repo: AlchemyUserRepo):
    user = User(
        login="abc@def.gh",
        password="1231",
        merchant_name="some",
        presentation_id="12331212",
    )
    # save
    await user_repo.save(user)
    # reads
    db_user = await user_repo.get_by_presentation_id(user.presentation_id)
    assert user == db_user
    db_user = await user_repo.get_by_login(user.login)
    assert user == db_user

    # update
    user.password = "abc"
    await user_repo.save(user)
    db_user = await user_repo.get_by_login(user.login)
    assert user == db_user


@pytest.mark.asyncio
async def test_uath_data(auth_repo: AlchemyAuthRepo, user_repo: AlchemyUserRepo):
    user = User(
        login="abc@def.gh",
        password="1231",
        merchant_name="some",
        presentation_id="12331212",
    )
    # save
    await user_repo.save(user)

    auth_data = {"cookies": "some private data"}
    await auth_repo.save(user.login, auth_data)

    db_data = await auth_repo.read(user.login)
    assert db_data == auth_data

    auth_data = {"cookies": "some new data"}
    await auth_repo.save(user.login, auth_data)
    db_data = await auth_repo.read(user.login)
    assert db_data == auth_data
