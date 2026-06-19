import asyncio

from telegram.ext import Application

from app.common.logger import logger
from app.repository.bettor_repository import BettorRepository
from app.schemas.polymarket_data import BettorStatsSnapshot
from app.use_cases.polymarket_use_cases import PolymarketUseCases


class BettorStatsUpdater:
    def __init__(self, app: Application):
        db = app.bot_data["db"]
        self.bettor_repo = BettorRepository(db)
        self.polymarket_use_cases = PolymarketUseCases()
        self._semaphore = asyncio.Semaphore(10)

    async def _collect_bettor_stats(self, proxy_wallet: str) -> BettorStatsSnapshot:
        async with self._semaphore:
            async with asyncio.TaskGroup() as tg:
                closed_stats_task = tg.create_task(
                    self.polymarket_use_cases.get_closed_position_bettor_stats(
                        proxy_wallet
                    )
                )
                cur_stats_task = tg.create_task(
                    self.polymarket_use_cases.get_cur_position_bettor_stats(
                        proxy_wallet
                    )
                )
                last_trade_task = tg.create_task(
                    self.polymarket_use_cases.get_last_trade_day(proxy_wallet)
                )

            closed_stats = closed_stats_task.result()
            cur_stats = cur_stats_task.result()
            last_trade_day = last_trade_task.result()

            return BettorStatsSnapshot(
                uid=proxy_wallet,
                last_trade_date=last_trade_day,
                closed_trades_count=closed_stats.trades,
                current_trades_count=cur_stats.trades,
                closed_trades_volume=closed_stats.volume,
                current_trades_volume=cur_stats.volume,
                winnings=round(closed_stats.winnings, 2),
                winrate=closed_stats.winrate,
                roi=closed_stats.roi,
            )

    async def run(self) -> None:
        logger.info("Starting bettor stats update job")

        bettors = await self.bettor_repo.get_all()

        result = await asyncio.gather(
            *[self._collect_bettor_stats(bettor.proxy_wallet) for bettor in bettors],
            return_exceptions=True,
        )
        to_upload = []
        for outcome, bettor in zip(result, bettors, strict=True):
            if isinstance(outcome, Exception):
                logger.error(
                    "Error processing bettor %s: %s", bettor.proxy_wallet, outcome
                )
            else:
                to_upload.append(outcome)
        uploaded = await self.bettor_repo.bulk_upsert_stats(stats=to_upload)

        logger.info("Bettor stats update job completed, %d stats uploaded", uploaded)
