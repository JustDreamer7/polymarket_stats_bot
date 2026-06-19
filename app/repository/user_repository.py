import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import User as TelegramUser

from app.common.common_repository import CommonRepository, begin, connect
from app.models.user import User


class UserRepository(CommonRepository):

    @begin
    async def create_user(
        self, tg_user: TelegramUser, *, session: AsyncSession | None = None
    ) -> User:
        user = User(
            user_name=tg_user.username or f"user_{tg_user.id}",
            user_tg_id=tg_user.id,
            is_bot=tg_user.is_bot,
            firstname=tg_user.first_name,
            lastname=tg_user.last_name,
            language_code=tg_user.language_code,
        )
        await self.insert(user, session=session)
        return user

    @connect
    async def get_by_tg_id(
        self, tg_id: int, *, session: AsyncSession | None = None
    ) -> User | None:
        result = await self._execute_connect(
            select(User).where(User.user_tg_id == tg_id), session=session
        )
        return result.scalar_one_or_none()

    @connect
    async def get_by_id(
        self, user_id: uuid.UUID, *, session: AsyncSession | None = None
    ) -> User | None:
        result = await self._execute_connect(
            select(User).where(User.uid == user_id), session=session
        )
        return result.scalar_one_or_none()
