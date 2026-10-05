"""Base interfaces and protocols for Job Description semantic extractors."""

import hashlib
import json
from abc import ABC, abstractmethod
from typing import Any

from careercompiler.extraction.models import ExtractedJD
from careercompiler.parsing.models import ParsedDocument


def compute_extraction_cache_key(
    jd_text: str,
    extractor_name: str,
    extractor_version: str,
    config: dict[str, Any] | None = None,
) -> str:
    """Calculate deterministic SHA-256 hash identifying JD text and extractor configuration."""
    hasher = hashlib.sha256()
    hasher.update(jd_text.encode("utf-8"))
    hasher.update(b"::")
    hasher.update(extractor_name.encode("utf-8"))
    hasher.update(b"::")
    hasher.update(extractor_version.encode("utf-8"))
    if config:
        config_bytes = json.dumps(config, sort_keys=True).encode("utf-8")
        hasher.update(b"::")
        hasher.update(config_bytes)
    return hasher.hexdigest()


class BaseJDExtractor(ABC):
    """Abstract base class for all Job Description extractors."""

    def __init__(self, name: str, version: str = "1.0.0") -> None:
        self.name = name
        self.version = version

    @abstractmethod
    def extract(
        self,
        jd_text: str,
        document_tree: ParsedDocument | None = None,
    ) -> ExtractedJD:
        """Extract structured JD chunk from raw text and optional pre-parsed document tree."""
        raise NotImplementedError

    def get_cache_key(self, jd_text: str, config: dict[str, Any] | None = None) -> str:
        """Compute the deterministic cache key for the given JD text."""
        return compute_extraction_cache_key(
            jd_text=jd_text,
            extractor_name=self.name,
            extractor_version=self.version,
            config=config,
        )
