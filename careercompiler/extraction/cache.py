"""Cache store for extracted Job Description chunks."""

import json
from pathlib import Path

from careercompiler.extraction.models import ExtractedJD


class ExtractionCache:
    """Deterministic local cache for extracted JD chunks."""

    def __init__(self, cache_dir: Path | str | None = None) -> None:
        self._memory_cache: dict[str, ExtractedJD] = {}
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, cache_key: str) -> ExtractedJD | None:
        """Retrieve cached extraction by cache key."""
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, encoding="utf-8") as f:
                        data = json.load(f)
                    extracted = ExtractedJD.model_validate(data)
                    self._memory_cache[cache_key] = extracted
                    return extracted
                except Exception:
                    return None

        return None

    def set(self, cache_key: str, extracted: ExtractedJD) -> None:
        """Store extraction into in-memory and disk cache."""
        self._memory_cache[cache_key] = extracted

        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(extracted.model_dump(), f, indent=2)
            except Exception:
                pass

    def clear(self) -> None:
        """Clear all in-memory entries."""
        self._memory_cache.clear()
