"""
db/session.py — SQLAlchemy engine and session factory.

Persistence is optional: if DATABASE_URL is not set the entire layer is a no-op.
No code outside this module needs to check for the env var — get_db_session()
returns None when no DB is configured, and callers treat None as "skip persist".
"""

import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

logger = logging.getLogger(__name__)

_DATABASE_URL = os.getenv("DATABASE_URL")
_engine = None
_SessionLocal = None


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create all tables if DATABASE_URL is configured. Called once at API startup."""
    if not _DATABASE_URL:
        return
    from db.models import AnalysisRun  # noqa: F401 — ensures model is registered
    engine = _get_engine()
    if engine:
        Base.metadata.create_all(engine)
        logger.info("DB tables verified/created at %s", _DATABASE_URL.split("@")[-1])


def _get_engine():
    global _engine
    if _engine is None and _DATABASE_URL:
        _engine = create_engine(_DATABASE_URL, pool_pre_ping=True)
    return _engine


def get_db_session():
    """Return a new SQLAlchemy session, or None if DATABASE_URL is not set."""
    global _SessionLocal
    engine = _get_engine()
    if engine is None:
        return None
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=engine)
    return _SessionLocal()
