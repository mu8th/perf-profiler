"""Performance Profiler: a decorator-based instrumentation library.

Instruments Python functions with per-call CPU time, wall-clock duration,
and net memory growth. The library is stdlib-only so it can be imported
from any process without installing the dashboard backend.

CPU time comes from ``time.process_time`` (processor time actually consumed
by this process), which is distinct from wall-clock duration measured with
``time.perf_counter``. Memory growth is measured with ``tracemalloc`` as the
change in traced, still-allocated bytes across one call: a function that
retains objects on every call shows persistent positive growth, the shape of
a leak. Because tracemalloc tracks the whole process, allocations made by
other threads during the same window are attributed to the running call.
"""

from __future__ import annotations

import threading
import time
import tracemalloc
from collections.abc import Callable
from functools import wraps
from typing import Any


class ProfileResult:
    """Aggregated profiling metrics for a single function."""

    def __init__(self, function_name: str = "") -> None:
        self.function_name: str = function_name
        self.call_count: int = 0
        self.total_cpu_time: float = 0.0
        self.avg_cpu_time: float = 0.0
        self.max_cpu_time: float = 0.0
        self.min_cpu_time: float = 0.0
        self.total_duration: float = 0.0
        self.memory_peak: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize result as a JSON-compatible dictionary.

        Returns:
            Dictionary with all aggregate fields for this function.
        """
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
    """Collect and aggregate profiling metrics for decorated functions.

    Aggregation is guarded by a lock so decorated functions may be called
    from multiple threads without losing updates.
    """

    def __init__(self) -> None:
        self.results: dict[str, ProfileResult] = {}
        self._lock = threading.Lock()
        self._tracemalloc_started: bool = False

    def start_tracemalloc(self) -> None:
        """Begin memory tracking via tracemalloc. Idempotent."""
        if not self._tracemalloc_started:
            tracemalloc.start()
            self._tracemalloc_started = True

    def stop_tracemalloc(self) -> None:
        """Stop memory tracking. Idempotent."""
        if self._tracemalloc_started:
            tracemalloc.stop()
            self._tracemalloc_started = False

    def get_result(self, function_name: str) -> ProfileResult | None:
        """Retrieve aggregated result for a named function.

        Args:
            function_name: Name of the instrumented function.

        Returns:
            The accumulated result, or None if the name was never recorded.
        """
        return self.results.get(function_name)

    def get_all_results(self) -> dict[str, ProfileResult]:
        """Return all collected results keyed by function name."""
        return self.results


def profile(func: Callable[..., Any] | None = None, *, memory: bool = True) -> Any:
    """Decorator that instruments a function with CPU and memory metrics.

    Usable bare (``@profile``) or with options (``@profile(memory=False)``).
    Memory tracking starts automatically on the first instrumented call when
    enabled; tracemalloc adds overhead, so disable it for hot paths where
    only timing matters.

    Args:
        func: The callable to instrument when used bare.
        memory: Track per-call net memory growth via tracemalloc.

    Returns:
        Wrapped function that collects profiling data on each invocation.

    Usage:
        @profile
        def my_function(x: int) -> str:
            return str(x)
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        profiler = Profiler()

        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if memory:
                profiler.start_tracemalloc()

            cpu_start = time.process_time()
            wall_start = time.perf_counter()
            mem_before = tracemalloc.get_traced_memory()[0] if memory else 0

            result = fn(*args, **kwargs)

            duration = time.perf_counter() - wall_start
            cpu_time = time.process_time() - cpu_start

            mem_growth = 0
            if memory:
                mem_after = tracemalloc.get_traced_memory()[0]
                mem_growth = max(0, mem_after - mem_before)

            with profiler._lock:
                existing = profiler.results.get(fn.__name__)
                if existing is None:
                    existing = ProfileResult(fn.__name__)
                    profiler.results[fn.__name__] = existing
                existing.call_count += 1
                existing.total_cpu_time += cpu_time
                existing.avg_cpu_time = existing.total_cpu_time / existing.call_count
                existing.max_cpu_time = max(existing.max_cpu_time, cpu_time)
                if existing.call_count == 1 or cpu_time < existing.min_cpu_time:
                    existing.min_cpu_time = cpu_time
                existing.total_duration += duration
                existing.memory_peak = max(existing.memory_peak, mem_growth)

            return result

        wrapper._profiler = profiler  # type: ignore[attr-defined]
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


def get_profiler_data(func: Callable[..., Any]) -> dict[str, ProfileResult]:
    """Extract profiling data from a decorated function.

    Args:
        func: A function decorated with @profile.

    Returns:
        Dictionary of all collected results for this session. Empty if the
        function was not decorated with @profile.
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
        with profiler._lock:
            profiler.results.clear()
