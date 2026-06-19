# pylint: disable=protected-access
from typing import Literal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.polymarket_data import BettorStats, Trade
from app.schemas.polymarket_gamma import PublicProfile
from app.tg_bot.bot import TelegramBot

# TODO: rewrite tg bot tests


def _make_application() -> MagicMock:
    application = MagicMock()
    application.add_handler = MagicMock()
    application.bot_data = {"db": MagicMock()}
    return application


def _build_bot(**use_case_overrides) -> TelegramBot:
    bot = TelegramBot(_make_application())
    for name, uc in use_case_overrides.items():
        setattr(bot, name, uc)
    return bot


def _mock_profile(wallet: str = "0x" + "1" * 40, name: str = "alice") -> PublicProfile:
    return PublicProfile(proxy_wallet=wallet, name=name, verified_badge=False)


def _mock_bettor(name: str = "alice", wallet: str = "0x" + "1" * 40) -> MagicMock:
    bettor = MagicMock()
    bettor.name = name
    bettor.proxy_wallet = wallet
    return bettor


def _mock_trade(side: Literal["BUY", "SELL"] = "BUY") -> Trade:
    return Trade(
        proxy_wallet="0x" + "1" * 40,
        side=side,
        size=10.0,
        price=0.5,
        timestamp=1700000000,
        title="Some market",
        slug="slug",
        event_slug="event-slug",
        outcome="Yes",
        outcome_index=0,
        name="Yes",
    )


def _make_update(args=None) -> MagicMock:
    update = MagicMock()
    update.effective_user.id = 123456
    update.effective_user.username = "test_user"
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def make_update():
    return _make_update


def _make_context(args=None) -> MagicMock:
    context = MagicMock()
    context.args = args if args is not None else []
    return context


@pytest.fixture
def make_context():
    return _make_context


def _reply_text(update) -> str:
    return update.message.reply_text.call_args[0][0]


class TestBotCommands:
    @pytest.mark.asyncio
    async def test_start_command_welcomes(self, make_update, make_context):
        update = make_update()
        bot = _build_bot(user_use_cases=MagicMock(get_or_create=AsyncMock()))
        await bot.start_command(update, make_context())
        assert "Добро пожаловать" in _reply_text(update)

    @pytest.mark.asyncio
    async def test_help_command(self, make_update, make_context):
        update = make_update()
        bot = _build_bot()
        await bot.help_command(update, make_context())
        assert "Доступные команды" in _reply_text(update)

    @pytest.mark.asyncio
    async def test_search_command_no_args(self, make_update, make_context):
        update = make_update()
        bot = _build_bot()
        await bot.search_command(update, make_context([]))
        assert "Использование" in _reply_text(update)

    @pytest.mark.asyncio
    async def test_search_command_user_not_found(self, make_update, make_context):
        update = make_update()
        polymarket_use_cases = MagicMock()
        polymarket_use_cases.search_user = AsyncMock(return_value=None)
        bot = _build_bot(polymarket_use_cases=polymarket_use_cases)
        await bot.search_command(update, make_context(["0xabc"]))
        assert "не найден" in _reply_text(update)

    @pytest.mark.asyncio
    async def test_search_command_renders_stats(self, make_update, make_context):
        update = make_update()
        profile = _mock_profile(name="alice")
        bettor = _mock_bettor(name="alice")

        polymarket_use_cases = MagicMock()
        polymarket_use_cases.search_user = AsyncMock(return_value=profile)
        polymarket_use_cases.get_closed_position_bettor_stats = AsyncMock(
            return_value=BettorStats(75.0, 4, 100.0, 200.0, 50.0)
        )
        polymarket_use_cases.get_cur_position_bettor_stats = AsyncMock(
            return_value=BettorStats(0.0, 2, 0.0, 50.0, 0.0)
        )
        polymarket_use_cases.get_last_trade_day = AsyncMock(return_value=None)

        bettor_use_cases = MagicMock()
        bettor_use_cases.get_or_create = AsyncMock(return_value=bettor)

        bot = _build_bot(
            polymarket_use_cases=polymarket_use_cases,
            bettor_use_cases=bettor_use_cases,
        )
        await bot.search_command(update, make_context(["alice"]))

        text = _reply_text(update)
        assert "Статистика" in text
        assert "alice" in text

    @pytest.mark.asyncio
    async def test_search_command_handles_error(self, make_update, make_context):
        update = make_update()
        polymarket_use_cases = MagicMock()
        polymarket_use_cases.search_user = AsyncMock(side_effect=RuntimeError("boom"))
        bot = _build_bot(polymarket_use_cases=polymarket_use_cases)
        await bot.search_command(update, make_context(["alice"]))
        assert "Ошибка" in _reply_text(update)

    @pytest.mark.asyncio
    async def test_show_trades_command_no_args(self, make_update, make_context):
        update = make_update()
        bot = _build_bot()
        await bot.show_trades_command(update, make_context([]))
        assert "Использование" in _reply_text(update)

    @pytest.mark.asyncio
    async def test_show_trades_command_not_found(self, make_update, make_context):
        update = make_update()
        polymarket_use_cases = MagicMock()
        polymarket_use_cases.search_user = AsyncMock(return_value=None)
        bot = _build_bot(polymarket_use_cases=polymarket_use_cases)
        await bot.show_trades_command(update, make_context(["nobody"]))
        assert "не найден" in _reply_text(update)

    @pytest.mark.asyncio
    async def test_show_trades_command_no_trades(self, make_update, make_context):
        update = make_update()
        profile = _mock_profile()
        bettor = _mock_bettor(name="alice")
        polymarket_use_cases = MagicMock()
        polymarket_use_cases.search_user = AsyncMock(return_value=profile)
        polymarket_use_cases.get_last_trades = AsyncMock(return_value=[])
        bettor_use_cases = MagicMock()
        bettor_use_cases.get_or_create = AsyncMock(return_value=bettor)
        bot = _build_bot(
            polymarket_use_cases=polymarket_use_cases,
            bettor_use_cases=bettor_use_cases,
        )
        await bot.show_trades_command(update, make_context(["alice"]))
        assert "нет ставок" in _reply_text(update)

    @pytest.mark.asyncio
    async def test_show_trades_command_renders_trades(self, make_update, make_context):
        update = make_update()
        profile = _mock_profile()
        bettor = _mock_bettor(name="alice")
        polymarket_use_cases = MagicMock()
        polymarket_use_cases.search_user = AsyncMock(return_value=profile)
        polymarket_use_cases.get_last_trades = AsyncMock(
            return_value=[_mock_trade("BUY"), _mock_trade("SELL")]
        )
        bettor_use_cases = MagicMock()
        bettor_use_cases.get_or_create = AsyncMock(return_value=bettor)
        bot = _build_bot(
            polymarket_use_cases=polymarket_use_cases,
            bettor_use_cases=bettor_use_cases,
        )
        await bot.show_trades_command(update, make_context(["alice"]))
        text = _reply_text(update)
        assert "Покупка" in text
        assert "Продажа" in text

    @pytest.mark.asyncio
    async def test_add_command_no_args(self, make_update, make_context):
        update = make_update()
        bot = _build_bot()
        await bot.add_command(update, make_context([]))
        assert "Использование" in _reply_text(update)

    @pytest.mark.asyncio
    async def test_add_command_user_not_found(self, make_update, make_context):
        update = make_update()
        polymarket_use_cases = MagicMock()
        polymarket_use_cases.search_user = AsyncMock(return_value=None)
        bot = _build_bot(polymarket_use_cases=polymarket_use_cases)
        await bot.add_command(update, make_context(["nobody"]))
        assert "не найден" in _reply_text(update)

    @pytest.mark.asyncio
    async def test_add_command_success(self, make_update, make_context):
        update = make_update()
        profile = _mock_profile()
        bettor = _mock_bettor(name="alice")
        mock_user = MagicMock()
        mock_user.uid = "user-uid"

        polymarket_use_cases = MagicMock()
        polymarket_use_cases.search_user = AsyncMock(return_value=profile)
        bettor_use_cases = MagicMock()
        bettor_use_cases.get_or_create = AsyncMock(return_value=bettor)
        user_use_cases = MagicMock()
        user_use_cases.get_or_create = AsyncMock(return_value=mock_user)
        subscription_use_cases = MagicMock()
        subscription_use_cases.add_subscription = AsyncMock(return_value=True)

        bot = _build_bot(
            polymarket_use_cases=polymarket_use_cases,
            bettor_use_cases=bettor_use_cases,
            user_use_cases=user_use_cases,
            subscription_use_cases=subscription_use_cases,
        )
        await bot.add_command(update, make_context(["alice"]))
        assert "Успешно подписались" in _reply_text(update)
        subscription_use_cases.add_subscription.assert_called_once_with(
            "user-uid", bettor.proxy_wallet
        )

    @pytest.mark.asyncio
    async def test_add_command_already_subscribed(self, make_update, make_context):
        update = make_update()
        profile = _mock_profile()
        bettor = _mock_bettor(name="alice")
        mock_user = MagicMock()
        mock_user.uid = "user-uid"

        bot = _build_bot(
            polymarket_use_cases=MagicMock(search_user=AsyncMock(return_value=profile)),
            bettor_use_cases=MagicMock(get_or_create=AsyncMock(return_value=bettor)),
            user_use_cases=MagicMock(get_or_create=AsyncMock(return_value=mock_user)),
            subscription_use_cases=MagicMock(
                add_subscription=AsyncMock(return_value=False)
            ),
        )
        await bot.add_command(update, make_context(["alice"]))
        assert "уже подписаны" in _reply_text(update)

    @pytest.mark.asyncio
    async def test_remove_command_no_args(self, make_update, make_context):
        update = make_update()
        bot = _build_bot()
        await bot.remove_command(update, make_context([]))
        assert "Использование" in _reply_text(update)

    @pytest.mark.asyncio
    async def test_remove_command_bettor_not_found(self, make_update, make_context):
        update = make_update()
        bettor_use_cases = MagicMock()
        bettor_use_cases.search_bettor = AsyncMock(return_value=None)
        bot = _build_bot(bettor_use_cases=bettor_use_cases)
        await bot.remove_command(update, make_context(["nobody"]))
        assert "не найдена" in _reply_text(update)

    @pytest.mark.asyncio
    async def test_remove_command_subscription_not_found(
        self, make_update, make_context
    ):
        update = make_update()
        bettor = _mock_bettor(name="alice")
        mock_user = MagicMock()
        mock_user.uid = "user-uid"
        bot = _build_bot(
            bettor_use_cases=MagicMock(search_bettor=AsyncMock(return_value=bettor)),
            user_use_cases=MagicMock(get_or_create=AsyncMock(return_value=mock_user)),
            subscription_use_cases=MagicMock(
                remove_subscription=AsyncMock(return_value=False)
            ),
        )
        await bot.remove_command(update, make_context(["alice"]))
        assert "не найдена" in _reply_text(update)

    @pytest.mark.asyncio
    async def test_remove_command_success(self, make_update, make_context):
        update = make_update()
        bettor = _mock_bettor(name="alice")
        mock_user = MagicMock()
        mock_user.uid = "user-uid"
        bot = _build_bot(
            bettor_use_cases=MagicMock(search_bettor=AsyncMock(return_value=bettor)),
            user_use_cases=MagicMock(get_or_create=AsyncMock(return_value=mock_user)),
            subscription_use_cases=MagicMock(
                remove_subscription=AsyncMock(return_value=True)
            ),
        )
        await bot.remove_command(update, make_context(["alice"]))
        assert "удалён" in _reply_text(update)

    @pytest.mark.asyncio
    async def test_list_command_no_subscriptions(self, make_update, make_context):
        update = make_update()
        mock_user = MagicMock()
        mock_user.uid = "user-uid"
        bot = _build_bot(
            user_use_cases=MagicMock(get_or_create=AsyncMock(return_value=mock_user)),
            bettor_use_cases=MagicMock(
                get_subscription_page=AsyncMock(return_value=([], 0))
            ),
        )
        await bot.list_command(update, make_context())
        assert "нет подписок" in _reply_text(update).lower()

    @pytest.mark.asyncio
    async def test_list_command_with_subscriptions(self, make_update, make_context):
        update = make_update()
        mock_user = MagicMock()
        mock_user.uid = "user-uid"
        bettor = MagicMock()
        bettor.name = "alice"
        bettor.proxy_wallet = "0x" + "1" * 40
        bettor.stats = None
        bot = _build_bot(
            user_use_cases=MagicMock(get_or_create=AsyncMock(return_value=mock_user)),
            bettor_use_cases=MagicMock(
                get_subscription_page=AsyncMock(return_value=([bettor], 1))
            ),
        )
        await bot.list_command(update, make_context())
        text = _reply_text(update)
        assert "alice" in text
        assert "Ваши подписки" in text

    @pytest.mark.asyncio
    async def test_list_callback_renders_page(self):
        query = AsyncMock()
        query.data = "list:5"
        query.from_user.id = 123456
        update = MagicMock()
        update.callback_query = query

        mock_user = MagicMock()
        mock_user.uid = "user-uid"
        bettor = MagicMock()
        bettor.name = "alice"
        bettor.proxy_wallet = "0x" + "1" * 40
        bettor.stats = None

        bot = _build_bot(
            user_use_cases=MagicMock(get_or_create=AsyncMock(return_value=mock_user)),
            bettor_use_cases=MagicMock(
                get_subscription_page=AsyncMock(return_value=([bettor], 6))
            ),
        )
        await bot.list_callback(update, MagicMock())

        query.edit_message_text.assert_called_once()
        rendered = query.edit_message_text.call_args[0][0]
        assert "alice" in rendered

    @pytest.mark.asyncio
    async def test_list_callback_invalid_offset_ignored(self):
        query = AsyncMock()
        query.data = "list:abc"
        query.from_user.id = 123456
        update = MagicMock()
        update.callback_query = query

        bot = _build_bot(
            user_use_cases=MagicMock(get_or_create=AsyncMock()),
        )
        await bot.list_callback(update, MagicMock())
        query.edit_message_text.assert_not_called()

    def test_registers_all_command_handlers(self):
        application = _make_application()
        TelegramBot(application)

        command_handlers = {
            next(iter(call.args[0].commands))
            for call in application.add_handler.call_args_list
            if hasattr(call.args[0], "commands")
        }
        assert command_handlers == {
            "start",
            "help",
            "search",
            "show_trades",
            "add",
            "remove",
            "list",
        }

    def test_list_keyboard_first_page_has_next_only(self):
        bot = _build_bot()
        keyboard = bot._list_keyboard(offset=0, total=10)
        assert keyboard is not None
        buttons = keyboard.inline_keyboard[0]
        labels = [b.text for b in buttons]
        assert "Вперёд ▶️" in labels
        assert "◀️ Назад" not in labels

    def test_list_keyboard_middle_page_has_both(self):
        bot = _build_bot()
        keyboard = bot._list_keyboard(offset=5, total=15)
        labels = [b.text for b in keyboard.inline_keyboard[0]]
        assert "◀️ Назад" in labels
        assert "Вперёд ▶️" in labels

    def test_list_keyboard_single_page_no_buttons(self):
        bot = _build_bot()
        assert bot._list_keyboard(offset=0, total=3) is None
