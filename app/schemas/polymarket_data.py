from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal


@dataclass
class Position:
    proxy_wallet: str
    asset: str
    condition_id: str
    size: float
    avg_price: float
    initial_value: float
    current_value: float
    cash_pnl: float
    percent_pnl: float
    total_bought: float
    realized_pnl: float
    percent_realized_pnl: float
    cur_price: float
    redeemable: bool
    mergeable: bool
    title: str
    slug: str
    icon: str
    event_slug: str
    outcome: str
    outcome_index: int
    opposite_outcome: str
    opposite_asset: str
    end_date: str
    negative_risk: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Position":
        return cls(
            proxy_wallet=data["proxyWallet"],
            asset=data["asset"],
            condition_id=data["conditionId"],
            size=data["size"],
            avg_price=data["avgPrice"],
            initial_value=data["initialValue"],
            current_value=data["currentValue"],
            cash_pnl=data["cashPnl"],
            percent_pnl=data["percentPnl"],
            total_bought=data["totalBought"],
            realized_pnl=data["realizedPnl"],
            percent_realized_pnl=data["percentRealizedPnl"],
            cur_price=data["curPrice"],
            redeemable=data["redeemable"],
            mergeable=data["mergeable"],
            title=data["title"],
            slug=data["slug"],
            icon=data["icon"],
            event_slug=data["eventSlug"],
            outcome=data["outcome"],
            outcome_index=data["outcomeIndex"],
            opposite_outcome=data["oppositeOutcome"],
            opposite_asset=data["oppositeAsset"],
            end_date=data["endDate"],
            negative_risk=data["negativeRisk"],
        )


@dataclass
class ClosedPosition:
    proxy_wallet: str
    asset: str
    condition_id: str
    avg_price: float
    total_bought: float
    realized_pnl: float
    cur_price: float
    timestamp: int
    title: str
    slug: str
    icon: str
    event_slug: str
    outcome: str
    outcome_index: int
    opposite_outcome: str
    opposite_asset: str
    end_date: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClosedPosition":
        return cls(
            proxy_wallet=data["proxyWallet"],
            asset=data["asset"],
            condition_id=data["conditionId"],
            avg_price=data["avgPrice"],
            total_bought=data["totalBought"],
            realized_pnl=data["realizedPnl"],
            cur_price=data["curPrice"],
            timestamp=data["timestamp"],
            title=data["title"],
            slug=data["slug"],
            icon=data["icon"],
            event_slug=data["eventSlug"],
            outcome=data["outcome"],
            outcome_index=data["outcomeIndex"],
            opposite_outcome=data["oppositeOutcome"],
            opposite_asset=data["oppositeAsset"],
            end_date=data["endDate"],
        )


@dataclass
class Trade:
    proxy_wallet: str
    side: Literal["BUY", "SELL"] | None
    size: float
    price: float
    timestamp: int
    title: str
    slug: str
    event_slug: str
    outcome: str
    outcome_index: int
    name: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Trade":
        return cls(
            proxy_wallet=data["proxyWallet"],
            side=data.get("side"),
            size=data["size"],
            price=data["price"],
            timestamp=data["timestamp"],
            title=data["title"],
            slug=data["slug"],
            event_slug=data["eventSlug"],
            outcome=data["outcome"],
            outcome_index=data["outcomeIndex"],
            name=data["name"],
        )


@dataclass
class Activity:
    proxy_wallet: str
    timestamp: int
    condition_id: str
    type: str
    size: float
    usdc_size: float
    transaction_hash: str
    price: float
    asset: str
    side: str | None
    outcome_index: int
    title: str
    slug: str
    icon: str
    event_slug: str
    outcome: str
    name: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Activity":
        return cls(
            proxy_wallet=data["proxyWallet"],
            timestamp=data["timestamp"],
            condition_id=data["conditionId"],
            type=data["type"],
            size=data["size"],
            usdc_size=data["usdcSize"],
            transaction_hash=data["transactionHash"],
            price=data["price"],
            asset=data["asset"],
            side=data.get("side"),
            outcome_index=data["outcomeIndex"],
            title=data["title"],
            slug=data["slug"],
            icon=data["icon"],
            event_slug=data["eventSlug"],
            outcome=data["outcome"],
            name=data["name"],
        )


@dataclass
class EquitySnapshot:
    cash_balance: float
    positions_value: float
    equity: float
    valuation_time: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EquitySnapshot":
        return cls(
            cash_balance=float(data["cashBalance"]),
            positions_value=float(data["positionsValue"]),
            equity=float(data["equity"]),
            valuation_time=data["valuationTime"],
        )


@dataclass
class BettorStats:
    winrate: float
    trades: int
    winnings: float
    volume: float
    roi: float


@dataclass
class BettorStatsSnapshot:
    uid: str
    last_trade_date: datetime | None
    closed_trades_count: int
    current_trades_count: int
    closed_trades_volume: float
    current_trades_volume: float
    winnings: float
    winrate: float
    roi: float


@dataclass
class LeaderboardEntry:
    rank: str
    proxy_wallet: str
    username: str
    pnl: float
    volume: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LeaderboardEntry":
        return cls(
            rank=data["rank"],
            proxy_wallet=data["proxyWallet"],
            username=data["userName"],
            pnl=data["pnl"],
            volume=data["vol"],
        )
