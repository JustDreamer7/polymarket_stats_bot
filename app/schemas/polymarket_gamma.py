from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class PublicProfile:
    proxy_wallet: str
    name: str
    verified_badge: bool
    created_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PublicProfile":
        return cls(
            proxy_wallet=data["proxyWallet"],
            name=data.get("name", ""),
            verified_badge=data.get("verifiedBadge", False),
            created_at=data.get("createdAt"),
        )
