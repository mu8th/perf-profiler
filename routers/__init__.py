"""REST API routes for Perf Profiler."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.get("/profiles")
async def get_profiles() -> list[dict[str, Any]]:
    """Retrieve all collected profile entries. Returns JSON array."""
    return []


@router.get("/profiles/{function_name}")
async def get_profile(function_name: str) -> dict[str, Any]:
    """Retrieve aggregated profile for a specific function."""
    return {}


@router.post("/profiles")
async def submit_profile(data: dict[str, Any]) -> dict[str, Any]:
    """Accept and store a new profile entry. Returns confirmation."""
    return {"status": "accepted"}


@router.get("/hot_paths")
async def get_hot_paths() -> list[dict[str, Any]]:
    """Retrieve detected hot paths ranked by CPU time percentage."""
    return []


@router.get("/memory_snapshots")
async def get_memory_snapshots() -> list[dict[str, Any]]:
    """Retrieve memory allocation trend snapshots."""
    return []


websocket_router = APIRouter()


@websocket_router.websocket("/ws/metrics")
async def metrics_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint for streaming real-time metrics.

    Clients connect to receive live profile data updates.
    """
    await websocket.accept()
    try:
        while True:
            await websocket.receive_json()
            await websocket.send_json({"status": "received"})
    except WebSocketDisconnect:
        pass