"""Tests for Markdown diff report formatting."""

from careercompiler.diff.models import (
    BulletDiff,
    DiffActionType,
    RevertRecord,
    ScoreDelta,
    SelectionDiff,
)
from careercompiler.diff.report import format_markdown_report
from careercompiler.scoring.models import ScoreBreakdown


def test_format_markdown_report_comprehensive() -> None:
    """Markdown report includes headers, score deltas, slot tables, and audit logs."""
    b_score = ScoreBreakdown(
        total_score=50.0,
        lexical_score=40.0,
        bm25_score=50.0,
        semantic_score=60.0,
        quality_score=60.0,
        coverage_count=2,
        total_requirements=5,
        covered_requirements=["python", "docker"],
        missing_requirements=["aws", "kubernetes", "fastapi"],
        component_contributions={"lexical": 16.0, "bm25": 12.5, "semantic": 12.0, "quality": 9.5},
    )

    t_score = ScoreBreakdown(
        total_score=75.0,
        lexical_score=70.0,
        bm25_score=80.0,
        semantic_score=75.0,
        quality_score=80.0,
        coverage_count=4,
        total_requirements=5,
        covered_requirements=["python", "docker", "aws", "kubernetes"],
        missing_requirements=["fastapi"],
        component_contributions={"lexical": 28.0, "bm25": 20.0, "semantic": 15.0, "quality": 12.0},
    )

    score_delta = ScoreDelta(
        baseline_score=b_score,
        tailored_score=t_score,
        delta_total=25.0,
        delta_lexical=30.0,
        delta_bm25=30.0,
        delta_semantic=15.0,
        delta_quality=20.0,
        newly_covered_requirements=["aws", "kubernetes"],
        lost_requirements=[],
    )

    b_diffs = [
        BulletDiff(
            slot_id="s1",
            entity_id="exp_1",
            action=DiffActionType.SWAPPED,
            baseline_variant_id="v1_base",
            tailored_variant_id="v1_tail",
            added_tags=["kubernetes"],
            line_delta=1,
            utility_delta=0.3,
            explanation="Swapped to variant emphasizing Kubernetes.",
        ),
        BulletDiff(
            slot_id="s2",
            entity_id="exp_1",
            action=DiffActionType.UNCHANGED,
            baseline_variant_id="v2_base",
            tailored_variant_id="v2_base",
            line_delta=0,
            utility_delta=0.0,
            explanation="Retained baseline default variant.",
        ),
    ]

    revert_history = [
        RevertRecord(
            timestamp="2026-10-07T12:00:00Z",
            slot_id="s1",
            previous_variant_id="v1_tail",
            reverted_to_variant_id="v1_base",
            reason="User preferred baseline wording",
        )
    ]

    diff = SelectionDiff(
        job_id="job_senior_devops",
        profile_id="anoop_nair",
        bullet_diffs=b_diffs,
        score_delta=score_delta,
        baseline_total_lines=28,
        tailored_total_lines=29,
        line_budget_delta=1,
        total_swapped=1,
        total_added=0,
        total_omitted=0,
        total_unchanged=1,
        revert_history=revert_history,
    )

    md = format_markdown_report(diff)

    assert "# Resume Tailoring Diff & Review Summary" in md
    assert "**Profile ID**: `anoop_nair`" in md
    assert "**Target Job ID**: `job_senior_devops`" in md
    assert "## ATS Score Delta" in md
    assert "`+25.00`" in md
    assert "**Newly Covered Requirements** (2): `aws`, `kubernetes`" in md
    assert "## Slot-Level Bullet Modifications" in md
    assert "`[SWAPPED]`" in md
    assert "`[UNCHANGED]`" in md
    assert "## Revert Audit Log" in md
    assert "User preferred baseline wording" in md
