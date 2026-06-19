import pytest

from app.models.user import User
from app.use_cases.user_use_cases import UserUseCases


@pytest.fixture
def user_use_cases(clear_database):
    return UserUseCases(clear_database)


class TestUserUseCases:
    @pytest.mark.asyncio
    async def test_get_or_create_creates_new_user(self, user_use_cases, make_tg_user):
        tg_user = make_tg_user(tg_id=1, username="alice")
        user = await user_use_cases.get_or_create(tg_user)

        assert isinstance(user, User)
        assert user.user_tg_id == 1
        assert user.user_name == "alice"

    @pytest.mark.asyncio
    async def test_get_or_create_returns_existing_user(
        self, user_use_cases, make_tg_user
    ):
        tg_user = make_tg_user(tg_id=2, username="bob")
        created = await user_use_cases.get_or_create(tg_user)
        again = await user_use_cases.get_or_create(tg_user)

        assert again.uid == created.uid

    @pytest.mark.asyncio
    async def test_get_or_create_username_fallback_when_none(
        self, user_use_cases, make_tg_user
    ):
        tg_user = make_tg_user(tg_id=3, username=None)
        user = await user_use_cases.get_or_create(tg_user)
        # username is None -> username = f"user_{id}"
        assert user.user_name == "user_3"

    @pytest.mark.asyncio
    async def test_get_by_tg_id_found(self, user_use_cases, make_tg_user):
        await user_use_cases.get_or_create(make_tg_user(tg_id=4, username="carol"))
        user = await user_use_cases.get_by_tg_id(4)
        assert user is not None
        assert user.user_name == "carol"

    @pytest.mark.asyncio
    async def test_get_by_tg_id_not_found(self, user_use_cases):
        user = await user_use_cases.get_by_tg_id(999)
        assert user is None
