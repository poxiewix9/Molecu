"""Thread-safe in-process result cache.

Provides a singleton ResultCache so endpoint modules don't import
mutable state directly from main.py. FastAPI dependency injection
fetches the cache via ``get_result_cache()``.
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models import EvaluationResult

log = logging.getLogger(__name__)

_lock = threading.Lock()


class ResultCache:
    """Simple in-process cache keyed by disease name (lowercased).

    Thread-safe via a reentrant lock so multiple concurrent requests
    can safely read/write without data races.
    """

    def __init__(self, max_entries: int = 50) -> None:
        self._store: dict[str, EvaluationResult] = {}
        self._max = max_entries

    def get(self, disease_name: str) -> EvaluationResult | None:
        with _lock:
            return self._store.get(disease_name.lower())

    def put(self, disease_name: str, result: EvaluationResult) -> None:
        with _lock:
            key = disease_name.lower()
            if len(self._store) >= self._max and key not in self._store:
                oldest = next(iter(self._store))
                del self._store[oldest]
                log.info("Cache evicted oldest entry: %s", oldest)
            self._store[key] = result

    def keys(self) -> list[str]:
        with _lock:
            return list(self._store.keys())

    def __len__(self) -> int:
        with _lock:
            return len(self._store)


_instance: ResultCache | None = None


def get_result_cache() -> ResultCache:
    """Return the global ResultCache singleton (created on first call)."""
    global _instance
    if _instance is None:
        _instance = ResultCache()
    return _instance
