# pylint: disable=protected-access
from datetime import datetime

import pytest

from app.schemas.polymarket_data import (
    BettorStats,
    EquitySnapshot,
    LeaderboardEntry,
    Trade,
)
from app.schemas.polymarket_gamma import PublicProfile
from app.use_cases.polymarket_use_cases import PolymarketUseCases


@pytest.fixture
def polymarket_use_cases():
    return PolymarketUseCases()


class TestPolymarketUseCases:
    @pytest.mark.asyncio
    async def test_get_leaderboard_returns_list(self, polymarket_use_cases):
        result = await polymarket_use_cases.get_leaderboard()
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], LeaderboardEntry)

    @pytest.mark.asyncio
    async def test_search_user_by_wallet_found(
        self, polymarket_use_cases, test_address
    ):
        result = await polymarket_use_cases.search_user_by_wallet(test_address)
        assert isinstance(result, PublicProfile)
        assert result.proxy_wallet == test_address

    @pytest.mark.asyncio
    async def test_search_user_by_username_found(self, polymarket_use_cases, test_name):
        result = await polymarket_use_cases.search_user_by_username(test_name)
        assert isinstance(result, PublicProfile)
        assert result.name == test_name

    @pytest.mark.asyncio
    async def test_search_user(self, polymarket_use_cases, test_address, test_name):
        result = await polymarket_use_cases.search_user(test_address)
        assert isinstance(result, PublicProfile)
        assert result.proxy_wallet == test_address

        result = await polymarket_use_cases.search_user(test_name)
        assert isinstance(result, PublicProfile)
        assert result.name == test_name

    @pytest.mark.asyncio
    async def test_search_user_by_username_not_found(self, polymarket_use_cases):
        result = await polymarket_use_cases.search_user_by_username(
            "zzz_definitely_nobody_zzz"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_last_trade_day_returns_datetime(
        self, polymarket_use_cases, test_address
    ):
        result = await polymarket_use_cases.get_last_trade_day(test_address)
        if result is not None:
            assert isinstance(result, datetime)

    @pytest.mark.asyncio
    async def test_get_last_trade_day_no_trades(self, polymarket_use_cases):
        result = await polymarket_use_cases.get_last_trade_day("0x" + "0" * 40)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_last_trades_returns_list(
        self, polymarket_use_cases, test_address
    ):
        result = await polymarket_use_cases.get_last_trades(test_address, limit=3)
        assert isinstance(result, list)
        assert len(result) <= 3
        assert all(isinstance(t, Trade) for t in result)

    @pytest.mark.asyncio
    async def test_get_closed_position_bettor_stats(
        self, polymarket_use_cases, test_address
    ):
        stats = await polymarket_use_cases.get_closed_position_bettor_stats(
            test_address
        )
        assert isinstance(stats, BettorStats)
        assert stats.trades >= 0

    @pytest.mark.asyncio
    async def test_get_cur_position_bettor_stats(
        self, polymarket_use_cases, test_address
    ):
        stats = await polymarket_use_cases.get_cur_position_bettor_stats(test_address)
        assert isinstance(stats, BettorStats)
        assert stats.trades >= 0

    @pytest.mark.asyncio
    async def test_get_user_equity(self, polymarket_use_cases, test_address):
        equity = await polymarket_use_cases.get_user_equity(test_address)
        assert isinstance(equity, EquitySnapshot)

    @pytest.mark.asyncio
    async def test_count_stats_empty(self):
        stats = await PolymarketUseCases._count_stats([])
        assert stats.trades == 0
        assert stats.winrate == 0.0
        assert stats.volume == 0.0
        assert stats.winnings == 0.0
        assert stats.roi == 0.0
