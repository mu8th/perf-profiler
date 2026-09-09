"""FastAPI entry point for Perf Profiler."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.websockets import WebSocketDisconnect

from .database import init_db
from .services import storage

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
TICK_INTERVAL_SECONDS = 2.0


class ProfilePayload(BaseModel):
    """Body for POST /api/profiles."""

    function_name: str
    cpu_time: float
    duration: float
    call_count: int
    memory_peak_bytes: int | None = None


class MemorySnapshotPayload(BaseModel):
    """Body for POST /api/memory_snapshots."""

    current_bytes: int
    peak_bytes: int
    allocation_count: int


@asynccontextmanager
async def lifespan(_: FastAPI) -> Any:
    """Initialize the database when the app starts."""
    init_db()
    yield


app = FastAPI(
    title="Perf Profiler",
    description="Real-time performance profiling service",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Report service status."""
    return {"status": "ok"}


@app.get("/api/profiles")
async def get_profiles() -> list[dict[str, Any]]:
    """Return all stored profile entries, oldest first."""
    return storage.get_profiles()


@app.post("/api/profiles")
async def submit_profile(payload: ProfilePayload) -> dict[str, Any]:
    """Store an aggregated profile entry.

    Args:
        payload: Aggregated metrics for one instrumented function.

    Returns:
        Confirmation with the stored row id.
    """
    entry_id = storage.record_profile_entry(
        function_name=payload.function_name,
        cpu_time=payload.cpu_time,
        duration=payload.duration,
        call_count=payload.call_count,
        memory_peak_bytes=payload.memory_peak_bytes,
    )
    return {"status": "stored", "id": entry_id}


@app.get("/api/hot_paths")
async def get_hot_paths() -> list[dict[str, Any]]:
    """Return hot paths ranked by share of total recorded CPU time."""
    return storage.get_hot_paths()


@app.get("/api/memory_snapshots")
async def get_memory_snapshots() -> list[dict[str, Any]]:
    """Return all stored memory snapshots, oldest first."""
    return storage.get_memory_snapshots()


@app.post("/api/memory_snapshots")
async def submit_memory_snapshot(payload: MemorySnapshotPayload) -> dict[str, Any]:
    """Store a memory snapshot.

    Args:
        payload: Traced memory figures from one point in time.

    Returns:
        Confirmation with the stored row id.
    """
    snapshot_id = storage.record_memory_snapshot(
        current_bytes=payload.current_bytes,
        peak_bytes=payload.peak_bytes,
        allocation_count=payload.allocation_count,
    )
    return {"status": "stored", "id": snapshot_id}


@app.websocket("/ws/metrics")
async def metrics_websocket(websocket: WebSocket) -> None:
    """Stream live metric summaries to the dashboard.

    Each connection receives a summary of all stored metrics every few
    seconds, straight from the database. Clients only listen; they never send.
    The summary is fetched in a worker thread so the blocking database call
    does not stall the event loop.
    """
    await websocket.accept()
    while True:
        try:
            summary = await asyncio.to_thread(storage.latest_summary)
            await websocket.send_json({"type": "tick", **summary})
        except (WebSocketDisconnect, RuntimeError):
            # The client disconnected or the socket already closed; stop.
            break
        await asyncio.sleep(TICK_INTERVAL_SECONDS)


# Serve the dashboard after all API routes are registered.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
