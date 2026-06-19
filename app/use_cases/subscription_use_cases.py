import uuid

from app.common.database import Database
from app.models.subscription import Subscription
from app.repository.subscription_repository import SubscriptionRepository


class SubscriptionUseCases:
    def __init__(self, db: Database | None = None):
        self.subscription_repo = SubscriptionRepository(db)

    async def add_subscription(self, user_id: uuid.UUID, bettor_id: str) -> bool:
        existing = await self.subscription_repo.get_by_user_and_bettor(
            user_id, bettor_id
        )
        if existing:
            return False
        await self.subscription_repo.create(user_id=user_id, bettor_id=bettor_id)
        return True

    async def remove_subscription(self, user_id: uuid.UUID, bettor_id: str) -> bool:
        subscription = await self.subscription_repo.get_by_user_and_bettor(
            user_id, bettor_id
        )
        if subscription is None:
            return False
        await self.subscription_repo.delete(subscription)
        return True

    async def get_user_subscriptions(self, user_id: uuid.UUID) -> list[Subscription]:
        return await self.subscription_repo.get_by_user(user_id)

    async def get_distinct_bettor_ids(self) -> list[str]:
        return await self.subscription_repo.get_distinct_bettor_ids()
