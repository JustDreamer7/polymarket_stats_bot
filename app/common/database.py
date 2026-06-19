import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import Engine, create_engine, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import DatabaseConfig
from app.common.logger import logger
from app.common.models import Base


@asynccontextmanager
async def transaction_session(
    session: AsyncSession,
) -> AsyncGenerator[AsyncSession, None]:
    try:
        yield session
        await session.commit()
    except Exception as e:
        logger.error("Error in session: %s", str(e))
        await session.rollback()
        raise
    finally:
        task = asyncio.create_task(session.close())
        await asyncio.shield(task)


@asynccontextmanager
async def readonly_session(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    try:
        yield session
    finally:
        session.expunge_all()
        await session.rollback()
        task = asyncio.create_task(session.close())
        await asyncio.shield(task)


class Database:
    def __init__(self, config: DatabaseConfig):
        self._async_database_uri = config["async_database_uri"]
        self._sync_database_uri = config["sync_database_uri"]
        self._pool_recycle = config.get("pool_recycle", 900)
        self._pool_size = config.get("pool_size", 5)
        self._max_overflow = config.get("max_overflow", 10)
        self._schema = config.get("schema")

        async_connect_args = {}
        sync_connect_args = {}
        if self._schema:
            async_connect_args["server_settings"] = {"search_path": self._schema}
            sync_connect_args["options"] = f"-c search_path={self._schema}"
        self._async_engine = self._setup_engine(async_connect_args)
        self._sync_engine = self._setup_sync_engine(sync_connect_args)

        self._async_session_factory = async_sessionmaker(
            self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    def _setup_sync_engine(self, connect_args: dict) -> Engine:
        try:
            return create_engine(
                self._sync_database_uri,
                echo=False,
                pool_pre_ping=True,
                pool_size=self._pool_size,
                max_overflow=self._max_overflow,
                pool_recycle=self._pool_recycle,
                connect_args=connect_args,
            )
        except Exception as e:
            logger.error("Failed to create database engine: %s", str(e))
            raise

    def _setup_engine(self, connect_args: dict) -> AsyncEngine:
        try:
            return create_async_engine(
                self._async_database_uri,
                echo=False,
                pool_pre_ping=True,
                pool_size=self._pool_size,
                max_overflow=self._max_overflow,
                pool_recycle=self._pool_recycle,
                connect_args=connect_args,
            )
        except Exception as e:
            logger.error("Failed to create database engine: %s", str(e))
            raise

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._async_session_factory() as session:
            yield session

    def begin(self):
        return transaction_session(self._async_session_factory())

    def begin_readonly(self):
        return readonly_session(self._async_session_factory())

    async def create_database(self) -> None:
        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_database(self) -> None:
        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def startup_probe(self) -> None:
        async with self._async_engine.begin() as conn:
            await conn.execute(select(1))

    async def dispose_engine(self) -> None:
        if self._async_engine:
            await self._async_engine.dispose()
