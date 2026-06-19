from dataclasses import asdict
from functools import wraps
from typing import Any, Type, TypeVar

from sqlalchemy import Column, CursorResult, Executable
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine.interfaces import _CoreAnyExecuteParams
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import TypedReturnsRows

from app.common.database import Base, Database

_T = TypeVar("_T", bound=Any)
_Base = TypeVar("_Base", bound=Any)


class DuplicateKeyError(Exception):
    pass


class CommonRepository:
    _BULK_BATCH_SIZE = 1000

    def __init__(self, db: Database) -> None:
        self.db = db

    async def _insert(self, obj: _Base, session: AsyncSession) -> _Base:
        try:
            session.add(obj)
            await session.flush()
        except IntegrityError as err:
            raise DuplicateKeyError(f"Duplicate key error for {obj}") from err
        return obj

    async def insert(self, obj: _Base, session: AsyncSession | None = None) -> _Base:
        if session is not None:
            return await self._insert(obj, session)
        async with self.db.begin() as session:
            return await self._insert(obj, session)

    async def _upsert(self, obj: _Base, session: AsyncSession) -> _Base:
        merged_obj = await session.merge(obj)
        await session.flush()
        return merged_obj

    async def upsert(self, obj: _Base, session: AsyncSession | None = None) -> _Base:
        if session is not None:
            return await self._upsert(obj, session)
        async with self.db.begin() as session:
            return await self._upsert(obj, session)

    async def _delete(self, obj: _Base, session: AsyncSession) -> None:
        await session.delete(obj)
        await session.flush()

    async def delete(self, obj: _Base, session: AsyncSession = None) -> None:
        if session is not None:
            return await self._delete(obj, session)
        async with self.db.begin() as session:
            return await self._delete(obj, session)

    async def _execute(
        self,
        stmt: Executable | TypedReturnsRows[_T],
        session: AsyncSession | None = None,
        parameters: _CoreAnyExecuteParams | None = None,
    ) -> CursorResult[_T]:
        if session is not None:
            return await session.execute(stmt, parameters)
        async with self.db.begin() as session:
            return await session.execute(stmt, parameters)

    async def _execute_connect(
        self,
        stmt: Executable | TypedReturnsRows[_T],
        session: AsyncSession | None = None,
        parameters: _CoreAnyExecuteParams | None = None,
    ) -> CursorResult[_T]:
        if session is not None:
            return await session.execute(stmt, parameters)
        async with self.db.begin_readonly() as session:
            return await session.execute(stmt, parameters)

    async def _bulk_merge_dataclass(
        self,
        items: list[_T],
        model: Type[Base],
        *,
        session: AsyncSession | None = None,
        index_elements: list[Column],
    ) -> int:
        for offset in range(0, len(items), self._BULK_BATCH_SIZE):
            batch = items[offset : offset + self._BULK_BATCH_SIZE]
            values = [asdict(_) for _ in batch]
            stmt = (
                pg_insert(model)
                .values(values)
                .on_conflict_do_update(
                    index_elements=index_elements,
                    set_={
                        col.name: getattr(pg_insert(model).excluded, col.name)
                        for col in model.__table__.columns
                        if col not in index_elements
                    },
                )
            )
            await session.execute(stmt)
        return len(items)


def begin(func):
    @wraps(func)
    async def wrapper(
        self: CommonRepository, *args, session: AsyncSession | None = None, **kwargs
    ):
        if session is not None:
            return await func(self, *args, session=session, **kwargs)
        async with self.db.begin() as session:
            return await func(self, *args, session=session, **kwargs)

    return wrapper


def connect(func):
    @wraps(func)
    async def wrapper(
        self: CommonRepository, *args, session: AsyncSession | None = None, **kwargs
    ):
        if session is not None:
            return await func(self, *args, session=session, **kwargs)
        async with self.db.begin_readonly() as session:
            return await func(self, *args, session=session, **kwargs)

    return wrapper
