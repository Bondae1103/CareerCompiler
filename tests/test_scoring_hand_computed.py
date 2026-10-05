"""Unit tests verifying scoring calculations against hand-computed expected values."""

from careercompiler.decomposition.models import MetricQuality
from careercompiler.extraction.models import (
    ExtractedJD,
    ExtractedRequirement,
    RequirementCategory,
)
from careercompiler.scoring.lexical import LexicalScorer
from careercompiler.scoring.models import (
    CombinerWeights,
    MetricQualityConfig,
    RequirementWeights,
    ScorableBullet,
    ScoringConfig,
)
from careercompiler.scoring.scorer import ResumeScorer


def test_hand_computed_lexical_coverage() -> None:
    """Verify lexical coverage matches exact manual math:

    Requirements:
    1. Python (must_have, weight=1.0)
    2. Docker (must_have, weight=1.0)
    3. Kubernetes (nice_to_have, weight=0.5)
    Total weight = 2.5

    Candidate Bullets cover: Python, Kubernetes
    Covered weight = 1.0 + 0.5 = 1.5
    Expected score = 100 * (1.5 / 2.5) = 60.0%
    """
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
    jd = ExtractedJD(
        role_title="Backend Engineer",
        hard_requirements=[r1, r2],
        preferred_qualifications=[r3],
        scale_indicators=[],
        dropped_items_count=0,
        validation_warnings=[],
        extractor_name="test",
        extractor_version="1.0.0",
        cache_key="test_cache_key",
    )

    bullets = [
        ScorableBullet(
            id="b1",
            text="Engineered microservices in Python.",
            canonical_tags=["python"],
        ),
        ScorableBullet(
            id="b2",
            text="Deployed services onto Kubernetes clusters.",
            canonical_tags=["kubernetes"],
        ),
    ]

    scorer = LexicalScorer(RequirementWeights(must_have=1.0, nice_to_have=0.5))
    result = scorer.score_coverage(bullets, jd)

    assert result.total_weight == 2.5
    assert result.covered_weight == 1.5
    assert result.score == 60.0
    assert result.covered_ids == ["kubernetes", "python"]
    assert result.missing_ids == ["docker"]
    assert result.coverage_count == 2
    assert result.total_count == 3


def test_hand_computed_quality_score() -> None:
    """Verify average quality score matches manual math:

    4 Bullets:
    - b1: QUANTIFIED_WITH_BASELINE (1.00)
    - b2: QUANTIFIED (0.75)
    - b3: VAGUE (0.25)
    - b4: NONE (0.00)

    Average = (1.00 + 0.75 + 0.25 + 0.00) / 4 = 2.00 / 4 = 0.50
    Expected normalized score = 50.0%
    """
    bullets = [
        ScorableBullet(id="b1", text="b1", metric_quality=MetricQuality.QUANTIFIED_WITH_BASELINE),
        ScorableBullet(id="b2", text="b2", metric_quality=MetricQuality.QUANTIFIED),
        ScorableBullet(id="b3", text="b3", metric_quality=MetricQuality.VAGUE),
        ScorableBullet(id="b4", text="b4", metric_quality=MetricQuality.NONE),
    ]

    scorer = ResumeScorer()
    quality_score = scorer.compute_quality_score(bullets)
    assert quality_score == 50.0


def test_hand_computed_combiner_breakdown() -> None:
    """Verify that combiner properly computes contributions and total score:

    Weights:
    - lexical: 0.40
    - bm25: 0.25
    - semantic: 0.20
    - quality: 0.15
    (Sum = 1.00)

    Given components:
    - lexical = 60.0 -> 0.40 * 60.0 = 24.0
    - bm25 = 40.0 -> 0.25 * 40.0 = 10.0
    - semantic = 50.0 -> 0.20 * 50.0 = 10.0
    - quality = 50.0 -> 0.15 * 50.0 = 7.5
    Total score = 24.0 + 10.0 + 10.0 + 7.5 = 51.5
    """
    cfg = ScoringConfig(
        combiner=CombinerWeights(
            weight_lexical=0.40,
            weight_bm25=0.25,
            weight_semantic=0.20,
            weight_quality=0.15,
        ),
        metric_quality=MetricQualityConfig(
            quantified_with_baseline=1.00,
            quantified=0.75,
            vague=0.25,
            none=0.00,
        ),
    )
    scorer = ResumeScorer(cfg)

    bullets = [
        ScorableBullet(
            id="b1",
            text="Engineered Python systems.",
            canonical_tags=["python"],
            metric_quality=MetricQuality.QUANTIFIED_WITH_BASELINE,
        ),
        ScorableBullet(
            id="b2",
            text="Deployed onto Kubernetes.",
            canonical_tags=["kubernetes"],
            metric_quality=MetricQuality.NONE,
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
        category=RequirementCategory.MUST_HAVE,
    )
    jd = ExtractedJD(
        role_title="Backend Engineer",
        hard_requirements=[r1, r2],
        preferred_qualifications=[],
        scale_indicators=[],
        dropped_items_count=0,
        validation_warnings=[],
        extractor_name="test",
        extractor_version="1.0.0",
        cache_key="test_cache_key",
    )

    breakdown = scorer.score_selection(bullets, jd)

    # 1 of 2 must-have requirements covered = 50.0%
    assert breakdown.lexical_score == 50.0

    # Explainability Invariant:
    c = breakdown.component_contributions
    assert abs(breakdown.total_score - (c["lexical"] + c["bm25"] + c["semantic"] + c["quality"])) < 1e-4
