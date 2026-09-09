"""Demo: instrument real functions and push measured results to the dashboard.

Run the server first (``uvicorn backend.main:app --port 8000``), then run
this script. It profiles a CPU-bound function, a fast one, and a function
that retains objects on every call (a leak shape), stores memory snapshots
along the way, and POSTs everything to the running API so the dashboard
shows real measured data instead of an empty chart.

Usage:
    python demo.py [--url http://127.0.0.1:8000]
"""

from __future__ import annotations

import argparse
import json
import time
import tracemalloc
import urllib.error
import urllib.request

from profiler import get_profiler_data, profile

# Module-level cache that never evicts: the leak the demo is meant to show.
_leak_cache: list[bytes] = []


@profile
def fibonacci(n: int) -> int:
    """Recursively compute the nth Fibonacci number (CPU-bound work)."""
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


@profile
def fast_lookup(key: str) -> str:
    """Do trivial work; should show up as a cold path."""
    return key.upper()


@profile
def leaky_loader(payload_size: int) -> bytes:
    """Read a payload and retain it forever, one allocation per call."""
    payload = bytearray(payload_size).hex().encode()
    _leak_cache.append(payload)
    return payload


def collect_memory_snapshot() -> dict[str, int]:
    """Sample the process's traced memory at one point in time.

    Returns:
        Dictionary with current_bytes, peak_bytes, and allocation_count.
    """
    current, peak = tracemalloc.get_traced_memory()
    snapshot = tracemalloc.take_snapshot()
    allocation_count = sum(stat.count for stat in snapshot.statistics("traceback"))
    return {"current_bytes": current, "peak_bytes": peak, "allocation_count": allocation_count}


def server_reachable(url: str) -> bool:
    """Check the health endpoint. Returns True when the server answers."""
    try:
        with urllib.request.urlopen(f"{url}/health", timeout=5) as response:
            return 200 <= response.status < 300
    except urllib.error.URLError:
        return False


def post_json(url: str, payload: dict) -> bool:
    """POST a JSON payload to the API. Returns True on success."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return 200 <= response.status < 300
    except urllib.error.URLError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url", default="http://127.0.0.1:8000", help="Base URL of the running server"
    )
    args = parser.parse_args()

    # Warm up each function a few times so the aggregates mean something.
    for _ in range(3):
        fibonacci(24)
    for i in range(50):
        fast_lookup(f"key-{i}")
    for _ in range(20):
        leaky_loader(64 * 1024)

    # Map the library's aggregate fields onto the API's field names.
    payload_rows: list[dict] = []
    for func in (fibonacci, fast_lookup, leaky_loader):
        data = get_profiler_data(func)
        for result in data.values():
            d = result.to_dict()
            payload_rows.append(
                {
                    "function_name": d["function_name"],
                    "cpu_time": d["total_cpu_time"],
                    "duration": d["total_duration"],
                    "call_count": d["call_count"],
                    "memory_peak_bytes": d["memory_peak"],
                }
            )

    snapshot_rows: list[dict] = []
    for _ in range(5):
        snapshot_rows.append(collect_memory_snapshot())
        time.sleep(0.4)

    if not server_reachable(args.url):
        print(f"Server not reachable at {args.url}; printing payloads instead.")
        print(json.dumps({"profiles": payload_rows, "snapshots": snapshot_rows}, indent=2))
        return 1

    failures = 0
    for row in payload_rows:
        if not post_json(f"{args.url}/api/profiles", row):
            failures += 1
    for row in snapshot_rows:
        if not post_json(f"{args.url}/api/memory_snapshots", row):
            failures += 1

    print("Pushed measured data to the dashboard:")
    for row in payload_rows:
        print(
            f"  {row['function_name']}: {row['call_count']} calls, "
            f"{row['cpu_time']:.4f}s CPU, "
            f"peak net growth {row['memory_peak_bytes']} bytes"
        )
    print(f"  memory snapshots: {len(snapshot_rows)}")
    if failures:
        print(f"WARNING: {failures} request(s) failed; the server may be down.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
