"""Tests decomposing authentic bullet points from templates/resume.tex and profile storage."""

from pathlib import Path

from careercompiler.decomposition.decomposer import BulletDecomposer
from careercompiler.decomposition.models import MetricQuality
from careercompiler.parsing.resume_parser import parse_latex_resume
from tests.test_profile_storage import _build_test_profile


def test_decompose_test_profile_bullets() -> None:
    profile = _build_test_profile()
    decomposer = BulletDecomposer()
    results = decomposer.decompose_profile(profile)

    assert len(results) >= 3

    # Check v1_test_automation bullet
    b1 = results["v1_test_automation"]
    assert b1.action_verb is not None
    assert b1.action_verb.surface_form == "Architected"
    assert "playwright" in b1.canonical_tags
    assert "oop" in b1.canonical_tags
    assert "microservices" in b1.canonical_tags
    # Impact metric: 100% test coverage
    assert len(b1.impact_metrics) >= 1
    assert any(m.normalized_value == 100.0 and m.unit == "%" for m in b1.impact_metrics)
    assert b1.metric_quality == MetricQuality.QUANTIFIED

    # Check v2_prompt_opt bullet
    b2 = results["v2_prompt_opt"]
    assert b2.action_verb is not None
    assert b2.action_verb.surface_form == "Engineered"
    assert "prompt-engineering" in b2.canonical_tags
    assert "ci-cd" in b2.canonical_tags
    # 35% latency reduction
    assert len(b2.impact_metrics) >= 1
    assert any(m.normalized_value == 35.0 and m.unit == "%" for m in b2.impact_metrics)
    assert b2.metric_quality == MetricQuality.QUANTIFIED


def test_decompose_resume_tex_bullets() -> None:
    tex_path = Path("templates/resume.tex")
    assert tex_path.exists()
    profile = parse_latex_resume(tex_path.read_text(encoding="utf-8"))

    decomposer = BulletDecomposer()
    results = decomposer.decompose_profile(profile)

    # All bullets decomposed successfully
    assert len(results) >= 6

    for _vid, decomp in results.items():
        # Truth Invariant: every technology span slices the raw bullet text exactly
        for tech in decomp.technologies:
            start, end = tech.start, tech.end
            assert decomp.raw_text[start:end] == tech.surface_form

        # Truth Invariant: every impact metric span slices the raw bullet text exactly
        for metric in decomp.impact_metrics:
            start, end = metric.raw_span
            assert decomp.raw_text[start:end] == metric.raw_text
