from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models import Base


class BettorStats(Base):
    __tablename__ = "bettor_stats"

    uid: Mapped[str] = mapped_column(
        String(42), ForeignKey("bettors.proxy_wallet"), primary_key=True
    )
    last_trade_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_trades_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_trades_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    closed_trades_volume: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    current_trades_volume: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    # ! only for closed positions
    winnings: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    winrate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    roi: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    bettor: Mapped["Bettor"] = relationship(  # noqa: F821
        back_populates="stats", uselist=False
    )
