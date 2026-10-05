"""Tests for extraction SHA-256 caching and persistence."""

from pathlib import Path

from careercompiler.extraction.base import compute_extraction_cache_key
from careercompiler.extraction.cache import ExtractionCache
from careercompiler.extraction.models import ExtractedJD


def test_cache_key_determinism() -> None:
    text = "Software Engineer Job Description"
    key1 = compute_extraction_cache_key(text, "LocalRuleExtractor", "1.0.0")
    key2 = compute_extraction_cache_key(text, "LocalRuleExtractor", "1.0.0")
    assert key1 == key2

    # Different version produces different key
    key_diff_version = compute_extraction_cache_key(text, "LocalRuleExtractor", "2.0.0")
    assert key1 != key_diff_version

    # Config variation produces different key
    key_config = compute_extraction_cache_key(text, "LocalRuleExtractor", "1.0.0", config={"opt": True})
    assert key1 != key_config


def test_extraction_cache_memory_and_disk(tmp_path: Path) -> None:
    cache = ExtractionCache(cache_dir=tmp_path)
    sample_key = "test_key_123"

    assert cache.get(sample_key) is None

    extracted = ExtractedJD(
        role_title="Backend Developer",
        extractor_name="LocalRuleExtractor",
        extractor_version="1.0.0",
        cache_key=sample_key,
    )

    cache.set(sample_key, extracted)

    # In-memory retrieval
    cached = cache.get(sample_key)
    assert cached is not None
    assert cached.role_title == "Backend Developer"

    # Disk file was written
    disk_file = tmp_path / f"{sample_key}.json"
    assert disk_file.exists()

    # Clear memory cache and re-read from disk
    cache.clear()
    assert len(cache._memory_cache) == 0
    from_disk = cache.get(sample_key)
    assert from_disk is not None
    assert from_disk.role_title == "Backend Developer"
