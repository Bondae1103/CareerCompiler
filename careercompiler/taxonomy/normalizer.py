"""Normalizer API for canonical entity resolution and document text normalization."""

from functools import lru_cache
from pathlib import Path

from careercompiler.taxonomy.ingest import load_seed_taxonomy
from careercompiler.taxonomy.matcher import BoundarySafeMatcher
from careercompiler.taxonomy.models import (
    EntityMatch,
    TaxonomyCatalog,
    TaxonomyEntity,
)


class TaxonomyNormalizer:
    """High-level normalizer providing entity extraction and canonicalization."""

    def __init__(
        self,
        catalog: TaxonomyCatalog | None = None,
        seed_path: Path | str | None = None,
    ) -> None:
        if catalog is not None:
            self.catalog = catalog
        else:
            self.catalog = load_seed_taxonomy(seed_path)

        self.matcher = BoundarySafeMatcher(self.catalog)

    def normalize(self, text: str) -> list[EntityMatch]:
        """Extract all boundary-safe, disambiguated canonical entity matches in text."""
        return self.matcher.match(text)

    def canonicalize(self, term: str) -> str | None:
        """Resolve a single technology term or alias to its canonical_id."""
        return self.catalog.canonicalize(term)

    def get_entity(self, canonical_id: str) -> TaxonomyEntity | None:
        """Lookup full taxonomy entity record by canonical ID."""
        return self.catalog.get_by_id(canonical_id)


@lru_cache(maxsize=1)
def get_default_normalizer() -> TaxonomyNormalizer:
    """Return a process-wide cached TaxonomyNormalizer using the seed catalog."""
    return TaxonomyNormalizer()


def normalize(text: str) -> list[EntityMatch]:
    """Convenience function to extract entity matches using the default normalizer."""
    return get_default_normalizer().normalize(text)


def canonicalize(term: str) -> str | None:
    """Convenience function to canonicalize a term using the default normalizer."""
    return get_default_normalizer().canonicalize(term)
