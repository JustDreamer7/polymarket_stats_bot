import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    uid: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.uid"), nullable=False
    )
    bettor_id: Mapped[str] = mapped_column(
        String(42), ForeignKey("bettors.proxy_wallet"), nullable=False
    )
    subscribed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="subscriptions")
    bettor: Mapped["Bettor"] = relationship(back_populates="subscriptions")
