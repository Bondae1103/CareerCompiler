"""Full ACTR decomposition engine for resume accomplishments."""

import hashlib
from functools import lru_cache

from careercompiler.decomposition.metrics import (
    classify_metric_quality,
    extract_impact_metrics,
)
from careercompiler.decomposition.models import (
    BulletDecomposition,
    DomainConcept,
)
from careercompiler.decomposition.verbs import extract_action_verb
from careercompiler.models.profile import Profile
from careercompiler.taxonomy.normalizer import TaxonomyNormalizer, get_default_normalizer


def compute_bullet_cache_key(text: str) -> str:
    """Calculate deterministic SHA-256 hash for bullet text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class BulletDecomposer:
    """Decomposes resume bullet variants into structured ACTR components."""

    def __init__(self, normalizer: TaxonomyNormalizer | None = None) -> None:
        self.normalizer = normalizer or get_default_normalizer()
        self._cache: dict[str, BulletDecomposition] = {}

    def decompose(self, bullet_text: str) -> BulletDecomposition:
        """Decompose a single authored bullet variant into its ACTR components."""
        cleaned = bullet_text.strip()
        cache_key = compute_bullet_cache_key(cleaned)

        if cache_key in self._cache:
            return self._cache[cache_key]

        # 1. Action Verb
        verb = extract_action_verb(cleaned)

        # 2. Technologies (via Tier 2 Entity Gazetteer)
        tech_matches = self.normalizer.normalize(cleaned)

        # 3. Impact Metrics (deterministic parser)
        metrics = extract_impact_metrics(cleaned)

        # 4. Metric Quality
        quality = classify_metric_quality(cleaned, metrics)

        # 5. Evidenced Domain Concepts & Canonical Tags
        canonical_tags: list[str] = []
        for t in tech_matches:
            if t.canonical_id not in canonical_tags:
                canonical_tags.append(t.canonical_id)

        # Evidenced non-tech concepts
        domain_concepts: list[DomainConcept] = []

        decomposition = BulletDecomposition(
            raw_text=cleaned,
            action_verb=verb,
            technologies=tech_matches,
            domain_concepts=domain_concepts,
            impact_metrics=metrics,
            metric_quality=quality,
            canonical_tags=canonical_tags,
            cache_key=cache_key,
        )

        self._cache[cache_key] = decomposition
        return decomposition

    def decompose_profile(self, profile: Profile) -> dict[str, BulletDecomposition]:
        """Decompose every authored bullet variant across experiences and projects in a Profile."""
        results: dict[str, BulletDecomposition] = {}

        for exp in profile.experiences:
            for slot in exp.slots:
                for variant in slot.variants:
                    results[variant.id] = self.decompose(variant.text)

        for proj in profile.projects:
            for slot in proj.slots:
                for variant in slot.variants:
                    results[variant.id] = self.decompose(variant.text)

        return results


@lru_cache(maxsize=1)
def get_default_decomposer() -> BulletDecomposer:
    """Return a process-wide cached BulletDecomposer."""
    return BulletDecomposer()


def decompose_bullet(bullet_text: str) -> BulletDecomposition:
    """Convenience function to decompose a bullet using the default decomposer."""
    return get_default_decomposer().decompose(bullet_text)
