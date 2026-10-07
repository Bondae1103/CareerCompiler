"""Exact brute-force reference solver for small optimization instances."""

import itertools
import time
from collections.abc import Sequence
from typing import Any

from careercompiler.optimizer.models import SelectedBullet, Selection


class BruteForceOptimizer:
    """Exact combinatorial solver that explores all valid slot-to-variant assignments."""

    def __init__(
        self,
        weight_scale: int = 1000,
        utility_scale: int = 10,
        estimator: Any = None,
    ) -> None:
        self.weight_scale = weight_scale
        self.utility_scale = utility_scale
        self.estimator = estimator

    def _get_variant_lines(self, variant: Any) -> int:
        lines = getattr(variant, "lines", None)
        if lines is not None:
            return int(lines)
        if self.estimator is not None and hasattr(variant, "text"):
            return int(max(1, self.estimator.estimate(variant.text)))
        return 1

    def solve(
        self,
        entities: Sequence[Any],  # List of Experience or Project models with slots
        requirements: Sequence[Any],  # List of ExtractedRequirement or (req_id, canonical_id, weight)
        capacity_lines: int,
    ) -> Selection | None:
        """Find the globally optimal selection via exhaustive enumeration."""
        start_time = time.perf_counter()

        # 1. Flatten slots and map to entities
        all_slots: list[Any] = []
        slot_to_entity: dict[str, str] = {}
        for entity in entities:
            for slot in entity.slots:
                all_slots.append(slot)
                slot_to_entity[slot.id] = entity.id

        # 2. For each slot, candidate choices are: [None] + variants (or only variants if mandatory/pinned)
        slot_choices: list[list[Any]] = []
        for slot in all_slots:
            is_forced = getattr(slot, "mandatory", False) or getattr(slot, "pinned", False)
            choices = list(slot.variants)
            if not is_forced:
                choices = [None] + choices
            slot_choices.append(choices)

        best_score = float("-inf")
        best_assignment: list[tuple[Any, Any]] | None = None
        best_covered_reqs: list[str] = []
        best_lines = 0

        # Parse requirement tuples: (req_id, canonical_id, integer weight)
        req_tuples: list[tuple[str, str, int]] = []
        for r in requirements:
            if hasattr(r, "canonical_id"):
                cid = (r.canonical_id or r.surface_form).lower()
                cat_val = getattr(r.category, "value", str(r.category))
                w = int(self.weight_scale * (1.0 if cat_val == "must_have" else 0.5))
                req_tuples.append((r.id, cid, w))
            else:
                req_tuples.append((r[0], r[1].lower(), int(self.weight_scale * float(r[2]))))

        # 3. Exhaustive search over all combinations
        for combo in itertools.product(*slot_choices):
            # Check line budget
            total_lines = 0
            selected_per_entity: dict[str, int] = {e.id: 0 for e in entities}
            selected_items: list[tuple[Any, Any]] = []

            valid = True
            for slot, variant in zip(all_slots, combo, strict=True):
                if variant is not None:
                    var_lines = self._get_variant_lines(variant)
                    total_lines += var_lines
                    ent_id = slot_to_entity[slot.id]
                    selected_per_entity[ent_id] += 1
                    selected_items.append((slot, variant))

            if total_lines > capacity_lines:
                continue

            # Check entity min/max bounds
            for entity in entities:
                count = selected_per_entity[entity.id]
                min_b = getattr(entity, "min_bullets", 0)
                max_b = getattr(entity, "max_bullets", len(entity.slots))
                if not (min_b <= count <= max_b):
                    valid = False
                    break

            if not valid:
                continue

            # Compute requirement coverage
            covered_tags: set[str] = set()
            for _, variant in selected_items:
                tags = getattr(variant, "canonical_tags", [])
                for t in tags:
                    covered_tags.add(t.lower())

            cov_score = 0
            covered_ids: list[str] = []
            for rid, cid, w in req_tuples:
                if cid in covered_tags:
                    cov_score += w
                    covered_ids.append(rid)

            util_score = 0
            for _, variant in selected_items:
                util = int(self.utility_scale * round(getattr(variant, "utility", 0.0), 2))
                util_score += util

            # Objective: primary coverage, secondary utility, tertiary line tie-breaker
            score = float(cov_score + util_score - total_lines)

            # Stable tie-breaking: prefer strictly higher score
            if score > best_score:
                best_score = score
                best_assignment = selected_items
                best_covered_reqs = sorted(covered_ids)
                best_lines = total_lines

        elapsed = time.perf_counter() - start_time

        if best_assignment is None:
            return None

        # Build Selection model
        selected_bullets: list[SelectedBullet] = []
        slot_map: dict[str, str | None] = {s.id: None for s in all_slots}

        for slot, variant in best_assignment:
            slot_map[slot.id] = variant.id
            selected_bullets.append(
                SelectedBullet(
                    slot_id=slot.id,
                    variant_id=variant.id,
                    entity_id=slot_to_entity[slot.id],
                    text=variant.text,
                    lines=self._get_variant_lines(variant),
                    utility=getattr(variant, "utility", 0.0),
                    canonical_tags=getattr(variant, "canonical_tags", []),
                )
            )

        return Selection(
            selected_bullets=selected_bullets,
            slot_assignment=slot_map,
            total_lines=best_lines,
            covered_requirements=best_covered_reqs,
            objective_value=round(best_score, 4),
            solve_time_seconds=elapsed,
            solver_status="OPTIMAL",
        )
