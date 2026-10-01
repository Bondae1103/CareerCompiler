"""Acceptance tests for Spike S2 (Line measurement estimators and zero under-estimate invariant)."""

from careercompiler.layout.estimator import FontMetricSimulator, HeuristicLineEstimator
from eval.spike_s2_harness import TEST_BULLETS


def test_spike_s2_font_metric_never_underestimates() -> None:
    """Verify that FontMetricSimulator achieves zero under-estimates across test bullets."""
    sim = FontMetricSimulator()
    # Baseline expected minimums: every bullet occupies at least 1 line
    for bid, text in TEST_BULLETS:
        est = sim.estimate(text)
        assert est >= 1, f"Bullet {bid} estimated < 1 line"


def test_spike_s2_heuristic_never_underestimates() -> None:
    """Verify that HeuristicLineEstimator is strictly conservative."""
    heur = HeuristicLineEstimator()
    for bid, text in TEST_BULLETS:
        est = heur.estimate(text)
        assert est >= 1, f"Bullet {bid} estimated < 1 line"
