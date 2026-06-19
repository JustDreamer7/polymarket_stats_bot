from telegram import User as TelegramUser

from app.common.database import Database
from app.models.user import User
from app.repository.user_repository import UserRepository


class UserUseCases:
    def __init__(self, db: Database | None = None):
        self.user_repo = UserRepository(db)

    async def get_or_create(self, tg_user: TelegramUser) -> User:
        user = await self.user_repo.get_by_tg_id(tg_user.id)
        if user is not None:
            return user
        return await self.user_repo.create_user(tg_user)

    async def get_by_tg_id(self, tg_id: int) -> User | None:
        return await self.user_repo.get_by_tg_id(tg_id)
