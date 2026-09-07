# Perf Profiler

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)]
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)]

A lightweight profiling tool for Python functions. Decorate a function with
`@profile` and it records CPU time, wall-clock duration, call counts, and net
memory growth per call. A FastAPI service stores the results and streams live
metrics to a dashboard with flame graph bars, hot path ranking, and a memory
trend line.

```
instrument                        store                       visualize
──────────                        ─────                       ───────────
@profile wraps your function      entries persist in          dashboard reads stored
and measures each call:           SQLite / Postgres           data and gets live
CPU time, duration, net              │                         pushes over a
memory growth                        ▼                         WebSocket
   │                              hot paths = CPU share of    (flame graph, hot
   └──────────────────────────────► every stored entry        paths, memory trend)
```

## What it measures

- **CPU time** comes from `time.process_time`, the processor time this process
  actually consumed. That is different from wall-clock duration, which uses
  `time.perf_counter` and includes any waiting. Both are recorded per call and
  aggregated (total, average, min, max).
- **Memory growth** is measured with `tracemalloc` as the change in traced,
  still-allocated bytes across one call. A function that keeps allocating and
  retaining objects shows persistent positive growth on every call, which is
  the shape of a leak. Because tracemalloc tracks the whole process, work done
  by other threads during the same window gets attributed to the running call.
- **Hot paths** are computed from stored entries: each function's share of the
  total recorded CPU time, ranked most expensive first.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Library | stdlib only (`time`, `tracemalloc`, `threading`) |
| Backend | FastAPI + SQLAlchemy + SQLite (Postgres via env) |
| Frontend | HTML/CSS/JS with Canvas API for flame graphs |
| Real-time | WebSocket (server pushes, client listens) |
| Testing | pytest |

## Requirements

- Python 3.10+

Install deps:

```bash
pip install -r requirements.txt
```

## Quickstart

Start the server:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000> for the dashboard. It starts empty, which is
honest: there is no canned data. To fill it with real measured numbers, run
the demo in a second terminal. It profiles a CPU-bound function, a fast one,
and a function that retains objects on every call (a leak shape), then POSTs
the results and memory snapshots to the running server:

```bash
python demo.py
```

## Library usage

The decorator library is stdlib-only, so you can use it in any process without
installing the dashboard backend:

```python
from profiler import get_profiler_data, profile

@profile
def compute(n: int) -> int:
    return sum(range(n))

for _ in range(10):
    compute(10_000)

for name, result in get_profiler_data(compute).items():
    print(result.to_dict())
```

Use `@profile(memory=False)` on hot paths where the tracemalloc overhead is
not worth it.

### API

| Method | Path                      | Returns                                |
|--------|---------------------------|----------------------------------------|
| GET    | `/health`                 | Service status                         |
| GET    | `/api/profiles`           | All stored profile entries             |
| POST   | `/api/profiles`           | Store an aggregated entry              |
| GET    | `/api/hot_paths`          | CPU share ranking, most expensive first |
| GET    | `/api/memory_snapshots`   | All stored memory snapshots            |
| POST   | `/api/memory_snapshots`   | Store a memory snapshot                |
| WS     | `/ws/metrics`             | Live metric summaries (server pushes)  |

### Configuration (environment)

| Variable       | Default                  | Purpose                        |
|----------------|--------------------------|--------------------------------|
| `DATABASE_URL` | local SQLite file        | SQLAlchemy connection string   |

## Docker

```bash
docker compose up --build
```

The app binds `0.0.0.0` inside the container; compose maps the port to the
host's loopback only, so the service stays local.

## Tests

```bash
python -m pytest tests -q
```

The suite covers the library (aggregation math, min/max/avg invariants,
memory growth detection, thread safety) and the API through `TestClient`
(roundtrips, hot path percentages, payload validation, WebSocket broadcast,
frontend serving). It uses temporary databases, so nothing on your machine is
touched.

## Honest limitations

- **In-process only.** This instruments functions inside a Python process you
  run. It does not attach to or profile other running processes.
- **Heuristic memory attribution.** Per-call net growth is a process-wide
  tracemalloc measurement, so concurrent threads can skew it. It is good at
  spotting the leak shape (steady positive growth per call), not at exact
  per-object accounting.
- **No call graph.** The flame graph is a bar chart of CPU time per function,
  not a nested call tree. There is no parent/child relationship tracking.
- **Coarse CPU clock on Windows.** `time.process_time` ticks at roughly
  15 ms on many Windows builds, so short calls can report zero CPU time even
  though their wall-clock duration is recorded correctly. Longer or repeated
  calls accumulate real values; on Linux and macOS the resolution is
  nanoseconds.

## Development Conventions

- Type hints on all public functions and methods
- Google-style docstrings
- ruff + mypy linting (`ruff check .`, `mypy backend/ tests/ profiler.py`)
- Private repos only until explicitly approved

## License

MIT, see [LICENSE](LICENSE).
