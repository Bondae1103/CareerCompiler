"""Tests verifying the Explainability Invariant: all scores sum from components."""

from careercompiler.decomposition.models import MetricQuality
from careercompiler.extraction.models import (
    ExtractedJD,
    ExtractedRequirement,
    RequirementCategory,
)
from careercompiler.scoring.models import ScorableBullet
from careercompiler.scoring.scorer import ResumeScorer


def test_explainability_on_synthetic_configurations() -> None:
    """Verify that score breakdown components always sum to total_score."""
    scorer = ResumeScorer()

    bullets = [
        ScorableBullet(
            id="b1",
            text="Engineered Python microservices.",
            canonical_tags=["python"],
            metric_quality=MetricQuality.QUANTIFIED,
        ),
        ScorableBullet(
            id="b2",
            text="Optimized database queries.",
            canonical_tags=["postgresql"],
            metric_quality=MetricQuality.VAGUE,
        ),
    ]

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
        category=RequirementCategory.NICE_TO_HAVE,
    )
    jd = ExtractedJD(
        role_title="Backend Developer",
        hard_requirements=[r1],
        preferred_qualifications=[r2],
        scale_indicators=[],
        dropped_items_count=0,
        validation_warnings=[],
        extractor_name="test",
        extractor_version="1.0.0",
        cache_key="test_key",
    )

    breakdown = scorer.score_selection(bullets, jd)

    c = breakdown.component_contributions
    expected_sum = round(c["lexical"] + c["bm25"] + c["semantic"] + c["quality"], 4)
    assert breakdown.total_score == expected_sum

    # Check component calculations match weights
    comb = scorer.config.combiner
    assert c["lexical"] == round(comb.weight_lexical * breakdown.lexical_score, 4)
    assert c["bm25"] == round(comb.weight_bm25 * breakdown.bm25_score, 4)
    assert c["semantic"] == round(comb.weight_semantic * breakdown.semantic_score, 4)
    assert c["quality"] == round(comb.weight_quality * breakdown.quality_score, 4)


def test_explainability_on_empty_and_full_selections() -> None:
    """Verify Explainability invariant on edge cases: 0 bullets and empty JD."""
    scorer = ResumeScorer()
    empty_jd = ExtractedJD(
        role_title="General",
        hard_requirements=[],
        preferred_qualifications=[],
        scale_indicators=[],
        dropped_items_count=0,
        validation_warnings=[],
        extractor_name="test",
        extractor_version="1.0.0",
        cache_key="test_empty",
    )

    # 1. Empty bullets, empty JD
    b_empty = scorer.score_selection([], empty_jd)
    assert b_empty.total_score == round(sum(b_empty.component_contributions.values()), 4)

    # 2. Some bullets, empty JD
    bullets = [ScorableBullet(id="b1", text="Python bullet", canonical_tags=["python"])]
    b_bullets_empty_jd = scorer.score_selection(bullets, empty_jd)
    assert b_bullets_empty_jd.total_score == round(sum(b_bullets_empty_jd.component_contributions.values()), 4)


def test_bullet_utility_breakdown() -> None:
    """Verify bullet utility calculation and explanation."""
    scorer = ResumeScorer()
    r1 = ExtractedRequirement(
        id="r1",
        canonical_id="python",
        surface_form="Python",
        evidence_span=(0, 6),
        evidence_text="Python",
        category=RequirementCategory.MUST_HAVE,
    )
    jd = ExtractedJD(
        role_title="Backend Engineer",
        hard_requirements=[r1],
        preferred_qualifications=[],
        scale_indicators=[],
        dropped_items_count=0,
        validation_warnings=[],
        extractor_name="test",
        extractor_version="1.0.0",
        cache_key="test_key",
    )
    b = ScorableBullet(
        id="b_test",
        text="Architected FastAPI microservices with sub-50ms latency.",
        canonical_tags=["fastapi", "python"],
        metric_quality=MetricQuality.QUANTIFIED,
        lines=2,
    )

    utility = scorer.score_bullet_utility(b, jd)
    assert utility.bullet_id == "b_test"
    assert len(utility.matched_requirements) >= 1
    assert utility.quality_bonus > 0.0
    assert utility.line_penalty > 0.0  # lines=2 -> overflow penalty
    assert "Utility" in utility.explanation
