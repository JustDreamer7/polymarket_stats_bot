import asyncio
from datetime import UTC, datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from app.common.database import Database
from app.common.logger import logger
from app.use_cases.bettor_use_cases import BettorUseCases
from app.use_cases.polymarket_use_cases import PolymarketUseCases
from app.use_cases.subscription_use_cases import SubscriptionUseCases
from app.use_cases.user_use_cases import UserUseCases

COMMANDS = [
    ("start", "Регистрация в системе"),
    ("help", "Показать справку"),
    ("search", "Статистика игрока"),
    ("show_trades", "Последние ставки игрока"),
    ("add", "Подписаться на игрока"),
    ("remove", "Отписаться от игрока"),
    ("list", "Список подписок"),
]


# pylint: disable=broad-exception-caught
class TelegramBot:
    LIST_PAGE_SIZE = 5

    def __init__(self, app: Application) -> None:
        db: Database = app.bot_data["db"]
        self.polymarket_use_cases = PolymarketUseCases()
        self.bettor_use_cases = BettorUseCases(db)
        self.user_use_cases = UserUseCases(db)
        self.subscription_use_cases = SubscriptionUseCases(db)

        self._register_handlers(app)

    def _register_handlers(self, app: Application) -> None:
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("search", self.search_command))
        app.add_handler(CommandHandler("show_trades", self.show_trades_command))
        app.add_handler(CommandHandler("add", self.add_command))
        app.add_handler(CommandHandler("remove", self.remove_command))
        app.add_handler(CommandHandler("list", self.list_command))
        # callback for buttons which callback_data started with "list:"
        app.add_handler(CallbackQueryHandler(self.list_callback, pattern=r"^list:"))

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        tg_user = update.effective_user
        await self.user_use_cases.get_or_create(tg_user)

        await update.message.reply_text(
            "👋 Добро пожаловать в Polymarket Betting Follow Bot!\n\n"
            "Используйте /help чтобы увидеть доступные команды."
        )

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await update.message.reply_text(
            "📚 Доступные команды:\n\n"
            "/start - Регистрация в системе\n"
            "/help - Показать это сообщение\n"
            "/search <кошелёк|юзернейм> - Показать статистику игрока\n"
            "/show_trades <кошелёк|юзернейм> - Показать 10 последних ставок игрока\n"
            "/add <кошелёк|юзернейм> - Подписаться на игрока\n"
            "/remove <кошелёк|юзернейм> - Отписаться от игрока\n"
            "/list - Показать ваши подписки\n\n"
            "Возможности:\n"
            "• Отслеживать игроков с высоким винрейтом\n"
            "• Получать уведомления о новых ставках в реальном времени\n"
            "• Просматривать детальную статистику и результаты"
        )

    async def search_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not context.args:
            await update.message.reply_text(
                "Использование: /search <кошелёк|юзернейм>\n\n"
                "👛 кошелёк — адрес 0x...\n"
                "🆔 юзернейм — имя пользователя Polymarket"
            )
            return

        query = " ".join(context.args)
        await update.message.reply_text(f"🔍 Поиск статистики игрока для {query}...")

        try:
            profile = await self.polymarket_use_cases.search_user(query)
            if not profile:
                await update.message.reply_text(
                    f"🚫 Игрок '{query}' не найден.\n"
                    "Укажите адрес кошелька (0x...) или имя пользователя."
                )
                return

            bettor = await self.bettor_use_cases.get_or_create(profile)

            async with asyncio.TaskGroup() as tg:
                closed_stats_task = tg.create_task(
                    self.polymarket_use_cases.get_closed_position_bettor_stats(
                        profile.proxy_wallet
                    )
                )
                cur_stats_task = tg.create_task(
                    self.polymarket_use_cases.get_cur_position_bettor_stats(
                        profile.proxy_wallet
                    )
                )
                last_trade_day_task = tg.create_task(
                    self.polymarket_use_cases.get_last_trade_day(profile.proxy_wallet)
                )

            stats = closed_stats_task.result()
            cur_stats = cur_stats_task.result()
            last_trade_day = last_trade_day_task.result()

            if last_trade_day:
                last_trade_resp = f"🕒 Время последней ставки: {last_trade_day.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            else:
                last_trade_resp = "🚫 Пользователь ранее не совершал ставок"

            # TODO: add balance
            response = (
                f'📊 Статистика <a href="https://polymarket.com/profile/{profile.proxy_wallet}">'
                f"{bettor.name}</a>:\n\n"
            )
            response += f"{last_trade_resp}\n\n"
            response += "🔒 Закрытые позиции:\n"
            response += f"🎯 Винрейт: {stats.winrate}%\n"
            response += f"🎲 Число ставок: {stats.trades}\n"
            response += f"💰 Выигрыш: ${stats.winnings:,.2f}\n"
            response += f"📦 Объём: ${stats.volume:,.2f}\n"
            response += f"💹 Процент выигрыша от вложенных средств: {stats.roi}%\n"
            response += "\n📊 Текущие позиции:\n"
            response += f"🎲 Число позиций: {cur_stats.trades}\n"
            response += f"📦 Объём: ${cur_stats.volume:,.2f}\n"

            await update.message.reply_text(response, parse_mode="HTML")

        except Exception as err:
            logger.error(f"Error fetching bettor stats: {err}")
            await update.message.reply_text(
                "Ошибка при загрузке статистики. Попробуйте снова."
            )

    async def show_trades_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not context.args:
            await update.message.reply_text(
                "Использование: /show_trades <кошелёк|юзернейм>"
            )
            return

        query = " ".join(context.args)
        await update.message.reply_text(
            f"📈 Загрузка последних ставок игрока {query}..."
        )

        try:
            profile = await self.polymarket_use_cases.search_user(query)
            if not profile:
                await update.message.reply_text(
                    f"🚫 Игрок '{query}' не найден.\n"
                    "Укажите адрес кошелька (0x...) или имя пользователя."
                )
                return

            bettor = await self.bettor_use_cases.get_or_create(profile)
            trades = await self.polymarket_use_cases.get_last_trades(
                profile.proxy_wallet
            )

            if not trades:
                await update.message.reply_text(
                    f"🚫 У игрока {bettor.name} нет ставок."
                )
                return

            response = (
                f'📈 Последние ставки <a href="https://polymarket.com/profile/{profile.proxy_wallet}">'
                f"{bettor.name}</a>:\n\n"
            )
            for trade in trades:
                trade_time = datetime.fromtimestamp(trade.timestamp, tz=UTC).strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                )
                side = "Покупка" if trade.side.lower() == "buy" else "Продажа"
                response += (
                    f"📊 {trade.title}\n"
                    f'<a href="https://polymarket.com/event/{trade.event_slug}">Открыть рынок</a>\n\n'
                    f"🎯 Исход: <b>{trade.outcome}</b>\n"
                    f"🔁 <b>{side}</b>\n"
                    f"💰 Размер: {trade.size:.2f}\n"
                    f"💵 Цена: {trade.price:.2f}\n"
                    f"🕒 Время: {trade_time}\n"
                    f"{'─' * 24}\n\n"
                )

            await update.message.reply_text(response, parse_mode="HTML")

        except Exception as err:
            logger.error(f"Error fetching bettor trades: {err}")
            await update.message.reply_text(
                "Ошибка при загрузке ставок. Попробуйте снова."
            )

    async def add_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not context.args:
            await update.message.reply_text("Использование: /add <кошелёк|юзернейм>")
            return

        query = " ".join(context.args)

        await update.message.reply_text(f"🔎 Добавление подписки на {query}...")

        try:
            profile = await self.polymarket_use_cases.search_user(query)
            if not profile:
                await update.message.reply_text(
                    f"🚫 Игрок '{query}' не найден.\n"
                    "Укажите адрес кошелька (0x...) или имя пользователя."
                )
                return

            user = await self.user_use_cases.get_or_create(update.effective_user)
            bettor = await self.bettor_use_cases.get_or_create(profile)

            # TODO: hueta c use_cases
            added = await self.subscription_use_cases.add_subscription(
                user.uid, bettor.proxy_wallet
            )
            if not added:
                await update.message.reply_text(f"Вы уже подписаны на {bettor.name}")
                return

            await update.message.reply_text(
                f"✅ Успешно подписались на {bettor.name}!\n"
                "Вы будете получать уведомления о новых ставках."
            )

        except Exception as e:
            logger.error(f"Error adding subscription: {e}")
            await update.message.reply_text(
                "Ошибка при добавлении подписки. Попробуйте снова."
            )

    async def remove_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not context.args:
            await update.message.reply_text("Использование: /remove <кошелёк|юзернейм>")
            return

        query = " ".join(context.args)

        await update.message.reply_text(f"🗑 Удаление {query} из подписок...")

        try:
            bettor = await self.bettor_use_cases.search_bettor(query)
            if not bettor:
                await update.message.reply_text(
                    f"🚫 Подписка на игрока '{query}' не найдена.\n"
                    "Укажите адрес кошелька (0x...) или имя пользователя."
                )
                return

            user = await self.user_use_cases.get_or_create(update.effective_user)

            removed = await self.subscription_use_cases.remove_subscription(
                user.uid, bettor.proxy_wallet
            )
            if not removed:
                await update.message.reply_text(
                    f"🚫 Подписка на игрока '{query}' не найдена.\n"
                    "Укажите адрес кошелька (0x...) или имя пользователя."
                )
                return

            await update.message.reply_text(
                f"✅ {bettor.name} удалён из ваших подписок"
            )

        except Exception as e:
            logger.error(f"Error removing subscription: {e}")
            await update.message.reply_text(
                "Ошибка при удалении подписки. Попробуйте снова."
            )

    async def list_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user = await self.user_use_cases.get_or_create(update.effective_user)

        bettors, total = await self.bettor_use_cases.get_subscription_page(
            user.uid, offset=0, limit=self.LIST_PAGE_SIZE
        )

        if not bettors:
            await update.message.reply_text(
                "У вас пока нет подписок.\n"
                "Используйте /add <кошелёк|юзернейм> чтобы начать отслеживать игроков!"
            )
            return

        await update.message.reply_text(
            self._render_list_page(bettors, offset=0, total=total),
            parse_mode="HTML",
            reply_markup=self._list_keyboard(offset=0, total=total),
        )

    async def list_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        await query.answer()

        try:
            offset = int(query.data.split(":")[1])
        except (IndexError, ValueError):
            return

        user = await self.user_use_cases.get_or_create(query.from_user)
        # TODO: somehow remove total or cache it
        bettors, total = await self.bettor_use_cases.get_subscription_page(
            user.uid, offset=offset, limit=self.LIST_PAGE_SIZE
        )

        await query.edit_message_text(
            self._render_list_page(bettors, offset=offset, total=total),
            parse_mode="HTML",
            reply_markup=self._list_keyboard(offset=offset, total=total),
        )

    def _render_list_page(self, bettors: list, offset: int, total: int) -> str:
        page = offset // self.LIST_PAGE_SIZE + 1
        total_pages = max(1, (total + self.LIST_PAGE_SIZE - 1) // self.LIST_PAGE_SIZE)
        response = f"📋 Ваши подписки ({total}), стр. {page}/{total_pages}:\n\n"

        for bettor in bettors:
            response += (
                f'👤 <a href="https://polymarket.com/profile/{bettor.proxy_wallet}">'
                f"@{bettor.name}</a>\n"
            )

            stats = bettor.stats
            if stats is not None:
                if stats.last_trade_date:
                    last_trade_resp = (
                        "🕒 Время последней ставки: "
                        f"{stats.last_trade_date.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    )
                else:
                    last_trade_resp = "🚫 Пользователь ранее не совершал ставок"

                response += f"{last_trade_resp}\n\n"
                response += "🔒 Закрытые позиции:\n"
                response += f"🎯 Винрейт: {stats.winrate}%\n"
                response += f"🎲 Число ставок: {stats.closed_trades_count}\n"
                response += f"💰 Выигрыш: ${stats.winnings:,.2f}\n"
                response += f"📦 Объём: ${stats.closed_trades_volume:,.2f}\n"
                response += f"💹 Процент выигрыша от вложенных средств: {stats.roi}%\n"
                response += "\n📊 Текущие позиции:\n"
                response += f"🎲 Число позиций: {stats.current_trades_count}\n"
                response += f"📦 Объём: ${stats.current_trades_volume:,.2f}\n"

            response += f"{'─' * 24}\n\n"

        return response

    def _list_keyboard(self, offset: int, total: int) -> InlineKeyboardMarkup | None:
        buttons: list[InlineKeyboardButton] = []
        if offset > 0:
            prev_offset = max(0, offset - self.LIST_PAGE_SIZE)
            buttons.append(
                InlineKeyboardButton("◀️ Назад", callback_data=f"list:{prev_offset}")
            )
        if offset + self.LIST_PAGE_SIZE < total:
            buttons.append(
                InlineKeyboardButton(
                    "Вперёд ▶️", callback_data=f"list:{offset + self.LIST_PAGE_SIZE}"
                )
            )
        if not buttons:
            return None
        return InlineKeyboardMarkup([buttons])
