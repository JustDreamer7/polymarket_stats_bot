import uuid
from datetime import datetime

from sqlalchemy import BIGINT, Boolean, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models import Base


class User(Base):
    __tablename__ = "users"

    uid: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    user_tg_id: Mapped[int] = mapped_column(BIGINT, nullable=False, unique=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    firstname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lastname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
