from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from dotenv import load_dotenv

from app.common.database import Database
from app.config import get_settings
from app.schemas.polymarket_gamma import PublicProfile

TEST_ADDRESS = "0x8eb2df7e7b89d594e0af2d05c3c79e0b79777ab1"
TEST_NAME = "dis0rdered"

load_dotenv(dotenv_path="./tests/env/test.env")


@pytest.fixture
def test_address():
    return TEST_ADDRESS


@pytest.fixture
def test_name():
    return TEST_NAME


@pytest_asyncio.fixture
async def clear_database() -> Database:
    config = get_settings()
    db = Database(config["database"])
    await db.drop_database()
    await db.create_database()


@pytest.fixture
def make_profile():
    def _make(
        proxy_wallet: str = "0x" + "1" * 40,
        name: str = "Alice",
    ) -> PublicProfile:
        return PublicProfile(
            proxy_wallet=proxy_wallet,
            name=name,
            verified_badge=False,
        )

    return _make


@pytest.fixture
def make_tg_user():
    # pylint: disable=too-many-positional-arguments
    def _make(
        tg_id: int = 100,
        username: str = "tg_user",
        first_name: str = "Test",
        last_name: str | None = None,
        is_bot: bool = False,
        language_code: str | None = "en",
    ) -> MagicMock:
        tg_user = MagicMock()
        tg_user.id = tg_id
        tg_user.username = username
        tg_user.first_name = first_name
        tg_user.last_name = last_name
        tg_user.is_bot = is_bot
        tg_user.language_code = language_code
        return tg_user

    return _make
