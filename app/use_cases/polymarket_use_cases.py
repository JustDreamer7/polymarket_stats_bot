import csv
from datetime import UTC, datetime
from io import StringIO

from app.clients.polymarket_data_client import PolymarketDataClient
from app.clients.polymarket_gamma_client import PolymarketGammaClient
from app.schemas.polymarket_data import (
    BettorStats,
    EquitySnapshot,
    LeaderboardEntry,
    Trade,
)
from app.schemas.polymarket_gamma import PublicProfile
from app.utils.extract_zip import extract_zip_member


class PolymarketUseCases:
    def __init__(
        self,
    ):
        self.data_client = PolymarketDataClient()
        self.gamma_client = PolymarketGammaClient()

    async def get_leaderboard(self, **kwargs) -> list[LeaderboardEntry]:
        return await self.data_client.get_leaderboard(**kwargs)

    async def search_user_by_wallet(self, proxy_wallet: str) -> PublicProfile | None:
        return await self.gamma_client.get_public_profile(proxy_wallet)

    async def search_user_by_username(self, username: str) -> PublicProfile | None:
        entries = await self.data_client.get_leaderboard(userName=username)
        if not entries:
            return None
        if len(entries) != 1:
            raise ValueError("More than 1 user founded") from None
        return await self.gamma_client.get_public_profile(entries[0].proxy_wallet)

    async def search_user(self, query: str) -> PublicProfile | None:
        if query.startswith("0x"):
            return await self.search_user_by_wallet(query)
        return await self.search_user_by_username(query)

    async def get_last_trade_day(self, proxy_wallet: str) -> datetime | None:
        trades = await self.data_client.get_trades(proxy_wallet, limit=1)
        if trades:
            return datetime.fromtimestamp(trades[-1].timestamp, tz=UTC)
        return None

    async def get_last_trades(self, proxy_wallet: str, limit: int = 10) -> list[Trade]:
        return await self.data_client.get_trades(proxy_wallet, limit=limit)

    # TODO: add cache?
    async def get_closed_position_bettor_stats(self, proxy_wallet: str) -> BettorStats:
        positions = await self.data_client.get_closed_positions_paginated(proxy_wallet)
        return await self._count_stats(positions)

    async def get_cur_position_bettor_stats(self, proxy_wallet: str) -> BettorStats:
        positions = await self.data_client.get_positions_paginated(proxy_wallet)
        return await self._count_stats(positions)

    async def get_user_equity(self, proxy_wallet) -> EquitySnapshot:
        resp_archive = await self.data_client.get_accounting_snapshot(proxy_wallet)
        csv_text = extract_zip_member(resp_archive, "equity.csv")
        reader = csv.DictReader(StringIO(csv_text))
        return [EquitySnapshot.from_dict(row) for row in reader][-1]

    @staticmethod
    async def _count_stats(positions) -> BettorStats:
        trades = len(positions)
        volume = sum(p.avg_price * p.total_bought for p in positions)
        winnings = sum(p.realized_pnl for p in positions)
        wins = sum(1 for p in positions if p.realized_pnl > 0)

        winrate = (wins / trades * 100) if trades else 0.0
        roi = (winnings / volume * 100) if volume else 0.0

        return BettorStats(
            winrate=round(winrate, 2),
            trades=trades,
            winnings=round(winnings, 2),
            volume=round(volume, 2),
            roi=round(roi, 2),
        )
