import pytest

from app.models.subscription import Subscription
from app.use_cases.bettor_use_cases import BettorUseCases
from app.use_cases.subscription_use_cases import SubscriptionUseCases
from app.use_cases.user_use_cases import UserUseCases


@pytest.fixture
def subscription_use_cases(clear_database):
    return SubscriptionUseCases(clear_database)


@pytest.fixture
async def setup_user_and_bettor(
    subscription_use_cases, clear_database, make_profile, make_tg_user
):
    db = clear_database
    user_uc = UserUseCases(db)
    bettor_uc = BettorUseCases(db)

    user = await user_uc.get_or_create(make_tg_user(tg_id=1, username="u1"))
    bettor = await bettor_uc.get_or_create(make_profile(name="bettor1"))

    return user.uid, bettor.proxy_wallet


class TestSubscriptionUseCases:
    @pytest.mark.asyncio
    async def test_add_subscription_creates(
        self, subscription_use_cases, setup_user_and_bettor
    ):
        user_id, bettor_id = setup_user_and_bettor

        added = await subscription_use_cases.add_subscription(user_id, bettor_id)
        assert added is True

        subs = await subscription_use_cases.get_user_subscriptions(user_id)
        assert len(subs) == 1
        assert isinstance(subs[0], Subscription)
        assert subs[0].bettor_id == bettor_id

    @pytest.mark.asyncio
    async def test_add_subscription_duplicate_returns_false(
        self, subscription_use_cases, setup_user_and_bettor
    ):
        user_id, bettor_id = setup_user_and_bettor

        first = await subscription_use_cases.add_subscription(user_id, bettor_id)
        second = await subscription_use_cases.add_subscription(user_id, bettor_id)

        assert first is True
        assert second is False

        subs = await subscription_use_cases.get_user_subscriptions(user_id)
        assert len(subs) == 1

    @pytest.mark.asyncio
    async def test_remove_subscription_removes(
        self, subscription_use_cases, setup_user_and_bettor
    ):
        user_id, bettor_id = setup_user_and_bettor
        await subscription_use_cases.add_subscription(user_id, bettor_id)

        removed = await subscription_use_cases.remove_subscription(user_id, bettor_id)
        assert removed is True

        subs = await subscription_use_cases.get_user_subscriptions(user_id)
        assert subs == []

    @pytest.mark.asyncio
    async def test_remove_subscription_not_found_returns_false(
        self, subscription_use_cases, setup_user_and_bettor
    ):
        user_id, bettor_id = setup_user_and_bettor

        removed = await subscription_use_cases.remove_subscription(user_id, bettor_id)
        assert removed is False

    @pytest.mark.asyncio
    async def test_get_distinct_bettor_ids(
        self,
        subscription_use_cases,
        clear_database,
        make_profile,
        make_tg_user,
    ):
        db = clear_database
        user_uc = UserUseCases(db)
        bettor_uc = BettorUseCases(db)

        user = await user_uc.get_or_create(make_tg_user(tg_id=2, username="u2"))
        b1 = await bettor_uc.get_or_create(
            make_profile(proxy_wallet="0x" + "1" * 40, name="b1")
        )
        b2 = await bettor_uc.get_or_create(
            make_profile(proxy_wallet="0x" + "2" * 40, name="b2")
        )

        await subscription_use_cases.add_subscription(user.uid, b1.proxy_wallet)
        await subscription_use_cases.add_subscription(user.uid, b2.proxy_wallet)

        ids = await subscription_use_cases.get_distinct_bettor_ids()
        assert sorted(ids) == sorted([b1.proxy_wallet, b2.proxy_wallet])

    @pytest.mark.asyncio
    async def test_get_distinct_bettor_ids_empty(self, subscription_use_cases):
        ids = await subscription_use_cases.get_distinct_bettor_ids()
        assert ids == []
