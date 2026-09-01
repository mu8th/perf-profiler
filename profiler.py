"""Perf Profiler — decorator-based instrumentation library."""

from __future__ import annotations

import time
import tracemalloc
from collections.abc import Callable
from functools import wraps
from typing import Any


class ProfileResult:
    """Single function call profiling result."""

    def __init__(self) -> None:
        self.function_name: str = ""
        self.call_count: int = 0
        self.total_cpu_time: float = 0.0
        self.avg_cpu_time: float = 0.0
        self.max_cpu_time: float = 0.0
        self.min_cpu_time: float = 0.0
        self.total_duration: float = 0.0
        self.memory_peak: int = 0
        self.memory_snapshot: list[tuple[int, int]] = []

    def to_dict(self) -> dict[str, Any]:
        """Serialize result as JSON-compatible dictionary."""
        return {
            "function_name": self.function_name,
            "call_count": self.call_count,
            "total_cpu_time": self.total_cpu_time,
            "avg_cpu_time": self.avg_cpu_time,
            "max_cpu_time": self.max_cpu_time,
            "min_cpu_time": self.min_cpu_time,
            "total_duration": self.total_duration,
            "memory_peak": self.memory_peak,
        }


class Profiler:
    """Collect and aggregate profiling metrics for decorated functions."""

    def __init__(self) -> None:
        self.results: dict[str, ProfileResult] = {}
        self._tracemalloc_started: bool = False

    def start_tracemalloc(self) -> None:
        """Begin memory tracking via tracemalloc. Called once per session."""
        if not self._tracemalloc_started:
            tracemalloc.start()
            self._tracemalloc_started = True

    def stop_tracemalloc(self) -> None:
        """Stop memory tracking and capture final snapshot."""
        if self._tracemalloc_started:
            current, peak = tracemalloc.get_current_and_peak_snapshot()
            for result in self.results.values():
                result.memory_peak = peak.size
                result.memory_snapshot = current.traceback

    def get_result(self, function_name: str) -> ProfileResult | None:
        """Retrieve aggregated result for a named function."""
        return self.results.get(function_name)

    def get_all_results(self) -> dict[str, ProfileResult]:
        """Return all collected results keyed by function name."""
        return self.results


def profile(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that instruments a function with CPU and memory metrics.

    Args:
        func: The callable to instrument.

    Returns:
        Wrapped function that collects profiling data on each invocation.

    Usage:
        @profile
        def my_function(x: int) -> str:
            return str(x)
    """
    profiler = Profiler()

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        cpu_time = end_time - start_time

        function_name = func.__name__
        if function_name not in profiler.results:
            profiler.results[function_name] = ProfileResult()
            profiler.results[function_name].function_name = function_name

        existing = profiler.results[function_name]
        existing.call_count += 1
        existing.total_cpu_time += cpu_time
        existing.avg_cpu_time = existing.total_cpu_time / existing.call_count
        existing.max_cpu_time = max(existing.max_cpu_time, cpu_time)
        if existing.call_count == 1 or cpu_time < existing.min_cpu_time:
            existing.min_cpu_time = cpu_time

        return result

    wrapper._profiler = profiler  # type: ignore[attr-defined]
    return wrapper


def get_profiler_data(func: Callable[..., Any]) -> dict[str, ProfileResult]:
    """Extract profiling data from a decorated function.

    Args:
        func: A function decorated with @profile.

    Returns:
        Dictionary of all collected results for this session.
    """
    profiler = getattr(func, "_profiler", None)  # type: ignore[attr-defined]
    if profiler is not None:
        return profiler.get_all_results()
    return {}


def reset_profiler(func: Callable[..., Any]) -> None:
    """Reset profiling data for a decorated function.

    Args:
        func: A function decorated with @profile.
    """
    profiler = getattr(func, "_profiler", None)  # type: ignore[attr-defined]
    if profiler is not None:
        profiler.results.clear()