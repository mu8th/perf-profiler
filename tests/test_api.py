"""API tests for the Perf Profiler FastAPI service."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from backend import database
from backend.main import app


@pytest.fixture()
def client(tmp_path) -> Iterator[TestClient]:
    """Provide a TestClient backed by a fresh temporary SQLite database."""
    database.init_db(f"sqlite:///{tmp_path / 'test.db'}")
    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    """Verify the health endpoint reports ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_profile_roundtrip(client: TestClient) -> None:
    """Verify a stored profile entry is returned by GET /api/profiles."""
    payload = {
        "function_name": "demo_func",
        "cpu_time": 0.5,
        "duration": 0.6,
        "call_count": 10,
        "memory_peak_bytes": 2048,
    }
    stored = client.post("/api/profiles", json=payload)
    assert stored.status_code == 200
    assert stored.json()["status"] == "stored"

    profiles = client.get("/api/profiles").json()
    match = [p for p in profiles if p["function_name"] == "demo_func"]
    assert len(match) == 1
    assert match[0]["cpu_time"] == 0.5
    assert match[0]["call_count"] == 10
    assert match[0]["memory_peak_bytes"] == 2048


def test_profile_payload_validation(client: TestClient) -> None:
    """Verify incomplete profile payloads are rejected with 422."""
    response = client.post("/api/profiles", json={"function_name": "incomplete"})
    assert response.status_code == 422


def test_hot_paths_ranking_and_percentages(client: TestClient) -> None:
    """Verify hot paths rank by CPU share and percentages sum to ~100."""
    hot_payload = {"function_name": "hot", "cpu_time": 3.0, "duration": 3.0, "call_count": 3}
    cold_payload = {"function_name": "cold", "cpu_time": 1.0, "duration": 1.0, "call_count": 1}
    client.post("/api/profiles", json=hot_payload)
    client.post("/api/profiles", json=cold_payload)

    hot_paths = client.get("/api/hot_paths").json()
    assert [hp["function_name"] for hp in hot_paths] == ["hot", "cold"]
    assert hot_paths[0]["percentage_of_total"] == pytest.approx(75.0)
    assert hot_paths[1]["percentage_of_total"] == pytest.approx(25.0)
    total = sum(hp["percentage_of_total"] for hp in hot_paths)
    assert total == pytest.approx(100.0, abs=0.01)


def test_hot_paths_empty(client: TestClient) -> None:
    """Verify hot paths returns an empty list with no stored data."""
    assert client.get("/api/hot_paths").json() == []


def test_memory_snapshot_roundtrip(client: TestClient) -> None:
    """Verify a stored memory snapshot is returned by GET /api/memory_snapshots."""
    payload = {"current_bytes": 1024, "peak_bytes": 2048, "allocation_count": 42}
    stored = client.post("/api/memory_snapshots", json=payload)
    assert stored.status_code == 200

    snapshots = client.get("/api/memory_snapshots").json()
    match = [s for s in snapshots if s["current_bytes"] == 1024]
    assert len(match) == 1
    assert match[0]["peak_bytes"] == 2048
    assert match[0]["allocation_count"] == 42


def test_websocket_receives_metric_ticks(client: TestClient) -> None:
    """Verify a connected client receives periodic metric summaries."""
    with client.websocket_connect("/ws/metrics") as websocket:
        first = websocket.receive_json()
        second = websocket.receive_json()
    for message in (first, second):
        assert message["type"] == "tick"
        assert "cpu_time" in message
        assert "memory_bytes" in message
        assert "call_count" in message


def test_dashboard_served_at_root(client: TestClient) -> None:
    """Verify the frontend is served at the root path."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Perf Profiler" in response.text
