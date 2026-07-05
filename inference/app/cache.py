"""
Phase 5 — Redis cache
Holds ONLY the latest metric snapshot per job, key = "latest:{job_id}".
Set REDIS_URL env var, or defaults to local Redis started via:
    docker run -d -p 6379:6379 redis:7
"""

import os
import json
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_client = redis.from_url(REDIS_URL, decode_responses=True)

SNAPSHOT_TTL_SECONDS = 60 * 60  # expire stale snapshots after 1hr, avoids unbounded growth


def set_snapshot(job_id: str, payload: dict):
    _client.set(f"latest:{job_id}", json.dumps(payload), ex=SNAPSHOT_TTL_SECONDS)


def get_snapshot(job_id: str) -> dict | None:
    raw = _client.get(f"latest:{job_id}")
    return json.loads(raw) if raw else None