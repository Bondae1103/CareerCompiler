"""Unit and integration tests for optimizer constraints."""

from dataclasses import dataclass, field

from careercompiler.optimizer.solver import ILPOptimizer


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


def test_mandatory_slot_always_selected() -> None:
    """A mandatory slot must always be selected in any feasible solution."""
    solver = ILPOptimizer()
    v1 = Variant("v1", "Text 1", lines=1, utility=0.2, canonical_tags=["python"])
    v2 = Variant("v2", "Text 2", lines=1, utility=0.9, canonical_tags=["aws"])

    # slot1 is mandatory, slot2 is optional with higher utility and better tag
    s1 = Slot("s1", [v1], mandatory=True)
    s2 = Slot("s2", [v2], mandatory=False)
    ent = Entity("e1", [s1, s2], min_bullets=0, max_bullets=2)

    reqs = [("r1", "aws", 1.0)]

    # If capacity is 1 line, only 1 bullet can fit. S1 must be chosen despite lower utility/tag!
    res = solver.optimize([ent], reqs, capacity_lines=1)
    assert res.success is True
    assert res.selection is not None
    assert res.selection.slot_assignment["s1"] == "v1"
    assert res.selection.slot_assignment["s2"] is None
    assert res.selection.total_lines == 1


def test_entity_min_and_max_bullet_bounds() -> None:
    """Entity bounds [min_bullets, max_bullets] must strictly constrain the selection."""
    solver = ILPOptimizer()

    slots = [
        Slot(f"s{i}", [Variant(f"v{i}", f"Text {i}", lines=1, utility=1.0, canonical_tags=["python"])])
        for i in range(5)
    ]
    # min_bullets=2, max_bullets=3 on 5 available slots
    ent = Entity("e1", slots, min_bullets=2, max_bullets=3)
    reqs = [("r1", "python", 1.0)]

    # With capacity 5, exactly 3 should be selected (max_bullets=3)
    res_cap5 = solver.optimize([ent], reqs, capacity_lines=5)
    assert res_cap5.success is True
    assert res_cap5.selection is not None
    assert len(res_cap5.selection.selected_bullets) == 3

    # With capacity 2, exactly 2 should be selected (min_bullets=2)
    res_cap2 = solver.optimize([ent], reqs, capacity_lines=2)
    assert res_cap2.success is True
    assert res_cap2.selection is not None
    assert len(res_cap2.selection.selected_bullets) == 2

    # With capacity 1, infeasible because min_bullets=2 requires at least 2 lines
    res_cap1 = solver.optimize([ent], reqs, capacity_lines=1)
    assert res_cap1.success is False
    assert res_cap1.infeasibility_reason is not None
    assert res_cap1.infeasibility_reason.conflict_type == "LINE_BUDGET"


def test_submodular_tag_coverage_deduplication() -> None:
    """Covering a requirement multiple times only awards coverage credit once."""
    solver = ILPOptimizer()

    # Two slots both offering 'python' tag
    v1 = Variant("v1", "Python bullet 1", lines=1, utility=0.1, canonical_tags=["python"])
    v2 = Variant("v2", "Python bullet 2", lines=1, utility=0.1, canonical_tags=["python"])
    v3 = Variant("v3", "Docker bullet", lines=1, utility=0.1, canonical_tags=["docker"])

    s1 = Slot("s1", [v1])
    s2 = Slot("s2", [v2])
    s3 = Slot("s3", [v3])

    ent = Entity("e1", [s1, s2, s3], min_bullets=0, max_bullets=3)
    reqs = [("r1", "python", 1.0), ("r2", "docker", 1.0)]

    # With capacity 2, solver should pick (v1 or v2) + v3 to cover both requirements,
    # rather than (v1 + v2) which redundantly covers 'python'.
    res = solver.optimize([ent], reqs, capacity_lines=2)
    assert res.success is True
    assert res.selection is not None
    assert set(res.selection.covered_requirements) == {"r1", "r2"}
    assert res.selection.slot_assignment["s3"] == "v3"


def test_lexicographical_tie_breaking_prefers_fewer_lines() -> None:
    """When requirement coverage and utility are identical, fewer lines are strictly preferred."""
    solver = ILPOptimizer()

    # Slot 1 has two variants: 1 line vs 2 lines, identical tags and utility
    v_compact = Variant("v_comp", "Compact", lines=1, utility=0.5, canonical_tags=["python"])
    v_verbose = Variant("v_verb", "Verbose", lines=2, utility=0.5, canonical_tags=["python"])

    s = Slot("s1", [v_compact, v_verbose], mandatory=True)
    ent = Entity("e1", [s], min_bullets=1, max_bullets=1)
    reqs = [("r1", "python", 1.0)]

    res = solver.optimize([ent], reqs, capacity_lines=5)
    assert res.success is True
    assert res.selection is not None
    assert res.selection.slot_assignment["s1"] == "v_comp"
    assert res.selection.total_lines == 1
