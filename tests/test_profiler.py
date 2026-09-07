"""Tests for the Perf Profiler decorator library."""

from __future__ import annotations

import threading

from profiler import ProfileResult, get_profiler_data, profile, reset_profiler


def test_profile_decorator_basic() -> None:
    """Verify @profile collects metrics and preserves the return value."""
    calls = 0

    @profile
    def simple_function(x: int) -> str:
        # Do enough work to exceed the process_time tick (about 15 ms on
        # Windows, much finer elsewhere) so CPU time is measurable.
        nonlocal calls
        _ = sum(range(2_000_000))
        calls += 1
        return str(x)

    result = simple_function(42)
    assert result == "42"
    assert calls == 1

    data = get_profiler_data(simple_function)
    assert "simple_function" in data
    entry = data["simple_function"]
    assert entry.call_count == 1
    assert entry.total_cpu_time > 0
    assert entry.total_duration > 0


def test_profile_decorator_multiple_calls() -> None:
    """Verify metrics accumulate correctly across multiple invocations."""

    @profile
    def repeated_function(n: int) -> int:
        return n * 2

    for value in (10, 20, 30):
        assert repeated_function(value) == value * 2

    entry = get_profiler_data(repeated_function)["repeated_function"]
    assert entry.call_count == 3
    assert entry.avg_cpu_time == entry.total_cpu_time / 3
    assert entry.min_cpu_time <= entry.avg_cpu_time <= entry.max_cpu_time
    assert entry.total_duration >= entry.total_cpu_time


def test_profile_decorator_with_kwargs() -> None:
    """Verify the decorator works with keyword arguments."""

    @profile
    def kw_function(a: int, b: str = "default") -> str:
        return f"{a}-{b}"

    assert kw_function(10, b="custom") == "10-custom"
    assert get_profiler_data(kw_function)["kw_function"].call_count == 1


def test_profile_decorator_preserves_name() -> None:
    """Verify functools.wraps keeps the original function name."""

    @profile
    def named_function(x: int) -> int:
        return x

    assert named_function.__name__ == "named_function"


def test_reset_profiler() -> None:
    """Verify reset_profiler clears accumulated data."""

    @profile
    def test_function(x: int) -> int:
        return x + 1

    test_function(5)
    assert get_profiler_data(test_function)["test_function"].call_count == 1

    reset_profiler(test_function)
    assert get_profiler_data(test_function) == {}


def test_get_profiler_data_undecorated() -> None:
    """Verify get_profiler_data returns an empty dict for plain functions."""

    def plain(x: int) -> int:
        return x

    assert get_profiler_data(plain) == {}


def test_profile_result_to_dict_fields() -> None:
    """Verify to_dict serializes every aggregate field."""
    result = ProfileResult("test_func")
    result.call_count = 5
    result.total_cpu_time = 0.123
    result.avg_cpu_time = 0.0246
    result.max_cpu_time = 0.05
    result.min_cpu_time = 0.01
    result.total_duration = 0.2
    result.memory_peak = 1024

    serialized = result.to_dict()
    assert serialized == {
        "function_name": "test_func",
        "call_count": 5,
        "total_cpu_time": 0.123,
        "avg_cpu_time": 0.0246,
        "max_cpu_time": 0.05,
        "min_cpu_time": 0.01,
        "total_duration": 0.2,
        "memory_peak": 1024,
    }


def test_memory_growth_detected_for_retaining_function() -> None:
    """Verify a function that retains objects shows positive net growth."""
    retained: list[bytes] = []

    @profile
    def leaky(payload_size: int) -> bytes:
        payload = bytearray(payload_size).hex().encode()
        retained.append(payload)
        return payload

    for _ in range(5):
        leaky(256 * 1024)

    entry = get_profiler_data(leaky)["leaky"]
    # Each call keeps ~512 KB alive, so peak net growth must be well above zero.
    assert entry.memory_peak > 100_000


def test_memory_tracking_can_be_disabled() -> None:
    """Verify @profile(memory=False) skips memory tracking."""

    @profile(memory=False)
    def no_memory(x: int) -> int:
        return x

    no_memory(1)
    entry = get_profiler_data(no_memory)["no_memory"]
    assert entry.call_count == 1
    assert entry.memory_peak == 0


def test_profile_decorator_thread_safety() -> None:
    """Verify concurrent calls do not lose updates."""

    @profile(memory=False)
    def shared(x: int) -> int:
        return x + 1

    threads = [threading.Thread(target=shared, args=(i,)) for i in range(40)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    entry = get_profiler_data(shared)["shared"]
    assert entry.call_count == 40


def test_profile_result_min_max_across_calls() -> None:
    """Verify min and max track the fastest and slowest calls."""

    @profile(memory=False)
    def varying_function(n: int) -> int:
        total = 0
        for i in range(n):
            total += i
        return total

    varying_function(100_000)
    varying_function(3_000_000)

    entry = get_profiler_data(varying_function)["varying_function"]
    assert entry.max_cpu_time > entry.min_cpu_time
