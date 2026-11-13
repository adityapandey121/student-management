"""Student storage backends: in-memory (default) or Redis (when REDIS_URL is set)."""
from __future__ import annotations

import json
import logging
import os
from urllib.parse import urlsplit

log = logging.getLogger(__name__)


class DuplicateStudentError(Exception):
    pass


class MemoryStore:
    name = "memory"
    target = "in-process"
    last_error = None

    def __init__(self) -> None:
        self._students: dict[str, dict] = {}

    def ping(self) -> bool:
        return True

    def add(self, student: dict) -> None:
        if student["id"] in self._students:
            raise DuplicateStudentError(student["id"])
        self._students[student["id"]] = student

    def get(self, student_id: str) -> dict | None:
        return self._students.get(student_id)

    def all(self) -> list[dict]:
        return sorted(self._students.values(), key=lambda s: s["id"])

    def delete(self, student_id: str) -> bool:
        return self._students.pop(student_id, None) is not None

    def count(self) -> int:
        return len(self._students)


class RedisStore:
    """Stores every student as a JSON string in one Redis hash."""

    name = "redis"
    KEY = "students"

    def __init__(self, url: str) -> None:
        import redis  # imported lazily so tests and the CLI don't need Redis

        parts = urlsplit(url)
        # Never log the password: show only host, port and database.
        self.target = f"{parts.hostname}:{parts.port or 6379}{parts.path}"
        self.last_error = None
        self._redis = redis.Redis.from_url(url, decode_responses=True, socket_timeout=2)

    def ping(self) -> bool:
        try:
            ok = bool(self._redis.ping())
            self.last_error = None
            return ok
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            log.error("Redis at %s is unreachable: %s", self.target, self.last_error)
            return False

    def add(self, student: dict) -> None:
        if not self._redis.hsetnx(self.KEY, student["id"], json.dumps(student)):
            raise DuplicateStudentError(student["id"])

    def get(self, student_id: str) -> dict | None:
        raw = self._redis.hget(self.KEY, student_id)
        return json.loads(raw) if raw else None

    def all(self) -> list[dict]:
        students = [json.loads(v) for v in self._redis.hvals(self.KEY)]
        return sorted(students, key=lambda s: s["id"])

    def delete(self, student_id: str) -> bool:
        return bool(self._redis.hdel(self.KEY, student_id))

    def count(self) -> int:
        return int(self._redis.hlen(self.KEY))


def store_from_env() -> MemoryStore | RedisStore:
    url = os.environ.get("REDIS_URL", "").strip()
    return RedisStore(url) if url else MemoryStore()
