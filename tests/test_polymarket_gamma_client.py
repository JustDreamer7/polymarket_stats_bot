import pytest
from zapros import StatusCodeError

from app.clients.polymarket_gamma_client import PolymarketGammaClient
from app.schemas.polymarket_gamma import PublicProfile


@pytest.fixture
def gamma_client():
    return PolymarketGammaClient()


class TestPolymarketGammaClient:
    @pytest.mark.asyncio
    async def test_get_public_profile_returns_profile(self, gamma_client, test_address):
        result = await gamma_client.get_public_profile(test_address)
        assert isinstance(result, PublicProfile)

    @pytest.mark.asyncio
    async def test_get_public_profile_bad_wallet_raises(self, gamma_client):
        with pytest.raises(StatusCodeError):
            await gamma_client.get_public_profile("0xdead")
