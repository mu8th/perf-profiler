"""Database initialization and session management for the performance profiler.

The default store is a local SQLite file at the repository root. Set the
``DATABASE_URL`` environment variable to point at another database, for
example Postgres in Docker Compose.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

DEFAULT_DATABASE_URL = f"sqlite:///{Path(__file__).resolve().parent.parent / 'perf_profiler.db'}"

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def init_db(database_url: str | None = None) -> Engine:
    """Create the engine and tables. Idempotent; safe to call repeatedly.

    Args:
        database_url: SQLAlchemy connection string. Falls back to the
            DATABASE_URL environment variable, then the local SQLite default.

    Returns:
        The configured engine.
    """
    global _engine, _session_factory
    if _engine is not None and database_url is None:
        return _engine

    url = database_url or os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    kwargs: dict[str, object] = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    _engine = create_engine(url, **kwargs)
    Base.metadata.create_all(_engine)
    _session_factory = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


@contextmanager
def get_session() -> Iterator[Session]:
    """Provide a database session, closing it when the block exits.

    Usage:
        with get_session() as session:
            ...

    Yields:
        A bound Session. Initializes the database on first use.
    """
    if _session_factory is None:
        init_db()
    assert _session_factory is not None
    session = _session_factory()
    try:
        yield session
    finally:
        session.close()
