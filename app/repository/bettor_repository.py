import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from app.common.common_repository import CommonRepository, begin, connect
from app.models.bettor import Bettor
from app.models.bettor_stats import BettorStats
from app.models.subscription import Subscription
from app.schemas.polymarket_data import BettorStatsSnapshot
from app.schemas.polymarket_gamma import PublicProfile


class BettorRepository(CommonRepository):

    @connect
    async def get_all(self, *, session: AsyncSession | None = None) -> list[Bettor]:
        result = await self._execute_connect(select(Bettor), session=session)
        return list(result.scalars().all())

    @connect
    async def get_by_wallet(
        self, wallet: str, *, session: AsyncSession | None = None
    ) -> Bettor | None:
        result = await self._execute_connect(
            select(Bettor).where(Bettor.proxy_wallet == wallet), session=session
        )
        return result.scalar_one_or_none()

    @connect
    async def get_by_name(
        self, name: str, *, session: AsyncSession | None = None
    ) -> Bettor | None:
        result = await self._execute_connect(
            select(Bettor).where(Bettor.name == name), session=session
        )
        return result.scalar_one_or_none()

    @connect
    async def get_subscription_page(
        self,
        user_id: uuid.UUID,
        offset: int,
        limit: int,
        *,
        session: AsyncSession | None = None,
    ) -> tuple[list[Bettor], int]:
        # TODO: divide to diff function, add cache
        total_result = await self._execute_connect(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.user_id == user_id),
            session=session,
        )
        total = total_result.scalar_one()

        result = await self._execute_connect(
            select(Bettor)
            .outerjoin(BettorStats, BettorStats.uid == Bettor.proxy_wallet)
            .join(Subscription, Subscription.bettor_id == Bettor.proxy_wallet)
            .options(contains_eager(Bettor.stats))
            .where(Subscription.user_id == user_id)
            .order_by(Bettor.name)
            .offset(offset)
            .limit(limit),
            session=session,
        )
        return list(result.scalars().all()), total

    @begin
    async def create(
        self, profile: PublicProfile, *, session: AsyncSession | None = None
    ) -> Bettor:
        bettor = Bettor(
            proxy_wallet=profile.proxy_wallet, name=profile.name, platform="polymarket"
        )
        return await self.insert(bettor, session=session)

    @begin
    async def bulk_upsert_stats(
        self, stats: list[BettorStatsSnapshot], *, session: AsyncSession | None = None
    ) -> int:
        return await self._bulk_merge_dataclass(
            items=stats,
            model=BettorStats,
            index_elements=[BettorStats.uid],
            session=session,
        )
