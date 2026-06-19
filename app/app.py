from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application, ApplicationBuilder

from app.config import get_settings
from app.common.database import Database
from app.common.logger import logger
from app.tasks.bettor_stats_task import BettorStatsUpdater
from app.tasks.trades_task import TradesNotifier
from app.tg_bot.bot import COMMANDS, TelegramBot


async def init_db(app: Application) -> Database:
    config = app.bot_data["config"]
    db = Database(config["database"])
    app.bot_data["db"] = db
    return db


def init_scheduler(app: Application) -> AsyncIOScheduler:
    config = app.bot_data["config"]

    scheduler = AsyncIOScheduler()

    notifier = TradesNotifier(app)

    scheduler.add_job(
        notifier.run,
        "interval",
        minutes=config["notify_interval_minutes"],
        id="notify_trades",
        name="Notify subscribers about recent bettor trades",
        max_instances=1,
        replace_existing=False,
    )

    stats_updater = BettorStatsUpdater(app)

    scheduler.add_job(
        stats_updater.run,
        "interval",
        minutes=config["stats_interval_minutes"],
        id="update_bettor_stats",
        name="Update bettor stats",
        max_instances=1,
        replace_existing=False,
    )

    scheduler.start()
    return scheduler


async def post_init(app: Application) -> None:
    config = get_settings()
    app.bot_data["config"] = config

    await app.bot.set_my_commands(COMMANDS)

    await init_db(app)

    TelegramBot(app)

    app.bot_data["scheduler"] = init_scheduler(app)

    logger.info("Application initialized")


async def post_shutdown(app: Application) -> None:
    scheduler: AsyncIOScheduler = app.bot_data.get("scheduler")
    if scheduler is not None:
        scheduler.shutdown(wait=False)

    db: Database | None = app.bot_data.get("db")
    if db is not None:
        await db.dispose_engine()

    logger.info("Application stopped")


def create_app() -> Application:
    config = get_settings()
    app = (
        ApplicationBuilder()
        .token(config["telegram_token"])
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    return app
