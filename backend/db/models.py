"""
db/models.py — SQLAlchemy table definitions for VendorLens persistence.

One table: analysis_runs.
  - job_id is the primary key (UUID string from api/main.py)
  - proposals stores list[ProposalState.model_dump()] as JSONB
  - All queryable scalar fields get their own columns; nested data goes in JSONB

The Pydantic models in graph/state.py remain the source of truth for data shape.
These SQLAlchemy models mirror their output — never diverge independently.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from db.session import Base


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    job_id    = Column(String, primary_key=True)
    bundle_id = Column(String, nullable=False)
    status    = Column(String, nullable=False)       # done | error | partial
    created_at = Column(DateTime, default=datetime.utcnow)
    memo      = Column(Text,   nullable=True)
    error     = Column(Text,   nullable=True)
    proposals = Column(JSONB,  nullable=True)        # list[ProposalState.model_dump()]
