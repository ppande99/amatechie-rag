"""Database tests need a Postgres with pgvector. Set TEST_DATABASE_URL to run them; otherwise skipped.

    TEST_DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/rag_test pytest
"""

import os

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models import Base

TEST_DB_URL = os.environ.get("TEST_DATABASE_URL")


@pytest_asyncio.fixture
async def session():
    if not TEST_DB_URL:
        pytest.skip("TEST_DATABASE_URL not set")
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as s:
        yield s
    await engine.dispose()
