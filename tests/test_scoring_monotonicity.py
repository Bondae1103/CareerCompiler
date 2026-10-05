"""Monotonicity and submodularity tests for lexical requirement coverage scoring."""

import pytest

from careercompiler.extraction.models import (
    ExtractedJD,
    ExtractedRequirement,
    RequirementCategory,
)
from careercompiler.scoring.lexical import LexicalScorer
from careercompiler.scoring.models import ScorableBullet


@pytest.fixture
def sample_jd() -> ExtractedJD:
    r1 = ExtractedRequirement(
        id="r1",
        canonical_id="python",
        surface_form="Python",
        evidence_span=(0, 6),
        evidence_text="Python",
        category=RequirementCategory.MUST_HAVE,
    )
    r2 = ExtractedRequirement(
        id="r2",
        canonical_id="docker",
        surface_form="Docker",
        evidence_span=(7, 13),
        evidence_text="Docker",
        category=RequirementCategory.MUST_HAVE,
    )
    r3 = ExtractedRequirement(
        id="r3",
        canonical_id="kubernetes",
        surface_form="Kubernetes",
        evidence_span=(14, 24),
        evidence_text="Kubernetes",
        category=RequirementCategory.NICE_TO_HAVE,
    )
    r4 = ExtractedRequirement(
        id="r4",
        canonical_id="postgresql",
        surface_form="PostgreSQL",
        evidence_span=(25, 35),
        evidence_text="PostgreSQL",
        category=RequirementCategory.NICE_TO_HAVE,
    )
    return ExtractedJD(
        role_title="Senior Backend Engineer",
        hard_requirements=[r1, r2],
        preferred_qualifications=[r3, r4],
        scale_indicators=[],
        dropped_items_count=0,
        validation_warnings=[],
        extractor_name="test",
        extractor_version="1.0.0",
        cache_key="test_cache_key",
    )


def test_monotonicity_on_adding_new_coverage(sample_jd: ExtractedJD) -> None:
    """Adding bullets covering new requirements strictly increases or preserves the score."""
    scorer = LexicalScorer()

    b1 = ScorableBullet(id="b1", text="Python bullet", canonical_tags=["python"])
    b2 = ScorableBullet(id="b2", text="Docker bullet", canonical_tags=["docker"])
    b3 = ScorableBullet(id="b3", text="Kubernetes bullet", canonical_tags=["kubernetes"])

    score_empty = scorer.score_coverage([], sample_jd).score
    assert score_empty == 0.0

    score_1 = scorer.score_coverage([b1], sample_jd).score
    assert score_1 > score_empty

    score_2 = scorer.score_coverage([b1, b2], sample_jd).score
    assert score_2 > score_1

    score_3 = scorer.score_coverage([b1, b2, b3], sample_jd).score
    assert score_3 > score_2


def test_duplicate_bullets_add_zero_marginal_delta(sample_jd: ExtractedJD) -> None:
    """Adding redundant bullets with already covered tags adds exactly zero score."""
    scorer = LexicalScorer()

    b1 = ScorableBullet(id="b1", text="Python bullet 1", canonical_tags=["python"])
    b1_dup = ScorableBullet(id="b1_dup", text="Python bullet 2", canonical_tags=["python"])

    initial_res = scorer.score_coverage([b1], sample_jd)
    combined_res = scorer.score_coverage([b1, b1_dup], sample_jd)

    assert combined_res.score == initial_res.score
    assert scorer.marginal_delta(b1_dup, [b1], sample_jd) == 0.0


def test_unrelated_bullet_adds_zero(sample_jd: ExtractedJD) -> None:
    """Adding a bullet with irrelevant skills adds zero points and does not lower score."""
    scorer = LexicalScorer()

    b1 = ScorableBullet(id="b1", text="Python bullet", canonical_tags=["python"])
    b_unrelated = ScorableBullet(id="b_unrelated", text="Ruby bullet", canonical_tags=["ruby"])

    base_score = scorer.score_coverage([b1], sample_jd).score
    with_unrelated_score = scorer.score_coverage([b1, b_unrelated], sample_jd).score

    assert with_unrelated_score == base_score
    assert with_unrelated_score >= base_score
