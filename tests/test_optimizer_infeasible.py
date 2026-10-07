"""Tests for optimizer infeasibility detection and structured error diagnostics."""

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


def test_infeasible_line_budget_exceeded() -> None:
    """When mandatory bullets require more lines than capacity, structured LINE_BUDGET reason is returned."""
    solver = ILPOptimizer()

    # Two mandatory slots requiring at least 1 + 2 = 3 lines
    s1 = Slot("s1", [Variant("v1", "Text 1", lines=1)], mandatory=True)
    s2 = Slot("s2", [Variant("v2", "Text 2", lines=2)], mandatory=True)
    ent = Entity("e1", [s1, s2], min_bullets=0, max_bullets=2)

    # Capacity is only 2 lines
    res = solver.optimize([ent], [], capacity_lines=2)
    assert res.success is False
    assert res.selection is None
    assert res.infeasibility_reason is not None
    assert res.infeasibility_reason.conflict_type == "LINE_BUDGET"
    assert res.infeasibility_reason.required_lines == 3
    assert res.infeasibility_reason.available_lines == 2
    assert set(res.infeasibility_reason.conflicting_slots) == {"s1", "s2"}


def test_infeasible_max_bullets_overflow() -> None:
    """When mandatory slots exceed max_bullets, MAX_BULLETS_CONFLICT is reported."""
    solver = ILPOptimizer()

    s1 = Slot("s1", [Variant("v1", "Text 1", lines=1)], mandatory=True)
    s2 = Slot("s2", [Variant("v2", "Text 2", lines=1)], mandatory=True)
    # max_bullets is 1, but 2 slots are mandatory!
    ent = Entity("e1", [s1, s2], min_bullets=0, max_bullets=1)

    res = solver.optimize([ent], [], capacity_lines=10)
    assert res.success is False
    assert res.infeasibility_reason is not None
    assert res.infeasibility_reason.conflict_type == "MAX_BULLETS_CONFLICT"
    assert "exceeds max_bullets" in res.infeasibility_reason.details


def test_infeasible_min_bullets_unsatisfiable() -> None:
    """When min_bullets exceeds available slots in an entity, MIN_BULLETS_UNSATISFIABLE is reported."""
    solver = ILPOptimizer()

    s1 = Slot("s1", [Variant("v1", "Text 1", lines=1)])
    # min_bullets is 3, but only 1 slot exists!
    ent = Entity("e1", [s1], min_bullets=3, max_bullets=5)

    res = solver.optimize([ent], [], capacity_lines=10)
    assert res.success is False
    assert res.infeasibility_reason is not None
    assert res.infeasibility_reason.conflict_type == "MIN_BULLETS_UNSATISFIABLE"
    assert "requires at least 3 bullets, but only has 1 total slots" in res.infeasibility_reason.details
