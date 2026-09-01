"""SQLAlchemy models for Perf Profiler database."""

from __future__ import annotations

import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ProfileEntry(Base):  # type: ignore[misc]
    """Database record for a single function call profile."""

    __tablename__ = "profile_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    function_name = Column(String(255), nullable=False, index=True)  # type: ignore[assignment]
    cpu_time = Column(Float, nullable=False)  # type: ignore[assignment]
    duration = Column(Float, nullable=False)  # type: ignore[assignment]
    call_count = Column(Integer, nullable=False)  # type: ignore[assignment]
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)  # type: ignore[assignment]
    memory_peak_bytes = Column(Integer, nullable=True)  # type: ignore[assignment]
    metadata = Column(Text, nullable=True)  # type: ignore[assignment]

    def to_dict(self) -> dict[str, Any]:
        """Serialize entry as JSON-compatible dictionary."""
        return {
            "id": self.id,
            "function_name": self.function_name,
            "cpu_time": self.cpu_time,
            "duration": self.duration,
            "call_count": self.call_count,
            "timestamp": self.timestamp.isoformat(),
            "memory_peak_bytes": self.memory_peak_bytes,
        }


class HotPath(Base):
    """Database record for detected hot paths."""

    __tablename__ = "hot_paths"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    function_name: str = Column(String(255), nullable=False, index=True)
    avg_cpu_time: float = Column(Float, nullable=False)
    call_count: int = Column(Integer, nullable=False)
    percentage_of_total: float = Column(Float, nullable=False)
    detected_at: datetime.datetime = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Serialize hot path entry as JSON-compatible dictionary."""
        return {
            "id": self.id,
            "function_name": self.function_name,
            "avg_cpu_time": self.avg_cpu_time,
            "call_count": self.call_count,
            "percentage_of_total": self.percentage_of_total,
            "detected_at": self.detected_at.isoformat(),
        }


class MemorySnapshot(Base):
    """Database record for memory allocation snapshots."""

    __tablename__ = "memory_snapshots"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    timestamp: datetime.datetime = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    current_bytes: int = Column(Integer, nullable=False)
    peak_bytes: int = Column(Integer, nullable=False)
    allocation_count: int = Column(Integer, nullable=False)

    def to_dict(self) -> dict[str, Any]:
        """Serialize memory snapshot as JSON-compatible dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "current_bytes": self.current_bytes,
            "peak_bytes": self.peak_bytes,
            "allocation_count": self.allocation_count,
        }


from typing import Any