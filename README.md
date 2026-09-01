# Real-time Performance Profiler

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)]
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)]

A lightweight profiling service that instruments running Python processes, collects CPU/memory/duration metrics per function call, and streams results to a real-time dashboard showing flame graphs, hot paths, memory allocation trends — all live as the application runs.

## Features
- Decorator-based instrumentation for Python functions/methods
- Live metric collection: CPU time, execution duration, function call counts, memory usage
- Real-time dashboard with flame graphs updating via WebSocket
- Hot path detection automatically identifies slowest/most-called functions
- Memory profiling tracks allocation patterns and detects leaks

## Tech Stack
| Component | Technology |
|-----------|------------|
| Backend | FastAPI + SQLAlchemy + SQLite |
| Frontend | HTML/CSS/JS with Canvas API for flame graphs |
| Profiling | cProfile wrapper / custom decorator instrumentation |
| Real-time | WebSocket (websockets library) |
| Testing | pytest (≥80% coverage target) |

## Development Conventions
- Private repos only until explicitly approved
- Concise commit messages describing WHAT changed
- Frequent small commits for activity tracking
- Type hints on all public functions/methods
- Google-style docstrings
- ruff + mypy linting/formatting

## Scope Boundaries
✅ Decorator-based instrumentation, real-time metric collection and streaming via WebSocket, dashboard with flame graphs. ❌ No cloud deployment until approved.
