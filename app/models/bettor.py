from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models import Base


class Bettor(Base):
    __tablename__ = "bettors"

    proxy_wallet: Mapped[str] = mapped_column(String(42), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    subscriptions: Mapped[list["Subscription"]] = relationship(  # noqa: F821
        back_populates="bettor", cascade="all, delete-orphan"
    )
    stats: Mapped["BettorStats"] = relationship(  # noqa: F821
        back_populates="bettor", cascade="all, delete-orphan", uselist=False
    )
