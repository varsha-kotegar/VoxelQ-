"""
Phase 5 — SQLAlchemy models
video_jobs (1) --- (many) metrics
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base


def utcnow():
    return datetime.now(timezone.utc)


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id = Column(String, primary_key=True)          # job_id (uuid string)
    source = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending|running|completed|error
    created_at = Column(DateTime, default=utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

    metrics = relationship("Metric", back_populates="job", cascade="all, delete-orphan")


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, ForeignKey("video_jobs.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=utcnow)
    occupancy = Column(Integer)
    avg_occupancy = Column(Float)
    arrival_rate_per_min = Column(Float)
    wait_time_seconds = Column(Float, nullable=True)
    density_band = Column(String)

    job = relationship("VideoJob", back_populates="metrics")