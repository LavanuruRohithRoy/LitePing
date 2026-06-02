import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, BigInteger, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    monitors: Mapped[list["Monitor"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Monitor(Base):
    __tablename__ = "monitors"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", on_delete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    monitor_type: Mapped[str] = mapped_column(String(20), default="HTTP")  # 'HTTP' or 'CRON'
    target_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    check_interval_seconds: Mapped[int] = mapped_column(Integer, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    owner: Mapped["User"] = relationship(back_populates="monitors")
    logs: Mapped[list["PingLog"]] = relationship(back_populates="monitor", cascade="all, delete-orphan")


class PingLog(Base):
    __tablename__ = "ping_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    monitor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("monitors.id", on_delete="CASCADE"), nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_up: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    monitor: Mapped["Monitor"] = relationship(back_populates="logs")

# Core chronological performance optimization scanning index
Index("idx_logs_monitor_time", PingLog.monitor_id, PingLog.checked_at.desc())
