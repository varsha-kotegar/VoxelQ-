"""
Phase 5 — DB setup
Set DATABASE_URL env var, or defaults to local Postgres started via:
    docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=voxelq -e POSTGRES_DB=voxelq postgres:16
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:voxelq@localhost:5432/voxelq",
)
# Managed Postgres providers (e.g. Render, Heroku) may supply postgres://,
# which SQLAlchemy 2.0 rejects unless normalized to postgresql://.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db():
    """Call once at startup — creates tables if they don't exist."""
    from app import models  # noqa: F401  (import so models register on Base.metadata)
    Base.metadata.create_all(bind=engine)


def get_session():
    """Each background job thread should call this to get its OWN session
    (SQLAlchemy sessions are not thread-safe to share)."""
    return SessionLocal()