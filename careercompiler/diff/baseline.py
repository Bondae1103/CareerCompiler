"""Baseline selection generator from Master Profile Bank defaults."""

from collections.abc import Sequence
from typing import Any

from careercompiler.layout.estimator import FontMetricSimulator
from careercompiler.optimizer.models import SelectedBullet, Selection


def build_baseline_selection(
    profile_or_entities: Any,
    estimator: FontMetricSimulator | None = None,
) -> Selection:
    """Generate the deterministic baseline selection using each slot's default variant.

    Args:
        profile_or_entities: Profile instance or sequence of Experience / Project entities.
        estimator: Optional FontMetricSimulator to estimate bullet line counts.

    Returns:
        Selection representing the user's default, untailored master profile state.
    """
    if hasattr(profile_or_entities, "experiences") and hasattr(profile_or_entities, "projects"):
        entities: Sequence[Any] = list(profile_or_entities.experiences) + list(profile_or_entities.projects)
    else:
        entities = list(profile_or_entities)

    sim = estimator or FontMetricSimulator()

    selected_bullets: list[SelectedBullet] = []
    slot_assignment: dict[str, str | None] = {}
    all_tags: set[str] = set()

    for entity in entities:
        for slot in entity.slots:
            if not getattr(slot, "variants", None):
                slot_assignment[slot.id] = None
                continue

            # Determine default variant
            default_var: Any = None
            if hasattr(slot, "get_default_variant"):
                default_var = slot.get_default_variant()
            else:
                for v in slot.variants:
                    if getattr(v, "is_default", False):
                        default_var = v
                        break
                if default_var is None:
                    default_var = slot.variants[0]

            slot_assignment[slot.id] = default_var.id

            # Determine line count
            lines = getattr(default_var, "lines", None)
            if lines is None:
                lines = max(1, sim.estimate(default_var.text))

            tags = list(getattr(default_var, "canonical_tags", []))
            all_tags.update(t.lower() for t in tags)

            selected_bullets.append(
                SelectedBullet(
                    slot_id=slot.id,
                    variant_id=default_var.id,
                    entity_id=entity.id,
                    text=default_var.text,
                    lines=int(lines),
                    utility=float(getattr(default_var, "utility", 0.0)),
                    canonical_tags=tags,
                )
            )

    total_lines = sum(b.lines for b in selected_bullets)

    return Selection(
        selected_bullets=selected_bullets,
        slot_assignment=slot_assignment,
        total_lines=total_lines,
        covered_requirements=sorted(all_tags),
        objective_value=0.0,
        solve_time_seconds=0.0,
        solver_status="OPTIMAL",
    )
