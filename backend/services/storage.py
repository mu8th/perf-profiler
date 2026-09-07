"""Persistence and aggregation for profile data."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select

from ..database import get_session
from ..models import MemorySnapshot, ProfileEntry


def record_profile_entry(
    function_name: str,
    cpu_time: float,
    duration: float,
    call_count: int,
    memory_peak_bytes: int | None = None,
) -> int:
    """Store one aggregated profile entry.

    Args:
        function_name: Name of the instrumented function.
        cpu_time: Total processor time across the recorded calls.
        duration: Total wall-clock time across the recorded calls.
        call_count: Number of recorded calls.
        memory_peak_bytes: Peak net memory growth observed per call, if tracked.

    Returns:
        The new row id.
    """
    with get_session() as session:
        entry = ProfileEntry(
            function_name=function_name,
            cpu_time=cpu_time,
            duration=duration,
            call_count=call_count,
            memory_peak_bytes=memory_peak_bytes,
        )
        session.add(entry)
        session.commit()
        return entry.id


def get_profiles() -> list[dict[str, Any]]:
    """Return all stored profile entries, oldest first.

    Returns:
        Serialized ProfileEntry dictionaries.
    """
    with get_session() as session:
        rows = session.execute(select(ProfileEntry).order_by(ProfileEntry.timestamp)).scalars().all()
        return [row.to_dict() for row in rows]


def get_hot_paths() -> list[dict[str, Any]]:
    """Compute hot paths from stored entries, ranked by CPU share.

    Aggregates entries per function name across the whole store, then ranks
    functions by their share of total recorded CPU time.

    Returns:
        List of dictionaries with function_name, avg_cpu_time, call_count,
        and percentage_of_total, most expensive first. Empty when no data.
    """
    with get_session() as session:
        rows = session.execute(select(ProfileEntry)).scalars().all()
    if not rows:
        return []

    totals: dict[str, dict[str, float]] = {}
    for row in rows:
        bucket = totals.setdefault(row.function_name, {"cpu": 0.0, "calls": 0})
        bucket["cpu"] += row.cpu_time
        bucket["calls"] += row.call_count

    grand_total = sum(bucket["cpu"] for bucket in totals.values())
    if grand_total <= 0:
        return []

    hot_paths: list[dict[str, Any]] = [
        {
            "function_name": name,
            "avg_cpu_time": bucket["cpu"] / bucket["calls"] if bucket["calls"] else 0.0,
            "call_count": int(bucket["calls"]),
            "percentage_of_total": round(bucket["cpu"] / grand_total * 100, 2),
        }
        for name, bucket in totals.items()
    ]
    hot_paths.sort(key=lambda hp: hp["percentage_of_total"], reverse=True)
    return hot_paths


def record_memory_snapshot(current_bytes: int, peak_bytes: int, allocation_count: int) -> int:
    """Store one memory snapshot.

    Args:
        current_bytes: Traced bytes currently allocated.
        peak_bytes: Peak traced bytes since tracking started.
        allocation_count: Number of live traced allocations.

    Returns:
        The new row id.
    """
    with get_session() as session:
        snapshot = MemorySnapshot(
            current_bytes=current_bytes,
            peak_bytes=peak_bytes,
            allocation_count=allocation_count,
        )
        session.add(snapshot)
        session.commit()
        return snapshot.id


def get_memory_snapshots() -> list[dict[str, Any]]:
    """Return all stored memory snapshots, oldest first.

    Returns:
        Serialized MemorySnapshot dictionaries.
    """
    with get_session() as session:
        rows = (
            session.execute(select(MemorySnapshot).order_by(MemorySnapshot.timestamp))
            .scalars()
            .all()
        )
        return [row.to_dict() for row in rows]


def latest_summary() -> dict[str, Any]:
    """Summarize the stored data for live metric broadcasts.

    Returns:
        Dictionary with total cpu_time (seconds), total memory_peak bytes,
        and total call_count across all stored entries.
    """
    with get_session() as session:
        cpu = session.execute(select(func.coalesce(func.sum(ProfileEntry.cpu_time), 0.0))).scalar_one()
        calls = session.execute(select(func.coalesce(func.sum(ProfileEntry.call_count), 0))).scalar_one()
        memory = session.execute(
            select(func.coalesce(func.max(MemorySnapshot.current_bytes), 0))
        ).scalar_one()
    return {"cpu_time": float(cpu), "memory_bytes": int(memory), "call_count": int(calls)}
