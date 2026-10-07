"""Tests for baseline selection generation from profile defaults."""

from dataclasses import dataclass, field

from careercompiler.diff.baseline import build_baseline_selection


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


@dataclass
class Entity:
    id: str
    slots: list[Slot]


def test_build_baseline_selection_uses_default_variants() -> None:
    """Baseline selection selects each slot's marked default variant."""
    v1 = Variant("v1", "Default text", is_default=True, lines=1, canonical_tags=["python"])
    v2 = Variant("v2", "Alternative text", is_default=False, lines=2, canonical_tags=["docker"])

    s1 = Slot("s1", [v1, v2])
    ent = Entity("e1", [s1])

    baseline = build_baseline_selection([ent])

    assert baseline.slot_assignment["s1"] == "v1"
    assert len(baseline.selected_bullets) == 1
    assert baseline.selected_bullets[0].variant_id == "v1"
    assert baseline.selected_bullets[0].text == "Default text"
    assert baseline.total_lines == 1
    assert "python" in baseline.covered_requirements


def test_build_baseline_selection_falls_back_to_first_variant() -> None:
    """When no variant is explicitly marked default, baseline falls back to first variant."""
    v1 = Variant("v1", "First text", is_default=False, lines=2, canonical_tags=["fastapi"])
    v2 = Variant("v2", "Second text", is_default=False, lines=1, canonical_tags=["redis"])

    s1 = Slot("s1", [v1, v2])
    ent = Entity("e1", [s1])

    baseline = build_baseline_selection([ent])

    assert baseline.slot_assignment["s1"] == "v1"
    assert baseline.total_lines == 2
