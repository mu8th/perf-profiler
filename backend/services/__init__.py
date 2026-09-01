"""Business logic for Perf Profiler."""

from __future__ import annotations

from typing import Any


class ProfileService:
    """Manage profile data collection and storage."""

    def collect_profile(self, function_name: str, cpu_time: float) -> dict[str, Any]:
        """Collect a single profile entry. Returns serialized result."""
        return {
            "function_name": function_name,
            "cpu_time": cpu_time,
        }

    def aggregate_profiles(self, entries: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate multiple profile entries into summary statistics."""
        total_cpu = sum(e["cpu_time"] for e in entries)
        count = len(entries)
        return {
            "total_cpu_time": total_cpu,
            "call_count": count,
            "avg_cpu_time": total_cpu / count if count > 0 else 0.0,
        }

    def detect_hot_paths(self, profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Identify functions consuming most CPU time percentage."""
        return []


class MemoryService:
    """Manage memory profiling data."""

    def capture_snapshot(self) -> dict[str, Any]:
        """Capture current and peak memory allocation snapshot."""
        return {
            "current_bytes": 0,
            "peak_bytes": 0,
        }

    def track_trend(self, snapshots: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze memory allocation trend over time."""
        return {}


class WebSocketService:
    """Manage WebSocket metric streaming."""

    async def broadcast_metrics(self, websocket: Any, data: dict[str, Any]) -> None:
        """Send metrics update to connected WebSocket client."""
        await websocket.send_json(data)