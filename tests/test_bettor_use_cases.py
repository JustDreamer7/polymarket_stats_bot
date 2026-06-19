import uuid
from unittest.mock import AsyncMock

import pytest

from app.models.bettor import Bettor
from app.models.bettor_stats import BettorStats
from app.models.subscription import Subscription
from app.models.user import User
from app.use_cases.bettor_use_cases import BettorUseCases


@pytest.fixture
def bettor_use_cases(clear_database):
    return BettorUseCases(clear_database)


class TestBettorUseCases:
    @pytest.mark.asyncio
    async def test_get_or_create_creates_new_bettor(
        self, bettor_use_cases, make_profile
    ):
        profile = make_profile()
        bettor = await bettor_use_cases.get_or_create(profile)

        assert isinstance(bettor, Bettor)
        assert bettor.proxy_wallet == profile.proxy_wallet
        assert bettor.name == profile.name
        assert bettor.platform == "polymarket"

    @pytest.mark.asyncio
    async def test_get_or_create_returns_existing_bettor(
        self, bettor_use_cases, make_profile
    ):
        profile = make_profile()
        created = await bettor_use_cases.get_or_create(profile)
        again = await bettor_use_cases.get_or_create(profile)
        assert again.proxy_wallet == created.proxy_wallet

    @pytest.mark.asyncio
    async def test_search_bettor_by_wallet_found(self, bettor_use_cases, make_profile):
        profile = make_profile(proxy_wallet="0x" + "1" * 40, name="alice")
        await bettor_use_cases.get_or_create(profile)

        found = await bettor_use_cases.search_bettor("0x" + "1" * 40)
        assert found is not None
        assert found.name == "alice"

    @pytest.mark.asyncio
    async def test_search_bettor_by_name_found(self, bettor_use_cases, make_profile):
        profile = make_profile(name="bob")
        await bettor_use_cases.get_or_create(profile)

        found = await bettor_use_cases.search_bettor("bob")
        assert found is not None
        assert found.name == "bob"

    @pytest.mark.asyncio
    async def test_search_bettor_by_wallet_not_found(self, bettor_use_cases):
        bettor_use_cases.bettor_repo.get_by_wallet = AsyncMock(return_value=None)
        bettor_use_cases.bettor_repo.get_by_name = AsyncMock(return_value=None)

        found = await bettor_use_cases.search_bettor("0x" + "9" * 40)

        assert found is None
        bettor_use_cases.bettor_repo.get_by_wallet.assert_called_once_with(
            "0x" + "9" * 40
        )
        bettor_use_cases.bettor_repo.get_by_name.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_bettor_by_name_not_found(self, bettor_use_cases):
        bettor_use_cases.bettor_repo.get_by_wallet = AsyncMock(return_value=None)
        bettor_use_cases.bettor_repo.get_by_name = AsyncMock(return_value=None)

        found = await bettor_use_cases.search_bettor("nobody")

        assert found is None
        bettor_use_cases.bettor_repo.get_by_name.assert_called_once_with("nobody")
        bettor_use_cases.bettor_repo.get_by_wallet.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_subscription_page_empty(self, bettor_use_cases):
        bettors, total = await bettor_use_cases.get_subscription_page(
            uuid.uuid4(), offset=0, limit=5
        )
        assert bettors == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_subscription_page_returns_bettors(
        self, bettor_use_cases, make_profile, clear_database
    ):
        db = clear_database
        profile = make_profile(name="dave")
        bettor = await bettor_use_cases.get_or_create(profile)

        async with db.begin() as session:
            session.add(
                BettorStats(
                    uid=bettor.proxy_wallet,
                    closed_trades_count=1,
                    current_trades_count=0,
                    closed_trades_volume=10.0,
                    current_trades_volume=0.0,
                    winnings=2.0,
                    winrate=100.0,
                    roi=20.0,
                )
            )
            user = User(user_name="u", user_tg_id=42)
            session.add(user)
            await session.flush()
            session.add(Subscription(user_id=user.uid, bettor_id=bettor.proxy_wallet))

        bettors, total = await bettor_use_cases.get_subscription_page(
            user.uid, offset=0, limit=5
        )
        assert total == 1
        assert len(bettors) == 1
        assert bettors[0].proxy_wallet == bettor.proxy_wallet
        assert bettors[0].stats is not None
