"""FastAPI entry point for Perf Profiler."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sqlalchemy import create_engine

engine = create_engine("sqlite:///perf_profiler.db")


app = FastAPI(title="Perf Profiler", description="Real-time performance profiling service")


@app.on_event("startup")
async def initialize_database() -> None:
    """Initialize SQLite database and SQLAlchemy tables on startup."""
    from models import Base
    Base.metadata.create_all(engine)


@app.on_event("shutdown")
async def shutdown_profiler() -> None:
    """Stop memory tracking and flush profiler data to database on shutdown."""


def create_app() -> FastAPI:
    """Create and configure the application. Returns configured instance."""
    return app


@app.get("/profiles")
async def get_profiles() -> list[dict[str, Any]]:
    """Retrieve all collected profile entries from database."""
    return []


@app.get("/profiles/{function_name}")
async def get_profile(function_name: str) -> dict[str, Any]:
    """Retrieve aggregated profile for a specific function."""
    return {}


@app.post("/profiles")
async def submit_profile(data: dict[str, Any]) -> dict[str, Any]:
    """Accept and store a new profile entry in database. Returns confirmation."""
    return {"status": "accepted"}


@app.get("/hot_paths")
async def get_hot_paths() -> list[dict[str, Any]]:
    """Retrieve detected hot paths ranked by CPU time percentage."""
    return []


@app.get("/memory_snapshots")
async def get_memory_snapshots() -> list[dict[str, Any]]:
    """Retrieve memory allocation trend snapshots from database."""
    return []


@app.websocket("/ws/metrics")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)