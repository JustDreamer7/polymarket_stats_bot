import asyncio

import orjson
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from zapros import AsyncClient, AsyncStdNetworkHandler, RetryMiddleware

from app.common.logger import logger
from app.config import get_settings

TELEGRAM_API_BASE = "https://api.telegram.org"
HEALTHCHECK_TEXT = "/healthping"

# How long to wait for the bot webhook to consume the probe message.
PROBE_POLL_ATTEMPTS = 5
PROBE_POLL_INTERVAL = 1.0


async def send_probe(client: AsyncClient, token: str, chat_id: str) -> None:
    resp = await client.get(
        f"/bot{token}/sendMessage",
        params={"chat_id": chat_id, "text": HEALTHCHECK_TEXT},
    )
    resp.raise_for_status()
    payload = orjson.loads(resp.text)
    if not payload.get("ok"):
        raise RuntimeError(f"sendMessage failed: {payload}")


async def get_pending_update_count(client: AsyncClient, token: str) -> int:
    resp = await client.get(f"/bot{token}/getWebhookInfo")
    resp.raise_for_status()
    payload = orjson.loads(resp.text)
    if not payload.get("ok"):
        raise RuntimeError(f"getWebhookInfo failed: {payload}")
    return int(payload["result"]["pending_update_count"])


async def probe_webhook(token: str, chat_id: str) -> int:
    """Send a probe message and wait until the webhook drains pending updates.

    Returns the last observed pending_update_count.
    """
    async with AsyncClient(
        base_url=TELEGRAM_API_BASE,
        handler=RetryMiddleware(
            AsyncStdNetworkHandler(connect_timeout=5.0, total_timeout=20.0),
            max_attempts=3,
        ),
    ) as client:
        await send_probe(client, token, chat_id)

        pending = await get_pending_update_count(client, token)
        for _ in range(PROBE_POLL_ATTEMPTS):
            if pending == 0:
                break
            await asyncio.sleep(PROBE_POLL_INTERVAL)
            pending = await get_pending_update_count(client, token)
        return pending


def create_app() -> FastAPI:
    config = get_settings()
    app = FastAPI(title="Betting Bot Healthcheck")
    app.state.config = config

    @app.get("/health")
    async def health() -> JSONResponse:
        token: str = app.state.config["telegram_token"]
        chat_id: str | None = app.state.config["healthcheck_chat_id"]
        try:
            pending = await probe_webhook(token, chat_id)
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.error(f"healthcheck probe failed: {err}")
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "detail": str(err)},
            )

        if pending != 0:
            logger.error(f"healthcheck pending_update_count={pending}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "detail": f"pending_update_count={pending}",
                },
            )

        return JSONResponse(
            status_code=200, content={"status": "healthy", "pending_update_count": 0}
        )

    return app


app = create_app()
