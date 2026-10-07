"""Diff calculation engine comparing tailored selections against baseline defaults."""

from collections.abc import Sequence
from typing import Any

from careercompiler.decomposition.metrics import (
    classify_metric_quality,
    extract_impact_metrics,
)
from careercompiler.diff.models import (
    BulletDiff,
    DiffActionType,
    ScoreDelta,
    SelectionDiff,
)
from careercompiler.extraction.models import ExtractedJD
from careercompiler.optimizer.models import SelectedBullet, Selection
from careercompiler.scoring.models import ScorableBullet
from careercompiler.scoring.scorer import ResumeScorer


class DiffEngine:
    """Computes granular bullet-level diffs and multi-component score deltas."""

    def __init__(self, scorer: ResumeScorer | None = None) -> None:
        self.scorer = scorer

    @staticmethod
    def _to_scorable_bullets(bullets: Sequence[SelectedBullet]) -> list[ScorableBullet]:
        """Convert SelectedBullet models to typed ScorableBullet models with parsed metric quality."""
        scorable: list[ScorableBullet] = []
        for b in bullets:
            metrics = extract_impact_metrics(b.text)
            qual = classify_metric_quality(b.text, metrics)
            scorable.append(
                ScorableBullet(
                    id=b.variant_id,
                    text=b.text,
                    canonical_tags=b.canonical_tags,
                    metric_quality=qual,
                    lines=b.lines,
                )
            )
        return scorable

    def compute_diff(
        self,
        baseline: Selection,
        tailored: Selection,
        profile_or_entities: Any,
        jd: ExtractedJD | None = None,
        job_id: str | None = None,
        extra_skills: Sequence[str] | None = None,
        bank_bullet_texts: Sequence[str] | None = None,
    ) -> SelectionDiff:
        """Calculate side-by-side slot diffs, keyword gains, and ATS score deltas."""
        # 1. Normalize entity list and extract profile ID
        profile_id = "master_profile"
        if hasattr(profile_or_entities, "id"):
            profile_id = str(profile_or_entities.id)

        if hasattr(profile_or_entities, "experiences") and hasattr(profile_or_entities, "projects"):
            entities: Sequence[Any] = list(profile_or_entities.experiences) + list(profile_or_entities.projects)
        else:
            entities = list(profile_or_entities)

        # 2. Map slots and authored variants
        slot_to_entity: dict[str, str] = {}
        variants_by_slot: dict[str, dict[str, Any]] = {}
        ordered_slot_ids: list[str] = []

        for entity in entities:
            for slot in entity.slots:
                slot_to_entity[slot.id] = entity.id
                ordered_slot_ids.append(slot.id)
                variants_by_slot[slot.id] = {v.id: v for v in slot.variants}

        # Include any slots present in assignments not in ordered list
        for sid in list(baseline.slot_assignment.keys()) + list(tailored.slot_assignment.keys()):
            if sid not in slot_to_entity:
                slot_to_entity[sid] = "unknown_entity"
                ordered_slot_ids.append(sid)
                variants_by_slot[sid] = {}

        bullet_diffs: list[BulletDiff] = []

        # 3. Compute slot-level diffs
        for slot_id in ordered_slot_ids:
            base_var_id = baseline.slot_assignment.get(slot_id)
            tail_var_id = tailored.slot_assignment.get(slot_id)

            if base_var_id is None and tail_var_id is None:
                continue

            entity_id = slot_to_entity.get(slot_id, "unknown_entity")
            slot_variants = variants_by_slot.get(slot_id, {})

            base_var = slot_variants.get(base_var_id) if base_var_id else None
            tail_var = slot_variants.get(tail_var_id) if tail_var_id else None

            base_text = getattr(base_var, "text", None)
            tail_text = getattr(tail_var, "text", None)

            base_tags = set(getattr(base_var, "canonical_tags", [])) if base_var else set()
            tail_tags = set(getattr(tail_var, "canonical_tags", [])) if tail_var else set()

            added_tags = sorted(tail_tags - base_tags)
            removed_tags = sorted(base_tags - tail_tags)

            base_lines = int(getattr(base_var, "lines", 1)) if base_var else 0
            tail_lines = int(getattr(tail_var, "lines", 1)) if tail_var else 0
            line_delta = tail_lines - base_lines

            base_util = float(getattr(base_var, "utility", 0.0)) if base_var else 0.0
            tail_util = float(getattr(tail_var, "utility", 0.0)) if tail_var else 0.0
            utility_delta = round(tail_util - base_util, 4)

            # Determine DiffActionType
            if base_var_id == tail_var_id:
                action = DiffActionType.UNCHANGED
                can_revert = False
                explanation = "Retained baseline default variant."
            elif base_var_id is None and tail_var_id is not None:
                action = DiffActionType.ADDED
                can_revert = True
                explanation = f"Added slot to include variant '{tail_var_id}' (+{tail_lines} lines)."
            elif base_var_id is not None and tail_var_id is None:
                action = DiffActionType.OMITTED
                can_revert = True
                explanation = f"Omitted slot to respect strict 1-page line budget (saved {base_lines} lines)."
            else:
                is_llm = getattr(tail_var, "is_llm_rewritten", False) or getattr(tail_var, "angle", "") == "llm_rewritten"
                action = DiffActionType.LLM_REWRITTEN if is_llm else DiffActionType.SWAPPED
                can_revert = True
                added_str = f", gained tags: [{', '.join(added_tags)}]" if added_tags else ""
                explanation = f"Swapped variant from '{base_var_id}' to '{tail_var_id}'{added_str}."

            bullet_diffs.append(
                BulletDiff(
                    slot_id=slot_id,
                    entity_id=entity_id,
                    action=action,
                    baseline_variant_id=base_var_id,
                    baseline_text=base_text,
                    tailored_variant_id=tail_var_id,
                    tailored_text=tail_text,
                    added_tags=added_tags,
                    removed_tags=removed_tags,
                    line_delta=line_delta,
                    utility_delta=utility_delta,
                    can_revert=can_revert,
                    revert_to_variant_id=base_var_id if can_revert else None,
                    explanation=explanation,
                )
            )

        # 4. Compute ScoreDelta if JD and scorer are available
        score_delta: ScoreDelta | None = None
        if jd is not None and self.scorer is not None:
            base_scorable = self._to_scorable_bullets(baseline.selected_bullets)
            tail_scorable = self._to_scorable_bullets(tailored.selected_bullets)

            base_breakdown = self.scorer.score_selection(base_scorable, jd, extra_skills, bank_bullet_texts)
            tail_breakdown = self.scorer.score_selection(tail_scorable, jd, extra_skills, bank_bullet_texts)

            d_total = round(tail_breakdown.total_score - base_breakdown.total_score, 4)
            d_lex = round(tail_breakdown.lexical_score - base_breakdown.lexical_score, 4)
            d_bm25 = round(tail_breakdown.bm25_score - base_breakdown.bm25_score, 4)
            d_sem = round(tail_breakdown.semantic_score - base_breakdown.semantic_score, 4)
            d_qual = round(tail_breakdown.quality_score - base_breakdown.quality_score, 4)

            new_reqs = sorted(set(tail_breakdown.covered_requirements) - set(base_breakdown.covered_requirements))
            lost_reqs = sorted(set(base_breakdown.covered_requirements) - set(tail_breakdown.covered_requirements))

            score_delta = ScoreDelta(
                baseline_score=base_breakdown,
                tailored_score=tail_breakdown,
                delta_total=d_total,
                delta_lexical=d_lex,
                delta_bm25=d_bm25,
                delta_semantic=d_sem,
                delta_quality=d_qual,
                newly_covered_requirements=new_reqs,
                lost_requirements=lost_reqs,
            )

        # 5. Summarize statistics
        total_swapped = sum(1 for d in bullet_diffs if d.action in (DiffActionType.SWAPPED, DiffActionType.LLM_REWRITTEN))
        total_added = sum(1 for d in bullet_diffs if d.action == DiffActionType.ADDED)
        total_omitted = sum(1 for d in bullet_diffs if d.action == DiffActionType.OMITTED)
        total_unchanged = sum(1 for d in bullet_diffs if d.action == DiffActionType.UNCHANGED)

        return SelectionDiff(
            job_id=job_id,
            profile_id=profile_id,
            bullet_diffs=bullet_diffs,
            score_delta=score_delta,
            baseline_total_lines=baseline.total_lines,
            tailored_total_lines=tailored.total_lines,
            line_budget_delta=tailored.total_lines - baseline.total_lines,
            total_swapped=total_swapped,
            total_added=total_added,
            total_omitted=total_omitted,
            total_unchanged=total_unchanged,
            revert_history=[],
        )
