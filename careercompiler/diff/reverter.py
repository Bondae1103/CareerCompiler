"""1-click reversion engine for individual bullet slots and full-resume rollbacks."""

from datetime import UTC, datetime
from typing import Any

from careercompiler.diff.models import RevertRecord
from careercompiler.layout.estimator import FontMetricSimulator
from careercompiler.optimizer.models import (
    SelectedBullet,
    Selection,
    TruthInvariantViolationError,
)


class RevertManager:
    """Manages 1-click slot rollbacks and audit log tracking with Truth Invariant preservation."""

    def __init__(self, estimator: FontMetricSimulator | None = None) -> None:
        self.estimator = estimator or FontMetricSimulator()

    @staticmethod
    def _normalize_entities(profile_or_entities: Any) -> tuple[str, list[Any]]:
        profile_id = str(getattr(profile_or_entities, "id", "master_profile"))
        if hasattr(profile_or_entities, "experiences") and hasattr(profile_or_entities, "projects"):
            entities = list(profile_or_entities.experiences) + list(profile_or_entities.projects)
        else:
            entities = list(profile_or_entities)
        return profile_id, entities

    @staticmethod
    def _get_default_variant(slot: Any) -> Any:
        if hasattr(slot, "get_default_variant"):
            return slot.get_default_variant()
        for v in slot.variants:
            if getattr(v, "is_default", False):
                return v
        return slot.variants[0] if slot.variants else None

    def revert_slot(
        self,
        current_selection: Selection,
        slot_id: str,
        profile_or_entities: Any,
        target_variant_id: str | None = None,
        reason: str | None = None,
    ) -> tuple[Selection, RevertRecord]:
        """Revert a single slot to its baseline default variant (or specified target variant).

        Raises:
            TruthInvariantViolationError: If target_variant_id is not an authored bank variant.
            KeyError: If slot_id is not found in profile entities.
        """
        _, entities = self._normalize_entities(profile_or_entities)

        # Locate slot and parent entity
        target_slot: Any = None
        parent_entity: Any = None

        for ent in entities:
            for s in ent.slots:
                if s.id == slot_id:
                    target_slot = s
                    parent_entity = ent
                    break
            if target_slot is not None:
                break

        if target_slot is None or parent_entity is None:
            raise KeyError(f"Slot '{slot_id}' not found in profile entities.")

        # Determine target variant
        if target_variant_id is None:
            target_variant = self._get_default_variant(target_slot)
            if target_variant is None:
                raise TruthInvariantViolationError(f"No default variant exists for slot '{slot_id}'.")
        else:
            variants_map = {v.id: v for v in target_slot.variants}
            if target_variant_id not in variants_map:
                raise TruthInvariantViolationError(
                    f"Truth Invariant Violation: Target variant '{target_variant_id}' is not an authored "
                    f"variant for slot '{slot_id}'."
                )
            target_variant = variants_map[target_variant_id]

        prev_variant_id = current_selection.slot_assignment.get(slot_id)

        # Build updated slot assignment
        new_slot_assignment = dict(current_selection.slot_assignment)
        new_slot_assignment[slot_id] = target_variant.id

        # Update selected bullets list
        new_bullets: list[SelectedBullet] = []
        slot_found_in_bullets = False

        v_lines = getattr(target_variant, "lines", None)
        if v_lines is None:
            v_lines = max(1, self.estimator.estimate(target_variant.text))

        replacement_bullet = SelectedBullet(
            slot_id=slot_id,
            variant_id=target_variant.id,
            entity_id=parent_entity.id,
            text=target_variant.text,
            lines=int(v_lines),
            utility=float(getattr(target_variant, "utility", 0.0)),
            canonical_tags=list(getattr(target_variant, "canonical_tags", [])),
        )

        for b in current_selection.selected_bullets:
            if b.slot_id == slot_id:
                new_bullets.append(replacement_bullet)
                slot_found_in_bullets = True
            else:
                new_bullets.append(b)

        if not slot_found_in_bullets:
            # Slot was previously omitted; add it
            new_bullets.append(replacement_bullet)

        # Validate entity bullet bounds
        bullets_in_entity = sum(1 for b in new_bullets if b.entity_id == parent_entity.id)
        min_b = getattr(parent_entity, "min_bullets", 0)
        max_b = getattr(parent_entity, "max_bullets", 999)
        if not (min_b <= bullets_in_entity <= max_b):
            raise ValueError(
                f"Reverting slot '{slot_id}' violates entity '{parent_entity.id}' bullet bounds: "
                f"{bullets_in_entity} bullets (allowed [{min_b}, {max_b}])."
            )

        new_total_lines = sum(b.lines for b in new_bullets)
        all_tags = sorted({t.lower() for b in new_bullets for t in b.canonical_tags})

        new_selection = Selection(
            selected_bullets=new_bullets,
            slot_assignment=new_slot_assignment,
            total_lines=new_total_lines,
            covered_requirements=all_tags,
            objective_value=current_selection.objective_value,
            solve_time_seconds=0.0,
            solver_status=current_selection.solver_status,
        )

        timestamp = datetime.now(UTC).isoformat()
        record = RevertRecord(
            timestamp=timestamp,
            slot_id=slot_id,
            previous_variant_id=prev_variant_id,
            reverted_to_variant_id=target_variant.id,
            reason=reason or f"Reverted slot '{slot_id}' to authored default '{target_variant.id}'.",
        )

        return new_selection, record

    def revert_all(
        self,
        current_selection: Selection,
        profile_or_entities: Any,
        reason: str = "1-click revert all to baseline defaults",
    ) -> tuple[Selection, list[RevertRecord]]:
        """1-click revert of all tailored slots back to the user's default authored variants."""
        _, entities = self._normalize_entities(profile_or_entities)
        records: list[RevertRecord] = []
        sel = current_selection

        for ent in entities:
            for s in ent.slots:
                default_v = self._get_default_variant(s)
                if default_v is None:
                    continue
                current_v_id = sel.slot_assignment.get(s.id)
                if current_v_id != default_v.id:
                    sel, rec = self.revert_slot(
                        sel,
                        slot_id=s.id,
                        profile_or_entities=profile_or_entities,
                        target_variant_id=default_v.id,
                        reason=reason,
                    )
                    records.append(rec)

        return sel, records
