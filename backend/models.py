"""SQLAlchemy ORM models for Perf Profiler."""

from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base class for all Perf Profiler models."""


def _utcnow() -> datetime.datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.datetime.now(datetime.timezone.utc)


class ProfileEntry(Base):
    """Database record for one instrumented function's aggregated profile."""

    __tablename__ = "profile_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    function_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cpu_time: Mapped[float] = mapped_column(Float, nullable=False)
    duration: Mapped[float] = mapped_column(Float, nullable=False)
    call_count: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    memory_peak_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def to_dict(self) -> dict[str, Any]:
        """Serialize entry as a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "function_name": self.function_name,
            "cpu_time": self.cpu_time,
            "duration": self.duration,
            "call_count": self.call_count,
            "timestamp": self.timestamp.isoformat(),
            "memory_peak_bytes": self.memory_peak_bytes,
        }


class MemorySnapshot(Base):
    """Database record for a process memory allocation snapshot."""

    __tablename__ = "memory_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    current_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    peak_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    allocation_count: Mapped[int] = mapped_column(Integer, nullable=False)

    def to_dict(self) -> dict[str, Any]:
        """Serialize snapshot as a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "current_bytes": self.current_bytes,
            "peak_bytes": self.peak_bytes,
            "allocation_count": self.allocation_count,
        }
