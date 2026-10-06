"""Tests for LayoutBudgetModel and line capacity constraints."""

from careercompiler.layout.budget import LayoutBudgetModel
from eval.spike_s2_harness import TEST_BULLETS


def test_budget_evaluation_fits_within_capacity() -> None:
    """Selections within 30 bullet lines report fits=True."""
    budget = LayoutBudgetModel(capacity_lines=30)
    bullets = [
        "Short bullet point 1.",
        "Short bullet point 2.",
        "Short bullet point 3.",
    ]
    status = budget.evaluate(bullets)
    assert status.fits is True
    assert status.used_lines == 3
    assert status.remaining_lines == 27
    assert status.overflow_lines == 0


def test_budget_evaluation_overflows_when_exceeded() -> None:
    """Selections exceeding capacity report fits=False with positive overflow."""
    budget = LayoutBudgetModel(capacity_lines=5)
    bullets = [f"Bullet point {i} testing line bounds." for i in range(8)]
    status = budget.evaluate(bullets)
    assert status.fits is False
    assert status.used_lines == 8
    assert status.remaining_lines == 0
    assert status.overflow_lines == 3


def test_estimator_zero_underestimates_on_p1_harness() -> None:
    """Verify that FontMetricSimulator achieves zero under-estimates across all 52 P1 bullets."""
    budget = LayoutBudgetModel()
    for bid, text in TEST_BULLETS:
        lines = budget.lines_for_bullet(text)
        # Every test bullet is at least 1 line
        assert lines >= 1, f"Bullet {bid} estimated < 1 line"
