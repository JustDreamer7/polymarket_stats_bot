import uuid

from app.common.database import Database
from app.models.bettor import Bettor
from app.repository.bettor_repository import BettorRepository
from app.schemas.polymarket_gamma import PublicProfile


class BettorUseCases:
    def __init__(self, db: Database | None = None):
        self.bettor_repo = BettorRepository(db)

    async def search_bettor(self, query: str) -> Bettor | None:
        if query.startswith("0x"):
            return await self.bettor_repo.get_by_wallet(query)
        return await self.bettor_repo.get_by_name(query)

    async def get_or_create(self, profile: PublicProfile) -> Bettor:
        bettor = await self.bettor_repo.get_by_wallet(profile.proxy_wallet)
        if bettor is not None:
            return bettor
        return await self.bettor_repo.create(profile)

    async def get_subscription_page(
        self, user_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[Bettor], int]:
        return await self.bettor_repo.get_subscription_page(user_id, offset, limit)
