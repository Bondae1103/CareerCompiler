"""Determinism tests for scoring engine across repeated runs."""

from pathlib import Path

from careercompiler.decomposition.decomposer import BulletDecomposer
from careercompiler.extraction.rule_extractor import LocalRuleExtractor
from careercompiler.parsing.resume_parser import parse_latex_resume
from careercompiler.scoring.models import ScorableBullet, ScoringConfig
from careercompiler.scoring.scorer import ResumeScorer


def test_scoring_determinism_across_runs() -> None:
    """Run scoring multiple times on authentic user resume and JD to verify bit-identical floats."""
    tex_path = Path("resume.tex")
    profile = parse_latex_resume(tex_path.read_text(encoding="utf-8"))

    decomposer = BulletDecomposer()
    decomp_map = decomposer.decompose_profile(profile)

    bullets: list[ScorableBullet] = []
    for vid, d in decomp_map.items():
        bullets.append(
            ScorableBullet(
                id=vid,
                text=d.raw_text,
                canonical_tags=d.canonical_tags,
                metric_quality=d.metric_quality,
            )
        )

    # Ingest a real JD
    jd_path = Path("data/raw_jds/optum_tdp_software_engineer.txt")
    extractor = LocalRuleExtractor()
    extracted_jd = extractor.extract(jd_path.read_text(encoding="utf-8"))

    cfg = ScoringConfig.load_from_toml()
    scorer = ResumeScorer(cfg)

    # First run baseline
    baseline_breakdown = scorer.score_selection(bullets, extracted_jd)

    # Verify 20 consecutive runs
    for run_idx in range(20):
        run_breakdown = scorer.score_selection(bullets, extracted_jd)
        assert run_breakdown.total_score == baseline_breakdown.total_score, f"Mismatch on run {run_idx}"
        assert run_breakdown.lexical_score == baseline_breakdown.lexical_score
        assert run_breakdown.bm25_score == baseline_breakdown.bm25_score
        assert run_breakdown.semantic_score == baseline_breakdown.semantic_score
        assert run_breakdown.quality_score == baseline_breakdown.quality_score
        assert run_breakdown.component_contributions == baseline_breakdown.component_contributions
        assert run_breakdown.covered_requirements == baseline_breakdown.covered_requirements
        assert run_breakdown.missing_requirements == baseline_breakdown.missing_requirements
