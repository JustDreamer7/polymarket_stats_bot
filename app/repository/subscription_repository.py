import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.common_repository import CommonRepository, begin, connect
from app.models.subscription import Subscription
from app.models.user import User


class SubscriptionRepository(CommonRepository):
    @connect
    async def get_by_user_and_bettor(
        self, user_id: uuid.UUID, bettor_id: str, *, session: AsyncSession | None = None
    ) -> Subscription | None:
        result = await self._execute_connect(
            select(Subscription).where(
                and_(
                    Subscription.user_id == user_id, Subscription.bettor_id == bettor_id
                )
            ),
            session=session,
        )
        return result.scalar_one_or_none()

    @begin
    async def create(
        self, user_id: uuid.UUID, bettor_id: str, *, session: AsyncSession | None = None
    ) -> Subscription:
        subscription = Subscription(user_id=user_id, bettor_id=bettor_id)
        await self.insert(subscription, session=session)
        return subscription

    @connect
    async def get_by_user(
        self, user_id: uuid.UUID, *, session: AsyncSession | None = None
    ) -> list[Subscription]:
        result = await self._execute_connect(
            select(Subscription).where(Subscription.user_id == user_id),
            session=session,
        )
        return list(result.scalars().all())

    @connect
    async def get_distinct_bettor_ids(
        self, *, session: AsyncSession | None = None
    ) -> list[str]:
        result = await self._execute_connect(
            select(Subscription.bettor_id).distinct(), session=session
        )
        return [row[0] for row in result.all()]

    @connect
    async def get_subscribers_by_bettor(
        self, bettor_id: str, *, session: AsyncSession | None = None
    ) -> list[User]:
        result = await self._execute_connect(
            select(User)
            .join(Subscription, Subscription.user_id == User.uid)
            .where(Subscription.bettor_id == bettor_id),
            session=session,
        )
        return list(result.scalars().all())
