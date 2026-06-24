from functools import partial

import orjson
from zapros import StatusCodeError

from app.clients.base_client import BaseClient
from app.schemas.polymarket_data import (
    Activity,
    ClosedPosition,
    LeaderboardEntry,
    Position,
    Trade,
)


class PolymarketDataClient(BaseClient):
    def __init__(self):
        super().__init__("https://data-api.polymarket.com")

    async def get_positions(
        self, user_address: str, limit: int = 50, offset: int = 0, **kwargs
    ) -> list[Position]:
        async with self.get_client() as client:
            params = self.stringify_params(
                {"user": user_address, "limit": limit, "offset": offset, **kwargs}
            )
            response = await client.get("/positions", params=params)
            if 400 <= response.status < 600:
                raise StatusCodeError(
                    response=response, message=response.text
                ) from None
            return [Position.from_dict(item) for item in orjson.loads(response.text)]

    async def get_positions_paginated(
        self, user_address: str, **kwargs
    ) -> list[Position]:
        return await self._paginate(
            partial(self.get_positions, user_address, **kwargs),
            limit=50,
        )

    async def get_closed_positions(
        self,
        user_address: str,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "TIMESTAMP",
        **kwargs,
    ) -> list[ClosedPosition]:
        async with self.get_client() as client:
            params = self.stringify_params(
                {
                    "user": user_address,
                    "limit": limit,
                    "offset": offset,
                    "sortBy": sort_by,
                    **kwargs,
                }
            )
            response = await client.get("/closed-positions", params=params)
            if 400 <= response.status < 600:
                raise StatusCodeError(
                    response=response, message=response.text
                ) from None
            return [
                ClosedPosition.from_dict(item) for item in orjson.loads(response.text)
            ]

    async def get_closed_positions_paginated(
        self, user_address: str, max_offset: int = 10000, **kwargs
    ) -> list[ClosedPosition]:
        return await self._paginate(
            partial(self.get_closed_positions, user_address, **kwargs),
            limit=50,
            max_offset=max_offset,
        )

    async def get_leaderboard(self, **kwargs) -> list[LeaderboardEntry]:
        async with self.get_client() as client:
            response = await client.get(
                "/v1/leaderboard", params=self.stringify_params(kwargs)
            )
            if 400 <= response.status < 600:
                raise StatusCodeError(response=response, message=response.text)
            return [
                LeaderboardEntry.from_dict(item) for item in orjson.loads(response.text)
            ]

    async def get_trades(
        self, user_address: str, limit: int = 50, offset: int = 0, **kwargs
    ) -> list[Trade]:
        async with self.get_client() as client:
            params = self.stringify_params(
                {"user": user_address, "limit": limit, "offset": offset, **kwargs}
            )
            response = await client.get("/trades", params=params)
            if 400 <= response.status < 600:
                raise StatusCodeError(
                    response=response, message=response.text
                ) from None
            return [Trade.from_dict(item) for item in orjson.loads(response.text)]

    async def get_trades_paginated(self, user_address: str, **kwargs) -> list[Trade]:
        return await self._paginate(
            partial(self.get_trades, user_address, **kwargs),
            limit=50,
        )

    # TODO: add checking REFERRAL + OTHER OPS
    async def get_activity(
        self,
        user_address: str,
        *,
        limit: int = 50,
        offset: int = 0,
        sort_by: str | None = None,
        type: str | None = None,
        sort_direction: str | None = None,
        **kwargs,
    ) -> list[Activity]:
        async with self.get_client() as client:
            params = self.stringify_params(
                {
                    "user": user_address,
                    "limit": limit,
                    "offset": offset,
                    "sortBy": sort_by,
                    "type": type,
                    "sortDirection": sort_direction,
                    **kwargs,
                }
            )
            response = await client.get("/activity", params=params)
            if 400 <= response.status < 600:
                raise StatusCodeError(
                    response=response, message=response.text
                ) from None
            return [Activity.from_dict(item) for item in orjson.loads(response.text)]

    async def get_accounting_snapshot(self, user_address: str) -> bytes:
        async with self.get_client() as client:
            params = self.stringify_params({"user": user_address})
            response = await client.get("/v1/accounting/snapshot", params=params)
            if 400 <= response.status < 600:
                raise StatusCodeError(
                    response=response, message=response.text
                ) from None
            return response.content
