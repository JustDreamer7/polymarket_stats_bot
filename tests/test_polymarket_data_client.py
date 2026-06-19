import pytest
from zapros import StatusCodeError

from app.clients.polymarket_data_client import PolymarketDataClient
from app.schemas.polymarket_data import (
    Activity,
    ClosedPosition,
    LeaderboardEntry,
    Position,
    Trade,
)


@pytest.fixture
def data_client():
    return PolymarketDataClient()


class TestPolymarketDataClient:
    @pytest.mark.asyncio
    async def test_get_positions_returns_list(self, data_client, test_address):
        result = await data_client.get_positions(test_address)
        assert isinstance(result, list)
        assert all(isinstance(p, Position) for p in result)

    @pytest.mark.asyncio
    async def test_get_positions_bad_wallet_raises(self, data_client):
        with pytest.raises(StatusCodeError):
            await data_client.get_positions("0xdeadbeef")

    @pytest.mark.asyncio
    async def test_get_closed_positions_returns_list(self, data_client, test_address):
        result = await data_client.get_closed_positions(test_address)
        assert isinstance(result, list)
        assert all(isinstance(p, ClosedPosition) for p in result)

    @pytest.mark.asyncio
    async def test_get_closed_positions_bad_wallet_raises(self, data_client):
        with pytest.raises(StatusCodeError):
            await data_client.get_closed_positions("0xdeadbeef")

    @pytest.mark.asyncio
    async def test_get_leaderboard_returns_list(self, data_client):
        result = await data_client.get_leaderboard()
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], LeaderboardEntry)

    @pytest.mark.asyncio
    async def test_get_trades_returns_list(self, data_client, test_address):
        result = await data_client.get_trades(test_address, limit=5)
        assert isinstance(result, list)
        assert len(result) <= 5
        assert all(isinstance(t, Trade) for t in result)

    @pytest.mark.asyncio
    async def test_get_activity_returns_list(self, data_client, test_address):
        result = await data_client.get_activity(test_address, limit=5)
        assert isinstance(result, list)
        assert all(isinstance(a, Activity) for a in result)

    @pytest.mark.asyncio
    async def test_get_activity_bad_wallet_raises(self, data_client):
        with pytest.raises(StatusCodeError):
            await data_client.get_activity("0xdeadbeef")

    @pytest.mark.asyncio
    async def test_get_accounting_snapshot_returns_bytes(
        self, data_client, test_address
    ):
        result = await data_client.get_accounting_snapshot(test_address)
        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_get_accounting_snapshot_bad_wallet_raises(self, data_client):
        with pytest.raises(StatusCodeError):
            await data_client.get_accounting_snapshot("0xdeadbeef")

    @pytest.mark.asyncio
    async def test_get_positions_paginated_returns_list(
        self, data_client, test_address
    ):
        result = await data_client.get_positions_paginated(test_address)
        assert isinstance(result, list)
        assert all(isinstance(p, Position) for p in result)
