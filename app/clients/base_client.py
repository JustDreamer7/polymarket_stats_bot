import asyncio
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import cast

from zapros import AsyncClient, AsyncStdNetworkHandler, RetryMiddleware


class BaseClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[AsyncClient, None]:
        async with AsyncClient(
            base_url=self.base_url,
            handler=RetryMiddleware(
                AsyncStdNetworkHandler(connect_timeout=5.0, total_timeout=60.0),
                max_attempts=3,
            ),
        ) as client:
            yield client

    async def _paginate(
        self, fetch_page: Callable, limit: int, max_offset: int | None = None
    ) -> list:
        BATCH_SIZE = 10
        results: list = []
        current_offset = 0
        while True:
            batch_offsets = [current_offset + i * limit for i in range(BATCH_SIZE)]
            pages = await asyncio.gather(
                *[fetch_page(limit=limit, offset=off) for off in batch_offsets],
                return_exceptions=True,
            )
            done = False
            for page in pages:
                if isinstance(page, Exception):
                    raise page  # TODO: add handling exception
                page = cast(list, page)
                results.extend(page)
                if len(page) < limit:
                    done = True
                    break
            if done:
                break
            current_offset += BATCH_SIZE * limit
            if max_offset is not None and max_offset <= current_offset:
                break
        return results

    @staticmethod
    def stringify_params(params: dict) -> dict[str, str]:
        return {key: str(value) for key, value in params.items() if value is not None}
