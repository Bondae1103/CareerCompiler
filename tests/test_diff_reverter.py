"""Tests for RevertManager handling 1-click rollbacks and Truth Invariant enforcement."""

from dataclasses import dataclass, field

import pytest

from careercompiler.diff.reverter import RevertManager
from careercompiler.optimizer.models import (
    SelectedBullet,
    Selection,
    TruthInvariantViolationError,
)


@dataclass
class Variant:
    id: str
    text: str
    is_default: bool = False
    lines: int = 1
    utility: float = 0.5
    canonical_tags: list[str] = field(default_factory=list)


@dataclass
class Slot:
    id: str
    variants: list[Variant]

    def get_default_variant(self) -> Variant:
        for v in self.variants:
            if v.is_default:
                return v
        return self.variants[0]


@dataclass
class Entity:
    id: str
    slots: list[Slot]
    min_bullets: int = 0
    max_bullets: int = 999


def test_revert_slot_restores_default_variant() -> None:
    """Reverting a slot restores the default authored variant and updates lines/tags."""
    v1 = Variant("v1", "Default authored bullet", is_default=True, lines=1, utility=0.5, canonical_tags=["python"])
    v2 = Variant("v2", "Tailored bullet variant", is_default=False, lines=2, utility=0.8, canonical_tags=["docker"])

    s1 = Slot("s1", [v1, v2])
    ent = Entity("e1", [s1], min_bullets=1, max_bullets=1)

    # Currently selecting v2
    tailored = Selection(
        selected_bullets=[
            SelectedBullet(slot_id="s1", variant_id="v2", entity_id="e1", text=v2.text, lines=2, utility=0.8, canonical_tags=["docker"])
        ],
        slot_assignment={"s1": "v2"},
        total_lines=2,
        covered_requirements=["docker"],
        objective_value=10.0,
        solve_time_seconds=0.01,
        solver_status="OPTIMAL",
    )

    reverter = RevertManager()
    new_sel, record = reverter.revert_slot(tailored, slot_id="s1", profile_or_entities=[ent], reason="User preference")

    assert new_sel.slot_assignment["s1"] == "v1"
    assert len(new_sel.selected_bullets) == 1
    assert new_sel.selected_bullets[0].variant_id == "v1"
    assert new_sel.selected_bullets[0].text == "Default authored bullet"
    assert new_sel.total_lines == 1
    assert "python" in new_sel.covered_requirements

    # Check audit record
    assert record.slot_id == "s1"
    assert record.previous_variant_id == "v2"
    assert record.reverted_to_variant_id == "v1"
    assert record.reason == "User preference"
    assert record.timestamp != ""


def test_revert_slot_enforces_truth_invariant() -> None:
    """Reverting to a non-existent variant raises TruthInvariantViolationError."""
    v1 = Variant("v1", "Default authored bullet", is_default=True)
    s1 = Slot("s1", [v1])
    ent = Entity("e1", [s1])

    tailored = Selection(
        selected_bullets=[
            SelectedBullet(slot_id="s1", variant_id="v1", entity_id="e1", text=v1.text, lines=1, utility=0.5, canonical_tags=["python"])
        ],
        slot_assignment={"s1": "v1"},
        total_lines=1,
        covered_requirements=["python"],
        objective_value=10.0,
        solve_time_seconds=0.01,
        solver_status="OPTIMAL",
    )

    reverter = RevertManager()
    with pytest.raises(TruthInvariantViolationError, match="not an authored variant"):
        reverter.revert_slot(tailored, slot_id="s1", profile_or_entities=[ent], target_variant_id="v_hallucinated")


def test_revert_all_restores_entire_resume() -> None:
    """revert_all restores multiple modified slots back to default authored states."""
    v1_1 = Variant("v1_1", "Default 1", is_default=True, lines=1, canonical_tags=["python"])
    v1_2 = Variant("v1_2", "Tailored 1", is_default=False, lines=1, canonical_tags=["docker"])

    v2_1 = Variant("v2_1", "Default 2", is_default=True, lines=1, canonical_tags=["fastapi"])
    v2_2 = Variant("v2_2", "Tailored 2", is_default=False, lines=1, canonical_tags=["redis"])

    s1 = Slot("s1", [v1_1, v1_2])
    s2 = Slot("s2", [v2_1, v2_2])
    ent = Entity("e1", [s1, s2])

    tailored = Selection(
        selected_bullets=[
            SelectedBullet(slot_id="s1", variant_id="v1_2", entity_id="e1", text=v1_2.text, lines=1, utility=0.8, canonical_tags=["docker"]),
            SelectedBullet(slot_id="s2", variant_id="v2_2", entity_id="e1", text=v2_2.text, lines=1, utility=0.8, canonical_tags=["redis"]),
        ],
        slot_assignment={"s1": "v1_2", "s2": "v2_2"},
        total_lines=2,
        covered_requirements=["docker", "redis"],
        objective_value=12.0,
        solve_time_seconds=0.01,
        solver_status="OPTIMAL",
    )

    reverter = RevertManager()
    restored, records = reverter.revert_all(tailored, [ent])

    assert len(records) == 2
    assert restored.slot_assignment["s1"] == "v1_1"
    assert restored.slot_assignment["s2"] == "v2_1"
    assert set(restored.covered_requirements) == {"fastapi", "python"}
