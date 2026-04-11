"""Tests for the ResultCache singleton."""

import pytest
from backend.cache import ResultCache, get_result_cache
from backend.models import EvaluationResult


def _make_result(disease: str = "test disease") -> EvaluationResult:
    return EvaluationResult(
        disease_name=disease,
        disease_summary="A test disease.",
        targets=[],
        candidates=[],
        safety_assessments=[],
        contradictions=[],
        evidence_summaries=[],
        data_sources=["TestDB"],
    )


class TestResultCache:
    """Unit tests for the in-process result cache."""

    def test_put_and_get(self):
        cache = ResultCache()
        result = _make_result("Huntington")
        cache.put("Huntington", result)
        assert cache.get("huntington") is result

    def test_get_missing_returns_none(self):
        cache = ResultCache()
        assert cache.get("nonexistent") is None

    def test_case_insensitive_keys(self):
        cache = ResultCache()
        cache.put("ALS", _make_result("ALS"))
        assert cache.get("als") is not None
        assert cache.get("ALS") is not None

    def test_overwrite_existing(self):
        cache = ResultCache()
        cache.put("ALS", _make_result("ALS v1"))
        cache.put("ALS", _make_result("ALS v2"))
        assert len(cache) == 1
        assert cache.get("als").disease_summary == "A test disease."

    def test_max_entries_eviction(self):
        cache = ResultCache(max_entries=3)
        cache.put("a", _make_result("a"))
        cache.put("b", _make_result("b"))
        cache.put("c", _make_result("c"))
        assert len(cache) == 3
        cache.put("d", _make_result("d"))
        assert len(cache) == 3
        assert cache.get("a") is None  # evicted (oldest)
        assert cache.get("d") is not None

    def test_keys(self):
        cache = ResultCache()
        cache.put("Alpha", _make_result())
        cache.put("Beta", _make_result())
        assert set(cache.keys()) == {"alpha", "beta"}

    def test_len(self):
        cache = ResultCache()
        assert len(cache) == 0
        cache.put("x", _make_result())
        assert len(cache) == 1


class TestGetResultCacheSingleton:
    """Verify the module-level singleton pattern."""

    def test_returns_same_instance(self):
        a = get_result_cache()
        b = get_result_cache()
        assert a is b

    def test_instance_is_result_cache(self):
        assert isinstance(get_result_cache(), ResultCache)
