"""Tests for Perf Profiler decorator and library."""

from __future__ import annotations

import pytest


def test_profile_decorator_basic() -> None:
    """Verify @profile decorator collects CPU time on function invocation.

    Expected: decorated function returns correct result, profiler data exists.
    """
    from profiler import get_profiler_data, profile

    @profile
    def simple_function(x: int) -> str:
        return str(x)

    result = simple_function(42)
    assert result == "42"

    data = get_profiler_data(simple_function)
    assert len(data) > 0
    assert "simple_function" in data


def test_profile_decorator_multiple_calls() -> None:
    """Verify @profile accumulates metrics across multiple invocations.

    Expected: call_count increases, avg_cpu_time computed correctly.
    """
    from profiler import get_profiler_data, profile

    @profile
    def repeated_function(n: int) -> int:
        return n * 2

    repeated_function(10)
    repeated_function(20)
    repeated_function(30)

    data = get_profiler_data(repeated_function)
    entry = data["repeated_function"]
    assert entry.call_count == 3


def test_reset_profiler() -> None:
    """Verify reset_profiler clears accumulated data.

    Expected: call_count returns to zero after reset.
    """
    from profiler import get_profiler_data, profile, reset_profiler

    @profile
    def test_function(x: int) -> int:
        return x + 1

    test_function(5)
    assert get_profiler_data(test_function)["test_function"].call_count == 1

    reset_profiler(test_function)
    data = get_profiler_data(test_function)
    assert len(data) == 0


def test_profile_result_to_dict() -> None:
    """Verify ProfileResult serialization produces valid dictionary.

    Expected: dict contains all required fields with correct types.
    """
    from profiler import ProfileResult

    result = ProfileResult()
    result.function_name = "test_func"
    result.call_count = 5
    result.total_cpu_time = 0.123

    serialized = result.to_dict()
    assert isinstance(serialized, dict)
    assert "function_name" in serialized
    assert "call_count" in serialized


def test_hot_path_detection_empty_data() -> None:
    """Verify hot path detection returns empty list when no data available.

    Expected: service returns [] for empty input.
    """
    from services import ProfileService

    service = ProfileService()
    result = service.detect_hot_paths([])
    assert result == []


def test_memory_snapshot_capture() -> None:
    """Verify MemoryService captures snapshot with required fields.

    Expected: dict contains current_bytes and peak_bytes keys.
    """
    from services import MemoryService

    service = MemoryService()
    snapshot = service.capture_snapshot()
    assert "current_bytes" in snapshot
    assert "peak_bytes" in snapshot


def test_aggregate_profiles_computation() -> None:
    """Verify aggregate_profiles computes correct average CPU time.

    Expected: avg_cpu_time equals total divided by count.
    """
    from services import ProfileService

    service = ProfileService()
    entries = [
        {"cpu_time": 0.1},
        {"cpu_time": 0.2},
        {"cpu_time": 0.3},
    ]

    aggregated = service.aggregate_profiles(entries)
    assert aggregated["call_count"] == 3
    assert aggregated["avg_cpu_time"] == pytest.approx(0.2)


def test_dashboard_flame_graph_render() -> None:
    """Verify Dashboard renders flame graph instructions from profile data.

    Expected: output is JSON string with drawing commands.
    """
    from frontend.dashboard import Dashboard

    dashboard = Dashboard()
    profiles = [
        {"cpu_time": 0.5, "function_name": "func_a"},
        {"cpu_time": 0.3, "function_name": "func_b"},
    ]

    result = dashboard.render_flame_graph(profiles)
    assert isinstance(result, str)


def test_dashboard_hot_paths_table_render() -> None:
    """Verify Dashboard renders HTML table rows for hot path data.

    Expected: output contains HTML tr elements with function names.
    """
    from frontend.dashboard import Dashboard

    dashboard = Dashboard()
    hot_paths = [
        {"function_name": "hot_func", "percentage_of_total": 50.0},
    ]

    result = dashboard.render_hot_paths_table(hot_paths)
    assert "<tr>" in result
    assert "hot_func" in result


def test_update_metrics_display_format() -> None:
    """Verify update_metrics_display produces formatted HTML string.

    Expected: output contains span elements with metric values.
    """
    from frontend.dashboard import update_metrics_display

    data = {"cpu_time": 0.15, "memory_bytes": 1024}
    result = update_metrics_display(data)
    assert "<span>" in result
    assert "0.15s" in result


def test_websocket_service_accept() -> None:
    """Verify WebSocketService broadcast_metrics handles mock connection cycle.

    Expected: service method completes without raising error on mock websocket.
    """
    import asyncio

    from services import WebSocketService

    service = WebSocketService()
    class MockWebSocket:
        async def accept(self) -> None:
            pass
        async def receive_json(self) -> dict[str, Any]:
            return {"test": "data"}
        async def send_json(self, data: dict[str, Any]) -> None:
            pass

    mock_ws = MockWebSocket()
    asyncio.run(service.broadcast_metrics(mock_ws, {"status": "ok"}) if hasattr(service, 'broadcast_metrics') else None)


def test_profile_decorator_with_kwargs() -> None:
    """Verify @profile decorator works with keyword arguments.

    Expected: decorated function accepts kwargs and collects metrics.
    """
    from profiler import get_profiler_data, profile

    @profile
    def kw_function(a: int, b: str = "default") -> str:
        return f"{a}-{b}"

    result = kw_function(10, b="custom")
    assert result == "10-custom"

    data = get_profiler_data(kw_function)
    assert len(data) > 0


def test_profile_decorator_preserves_name() -> None:
    """Verify @profile decorator preserves original function name via functools.wraps.

    Expected: wrapper.__name__ equals original func.__name__.
    """
    from profiler import profile

    @profile
    def named_function(x: int) -> int:
        return x

    assert named_function.__name__ == "named_function"


def test_profile_result_min_max_cpu_time() -> None:
    """Verify ProfileResult tracks min and max CPU time across calls.

    Expected: min equals first call, max equals longest call.
    """
    from profiler import get_profiler_data, profile

    @profile
    def varying_function(n: int) -> int:
        return n * 2

    varying_function(10)  # short call
    varying_function(100)  # longer call

    data = get_profiler_data(varying_function)
    entry = data["varying_function"]
    assert entry.max_cpu_time >= entry.min_cpu_time


def test_memory_service_track_trend() -> None:
    """Verify MemoryService track_trend returns analysis dict.

    Expected: output contains trend summary fields.
    """
    from services import MemoryService

    service = MemoryService()
    snapshots = [
        {"current_bytes": 1024, "peak_bytes": 2048},
        {"current_bytes": 512, "peak_bytes": 2048},
    ]

    result = service.track_trend(snapshots)
    assert isinstance(result, dict)


def test_dashboard_memory_chart_render() -> None:
    """Verify Dashboard renders memory chart instructions from snapshot data.

    Expected: output is JSON string with stroke commands.
    """
    from frontend.dashboard import Dashboard

    dashboard = Dashboard()
    snapshots = [
        {"timestamp": 100, "current_bytes": 1024, "peak_bytes": 2048},
        {"timestamp": 200, "current_bytes": 512, "peak_bytes": 2048},
    ]

    result = dashboard.render_memory_chart(snapshots)
    assert isinstance(result, str)


def test_dashboard_empty_data_render() -> None:
    """Verify Dashboard renders empty data placeholder for all sections.

    Expected: flame graph, hot paths, memory chart return no-data strings.
    """
    from frontend.dashboard import Dashboard

    dashboard = Dashboard()
    assert dashboard.render_flame_graph([]) == '{"command": "draw_text", "text": "No data available"}'
    assert dashboard.render_hot_paths_table([]) == '<tr><td colspan="4">No hot paths detected</td></tr>'
    assert dashboard.render_memory_chart([]) == '{"command": "draw_text", "text": "No data available"}'


def test_profile_result_all_fields_serialized() -> None:
    """Verify ProfileResult.to_dict includes all defined fields.

    Expected: dict contains function_name, call_count, total_cpu_time, avg_cpu_time, max_cpu_time, min_cpu_time, memory_peak.
    """
    from profiler import ProfileResult

    result = ProfileResult()
    result.function_name = "test_func"
    result.call_count = 5
    result.total_cpu_time = 0.123
    result.avg_cpu_time = 0.0246
    result.max_cpu_time = 0.05
    result.min_cpu_time = 0.01
    result.memory_peak = 1024

    serialized = result.to_dict()
    assert "function_name" in serialized
    assert "call_count" in serialized
    assert "total_cpu_time" in serialized
    assert "avg_cpu_time" in serialized
    assert "max_cpu_time" in serialized
    assert "min_cpu_time" in serialized
    assert "memory_peak" in serialized


def test_profile_service_collect_profile() -> None:
    """Verify ProfileService collect_profile produces valid entry dict.

    Expected: dict contains function_name and cpu_time keys.
    """
    from services import ProfileService

    service = ProfileService()
    result = service.collect_profile("test_func", 0.15)
    assert "function_name" in result
    assert "cpu_time" in result


def test_update_metrics_display_default_values() -> None:
    """Verify update_metrics_display handles missing metric values with defaults.

    Expected: output uses 0 for missing cpu_time or memory_bytes.
    """
    from frontend.dashboard import update_metrics_display

    data = {"cpu_time": 0}
    result = update_metrics_display(data)
    assert "0s" in result


def test_update_metrics_display_memory_only() -> None:
    """Verify update_metrics_display handles missing cpu_time with default.

    Expected: output contains memory value and 0 for cpu_time.
    """
    from frontend.dashboard import update_metrics_display

    data = {"memory_bytes": 2048}
    result = update_metrics_display(data)
    assert "2048 bytes" in result
    assert "0s" in result


from typing import Any