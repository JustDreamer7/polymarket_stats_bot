import asyncio
from datetime import UTC, datetime, timedelta

from telegram import Bot
from telegram.error import TelegramError
from telegram.ext import Application

from app.clients.polymarket_data_client import PolymarketDataClient
from app.common.logger import logger
from app.models.user import User
from app.repository.bettor_repository import BettorRepository
from app.repository.subscription_repository import SubscriptionRepository
from app.schemas.polymarket_data import Trade


class TradesNotifier:
    def __init__(self, app: Application):
        db = app.bot_data["db"]
        self.bot: Bot = app.bot
        self.subscription_repo = SubscriptionRepository(db)
        self.bettor_repo = BettorRepository(db)
        self.polymarker_data_client = PolymarketDataClient()
        self.notify_interval_minutes = app.bot_data["config"]["notify_interval_minutes"]
        self.recent_trades_limit = app.bot_data["config"]["recent_trades_limit"]
        self._semaphore = asyncio.Semaphore(10)

    async def _fetch_recent_trades(self, bettor_id: str) -> list[Trade]:
        trades = await self.polymarker_data_client.get_trades(
            bettor_id, limit=self.recent_trades_limit
        )
        cutoff = datetime.now(tz=UTC) - timedelta(minutes=self.notify_interval_minutes)
        cutoff_ts = int(cutoff.timestamp())
        return [trade for trade in trades if trade.timestamp >= cutoff_ts]

    def _format_trade(self, bettor_name: str, trade: Trade) -> str:
        side = "Покупка" if trade.side.lower() == "buy" else "Продажа"
        trade_time = datetime.fromtimestamp(trade.timestamp, tz=UTC).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
        return (
            f"🔔 Новая ставка от <b>{bettor_name}</b>\n"
            f'<a href="https://polymarket.com/event/{trade.event_slug}">Открыть рынок</a>\n\n'
            f"📊 {trade.title}\n"
            f"🎯 Исход: <b>{trade.outcome}</b>\n"
            f"🔁 {side}\n"
            f"💰 Размер: {trade.size}\n"
            f"💵 Цена: {trade.price}\n"
            f"🕒 Время: {trade_time}\n"
            f"{'─' * 24}\n\n"
        )

    async def _notify_subscribers(
        self, bettor_name: str, subscribers: list[User], trades: list[Trade]
    ) -> None:
        for subscriber in subscribers:
            for trade in trades:
                text = self._format_trade(bettor_name, trade)
                try:
                    await self.bot.send_message(
                        chat_id=subscriber.user_tg_id,
                        text=text,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )
                except TelegramError as e:
                    logger.error(
                        "Failed to send message to user %s: %s",
                        subscriber.uid,
                        e,
                    )

    async def _notify_bettor_trades(self, bettor_id: str) -> None:
        async with self._semaphore:
            trades = await self._fetch_recent_trades(bettor_id)
            if not trades:
                return

            subscribers = await self.subscription_repo.get_subscribers_by_bettor(
                bettor_id
            )
            if not subscribers:
                return

            bettor = await self.bettor_repo.get_by_wallet(bettor_id)

            await self._notify_subscribers(bettor.name, subscribers, trades)
            logger.info(
                "Notified %s subscribers about %s new trades from %s, %s",
                len(subscribers),
                len(trades),
                bettor.proxy_wallet,
                bettor.name,
            )

    async def run(self) -> None:
        logger.info("Starting trades notification job")

        bettor_ids = await self.subscription_repo.get_distinct_bettor_ids()
        result = await asyncio.gather(
            *[self._notify_bettor_trades(bettor_id) for bettor_id in bettor_ids],
            return_exceptions=True,
        )
        for _, bettor_id in zip(result, bettor_ids, strict=True):
            if isinstance(_, Exception):
                logger.error("Error processing bettor %s: %s", bettor_id, _)

        logger.info("Trades notification job completed")
