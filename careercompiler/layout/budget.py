"""Empirical line budget model and capacity verification for 1-page layout."""

from collections.abc import Sequence
from dataclasses import dataclass

from careercompiler.layout.estimator import FontMetricSimulator


@dataclass(frozen=True)
class BudgetStatus:
    """Status of line budget utilization."""

    fits: bool
    used_lines: int
    capacity_lines: int
    remaining_lines: int
    overflow_lines: int


class LayoutBudgetModel:
    """Manages line budget constraints derived empirically from Tectonic compile probes."""

    # Empirically measured: Jake's template fits up to 30 bullet lines alongside
    # standard header, education (4 lines), skills (6 lines), and leadership (3 lines).
    DEFAULT_BULLET_CAPACITY_LINES: int = 30

    def __init__(
        self,
        capacity_lines: int = DEFAULT_BULLET_CAPACITY_LINES,
        estimator: FontMetricSimulator | None = None,
    ) -> None:
        self.capacity_lines = capacity_lines
        self.estimator = estimator or FontMetricSimulator()

    def lines_for_bullet(self, text: str) -> int:
        """Estimate lines required for a single bullet text using FontMetricSimulator."""
        return max(1, self.estimator.estimate(text))

    def compute_total_bullet_lines(self, bullet_texts: Sequence[str]) -> int:
        """Compute sum of estimated lines across all selected bullets."""
        return sum(self.lines_for_bullet(t) for t in bullet_texts)

    def evaluate(self, bullet_texts: Sequence[str]) -> BudgetStatus:
        """Evaluate whether a selection of bullets fits within the 1-page budget."""
        used = self.compute_total_bullet_lines(bullet_texts)
        fits = used <= self.capacity_lines
        remaining = max(0, self.capacity_lines - used)
        overflow = max(0, used - self.capacity_lines)

        return BudgetStatus(
            fits=fits,
            used_lines=used,
            capacity_lines=self.capacity_lines,
            remaining_lines=remaining,
            overflow_lines=overflow,
        )
