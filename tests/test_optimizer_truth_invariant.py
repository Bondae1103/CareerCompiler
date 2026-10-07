"""Tests enforcing the Truth Invariant: every emitted bullet must match an authored bank variant byte-for-byte."""

from dataclasses import dataclass, field

import pytest

from careercompiler.optimizer.models import (
    SelectedBullet,
    Selection,
    TruthInvariantViolationError,
)
from careercompiler.optimizer.pipeline import ClosedLoopOptimizer


@dataclass
class Variant:
    id: str
    text: str
    lines: int = 1
    utility: float = 0.5
    canonical_tags: list[str] = field(default_factory=list)


@dataclass
class Slot:
    id: str
    variants: list[Variant]
    mandatory: bool = False
    pinned: bool = False


@dataclass
class Entity:
    id: str
    slots: list[Slot]
    min_bullets: int = 0
    max_bullets: int = 999


def test_truth_invariant_passes_on_valid_selection() -> None:
    """Truth Invariant verification succeeds when all selected bullets match authored bank variants."""
    v1 = Variant("v1", "Author authentic text A.")
    v2 = Variant("v2", "Author authentic text B.")
    ent = Entity("e1", [Slot("s1", [v1]), Slot("s2", [v2])])

    selection = Selection(
        selected_bullets=[
            SelectedBullet(slot_id="s1", variant_id="v1", entity_id="e1", text="Author authentic text A.", lines=1, utility=0.5),
            SelectedBullet(slot_id="s2", variant_id="v2", entity_id="e1", text="Author authentic text B.", lines=1, utility=0.5),
        ],
        slot_assignment={"s1": "v1", "s2": "v2"},
        total_lines=2,
        covered_requirements=[],
        objective_value=10.0,
        solve_time_seconds=0.01,
        solver_status="OPTIMAL",
    )

    optimizer = ClosedLoopOptimizer(template=None)
    # Should not raise
    optimizer.verify_truth_invariant([ent], selection)


def test_truth_invariant_raises_on_fabricated_variant_id() -> None:
    """Truth Invariant raises TruthInvariantViolationError if a variant ID does not exist in the bank."""
    v1 = Variant("v1", "Author authentic text A.")
    ent = Entity("e1", [Slot("s1", [v1])])

    # Injected phantom variant 'v_fake'
    selection = Selection(
        selected_bullets=[
            SelectedBullet(slot_id="s1", variant_id="v_fake", entity_id="e1", text="Author authentic text A.", lines=1, utility=0.5),
        ],
        slot_assignment={"s1": "v_fake"},
        total_lines=1,
        covered_requirements=[],
        objective_value=5.0,
        solve_time_seconds=0.01,
        solver_status="OPTIMAL",
    )

    optimizer = ClosedLoopOptimizer(template=None)
    with pytest.raises(TruthInvariantViolationError, match="does not exist in the authored profile bank"):
        optimizer.verify_truth_invariant([ent], selection)


def test_truth_invariant_raises_on_hallucinated_or_modified_text() -> None:
    """Truth Invariant raises TruthInvariantViolationError if bullet text is modified by even 1 character."""
    v1 = Variant("v1", "Author authentic text A.")
    ent = Entity("e1", [Slot("s1", [v1])])

    # Text modified with an extra period / word
    selection = Selection(
        selected_bullets=[
            SelectedBullet(slot_id="s1", variant_id="v1", entity_id="e1", text="Author authentic text A. (Modified)", lines=1, utility=0.5),
        ],
        slot_assignment={"s1": "v1"},
        total_lines=1,
        covered_requirements=[],
        objective_value=5.0,
        solve_time_seconds=0.01,
        solver_status="OPTIMAL",
    )

    optimizer = ClosedLoopOptimizer(template=None)
    with pytest.raises(TruthInvariantViolationError, match="has been modified from authored bank text"):
        optimizer.verify_truth_invariant([ent], selection)
