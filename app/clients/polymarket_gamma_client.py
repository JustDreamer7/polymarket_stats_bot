import os

import orjson
from zapros import StatusCodeError

from app.clients.base_client import BaseClient
from app.schemas.polymarket_gamma import PublicProfile


class PolymarketGammaClient(BaseClient):
    def __init__(self):
        super().__init__("https://gamma-api.polymarket.com")

    def _get_headers(self) -> dict[str, str]:
        return {
            "POLY_ADDRESS": os.getenv("POLYMARKET_ADDRESS", ""),
            "POLY_API_KEY": os.getenv("POLYMARKET_API_KEY", ""),
            "POLY_PASSPHRASE": os.getenv("POLYMARKET_API_PASSPHRASE", ""),
        }

    async def get_public_profile(self, address: str) -> PublicProfile | None:
        async with self.get_client() as client:
            params = self.stringify_params({"address": address})
            response = await client.get(
                "/public-profile", params=params, headers=self._get_headers()
            )
            if 400 <= response.status < 600:
                raise StatusCodeError(
                    response=response, message=response.text
                ) from None
            data = orjson.loads(response.text)
            return PublicProfile.from_dict(data)
