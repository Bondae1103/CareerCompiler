"""Exact Integer Linear Programming (ILP) optimizer using Google OR-Tools CP-SAT."""

import time
from collections.abc import Sequence
from typing import Any

from ortools.sat.python import cp_model

from careercompiler.optimizer.models import (
    InfeasibilityReason,
    OptimizationResult,
    SelectedBullet,
    Selection,
)


class ILPOptimizer:
    """Deterministic ILP optimizer for resume slot-variant selection under strict line budget."""

    def __init__(
        self,
        weight_scale: int = 1000,
        utility_scale: int = 10,
        random_seed: int = 42,
        estimator: Any = None,
    ) -> None:
        self.weight_scale = weight_scale
        self.utility_scale = utility_scale
        self.random_seed = random_seed
        self.estimator = estimator

    def _get_variant_lines(self, variant: Any) -> int:
        lines = getattr(variant, "lines", None)
        if lines is not None:
            return int(lines)
        if self.estimator is not None and hasattr(variant, "text"):
            return int(max(1, self.estimator.estimate(variant.text)))
        return 1

    def _diagnose_infeasibility(
        self,
        entities: Sequence[Any],
        capacity_lines: int,
    ) -> InfeasibilityReason:
        """Analyze conflicting constraints to provide a structured diagnosis."""
        min_lines_needed = 0
        conflicting_slots: list[str] = []

        for entity in entities:
            # Check if mandatory slots exceed max_bullets
            mandatory_count = 0
            for slot in entity.slots:
                is_forced = getattr(slot, "mandatory", False) or getattr(slot, "pinned", False)
                if is_forced:
                    mandatory_count += 1
                    conflicting_slots.append(slot.id)
                    # Minimum line cost among variants
                    min_v_lines = min((self._get_variant_lines(v) for v in slot.variants), default=1)
                    min_lines_needed += min_v_lines

            max_b = getattr(entity, "max_bullets", 999)
            if mandatory_count > max_b:
                return InfeasibilityReason(
                    conflict_type="MAX_BULLETS_CONFLICT",
                    details=(
                        f"Entity '{entity.id}' has {mandatory_count} mandatory/pinned slots, "
                        f"which exceeds max_bullets limit of {max_b}."
                    ),
                    conflicting_slots=conflicting_slots,
                    required_lines=min_lines_needed,
                    available_lines=capacity_lines,
                )

            # Check if available slots < min_bullets
            total_slots = len(entity.slots)
            min_b = getattr(entity, "min_bullets", 0)
            if total_slots < min_b:
                return InfeasibilityReason(
                    conflict_type="MIN_BULLETS_UNSATISFIABLE",
                    details=(
                        f"Entity '{entity.id}' requires at least {min_b} bullets, "
                        f"but only has {total_slots} total slots."
                    ),
                    conflicting_slots=[s.id for s in entity.slots],
                    required_lines=min_lines_needed,
                    available_lines=capacity_lines,
                )

            # Non-mandatory min_bullets line contribution
            if mandatory_count < min_b:
                remaining_needed = min_b - mandatory_count
                optional_slots = [
                    s for s in entity.slots
                    if not (getattr(s, "mandatory", False) or getattr(s, "pinned", False))
                ]
                # Smallest variant lines among optional slots
                optional_min_lines = sorted(
                    min((self._get_variant_lines(v) for v in s.variants), default=1)
                    for s in optional_slots
                )
                min_lines_needed += sum(optional_min_lines[:remaining_needed])

        if min_lines_needed > capacity_lines:
            return InfeasibilityReason(
                conflict_type="LINE_BUDGET",
                details=(
                    f"Required constraints (mandatory slots + entity min_bullets) demand at least "
                    f"{min_lines_needed} lines, which exceeds page capacity of {capacity_lines} lines."
                ),
                conflicting_slots=conflicting_slots,
                required_lines=min_lines_needed,
                available_lines=capacity_lines,
            )

        return InfeasibilityReason(
            conflict_type="CONSTRAINTS_CONFLICT",
            details="Solver determined the instance is infeasible under active constraints.",
            conflicting_slots=conflicting_slots,
            required_lines=min_lines_needed,
            available_lines=capacity_lines,
        )

    def optimize(
        self,
        entities: Sequence[Any],
        requirements: Sequence[Any],
        capacity_lines: int,
    ) -> OptimizationResult:
        """Solve the bullet selection ILP problem using OR-Tools CP-SAT."""
        start_time = time.perf_counter()

        # 1. First run fast infeasibility pre-check
        infeasibility_precheck = self._diagnose_infeasibility(entities, capacity_lines)
        if infeasibility_precheck.conflict_type in {"LINE_BUDGET", "MAX_BULLETS_CONFLICT", "MIN_BULLETS_UNSATISFIABLE"}:
            return OptimizationResult(
                success=False,
                selection=None,
                infeasibility_reason=infeasibility_precheck,
            )

        model = cp_model.CpModel()

        # 2. Decision variables
        # x[(slot_id, variant_id)] -> BoolVar
        x_vars: dict[tuple[str, str], cp_model.IntVar] = {}
        slot_to_vars: dict[str, list[cp_model.IntVar]] = {}
        slot_to_entity: dict[str, str] = {}
        var_to_variant_obj: dict[tuple[str, str], Any] = {}
        all_slots: list[Any] = []

        for entity in entities:
            for slot in entity.slots:
                all_slots.append(slot)
                slot_to_entity[slot.id] = entity.id
                slot_to_vars[slot.id] = []
                for variant in slot.variants:
                    var_key = (slot.id, variant.id)
                    var_name = f"x_{slot.id}_{variant.id}"
                    var = model.new_bool_var(var_name)
                    x_vars[var_key] = var
                    slot_to_vars[slot.id].append(var)
                    var_to_variant_obj[var_key] = variant

        # 3. Constraints: Slot exclusivity & Mandatory/Pinned
        for slot in all_slots:
            vars_for_slot = slot_to_vars[slot.id]
            is_forced = getattr(slot, "mandatory", False) or getattr(slot, "pinned", False)
            if is_forced:
                # Exactly 1 variant must be selected
                model.add(sum(vars_for_slot) == 1)
            else:
                # At most 1 variant can be selected
                model.add(sum(vars_for_slot) <= 1)

        # 4. Constraints: Entity min/max bullet bounds
        for entity in entities:
            entity_vars: list[cp_model.IntVar] = []
            for slot in entity.slots:
                entity_vars.extend(slot_to_vars[slot.id])

            min_b = getattr(entity, "min_bullets", 0)
            max_b = getattr(entity, "max_bullets", len(entity.slots))
            model.add(sum(entity_vars) >= min_b)
            model.add(sum(entity_vars) <= max_b)

        # 5. Constraints: Line budget
        line_terms: list[Any] = []
        for var_key, var in x_vars.items():
            variant = var_to_variant_obj[var_key]
            lines = self._get_variant_lines(variant)
            line_terms.append(lines * var)
        model.add(sum(line_terms) <= capacity_lines)

        # 6. Requirement coverage variables and linking
        req_tuples: list[tuple[str, str, int]] = []
        for r in requirements:
            if hasattr(r, "canonical_id"):
                cid = (r.canonical_id or r.surface_form).lower()
                cat_val = getattr(r.category, "value", str(r.category))
                w = int(self.weight_scale * (1.0 if cat_val == "must_have" else 0.5))
                req_tuples.append((r.id, cid, w))
            else:
                req_tuples.append((r[0], r[1].lower(), int(self.weight_scale * float(r[2]))))

        covered_vars: dict[str, cp_model.IntVar] = {}
        for rid, cid, _ in req_tuples:
            cov_var = model.new_bool_var(f"cov_{rid}")
            covered_vars[rid] = cov_var

            # Find all variants containing cid
            matching_x_vars: list[cp_model.IntVar] = []
            for var_key, var in x_vars.items():
                variant = var_to_variant_obj[var_key]
                tags = [t.lower() for t in getattr(variant, "canonical_tags", [])]
                if cid in tags:
                    matching_x_vars.append(var)

            if not matching_x_vars:
                # Impossible to cover
                model.add(cov_var == 0)
            else:
                # cov_var <= sum(matching_x_vars)
                model.add(cov_var <= sum(matching_x_vars))
                # for each matching var, cov_var >= matching_var
                for mx in matching_x_vars:
                    model.add(cov_var >= mx)

        # 7. Objective Function: Maximize weighted coverage + utility - line tie-breaker
        objective_terms: list[Any] = []

        # Coverage terms
        for rid, _, w in req_tuples:
            objective_terms.append(w * covered_vars[rid])

        # Utility terms and line penalty
        for var_key, var in x_vars.items():
            variant = var_to_variant_obj[var_key]
            utility = int(self.utility_scale * round(getattr(variant, "utility", 0.0), 2))
            lines = self._get_variant_lines(variant)
            # Combine utility bonus and line tie-breaker
            coeff = utility - lines
            objective_terms.append(coeff * var)

        model.maximize(sum(objective_terms))

        # 8. Solve with single thread and fixed random seed for strict determinism
        solver = cp_model.CpSolver()
        solver.parameters.random_seed = self.random_seed
        solver.parameters.num_search_workers = 1
        solver.parameters.max_time_in_seconds = 30.0

        status = solver.solve(model)
        elapsed = time.perf_counter() - start_time

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            diagnosis = self._diagnose_infeasibility(entities, capacity_lines)
            return OptimizationResult(
                success=False,
                selection=None,
                infeasibility_reason=diagnosis,
            )

        # 9. Extract solution
        selected_bullets: list[SelectedBullet] = []
        slot_assignment: dict[str, str | None] = {s.id: None for s in all_slots}
        total_used_lines = 0

        for var_key, var in x_vars.items():
            if solver.value(var) == 1:
                slot_id, variant_id = var_key
                variant = var_to_variant_obj[var_key]
                slot_assignment[slot_id] = variant_id
                v_lines = self._get_variant_lines(variant)
                total_used_lines += v_lines
                selected_bullets.append(
                    SelectedBullet(
                        slot_id=slot_id,
                        variant_id=variant_id,
                        entity_id=slot_to_entity[slot_id],
                        text=variant.text,
                        lines=v_lines,
                        utility=getattr(variant, "utility", 0.0),
                        canonical_tags=getattr(variant, "canonical_tags", []),
                    )
                )

        covered_req_ids = sorted(
            rid for rid in covered_vars
            if solver.value(covered_vars[rid]) == 1
        )

        status_str = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
        selection = Selection(
            selected_bullets=selected_bullets,
            slot_assignment=slot_assignment,
            total_lines=total_used_lines,
            covered_requirements=covered_req_ids,
            objective_value=float(solver.objective_value),
            solve_time_seconds=elapsed,
            solver_status=status_str,
        )

        return OptimizationResult(
            success=True,
            selection=selection,
            infeasibility_reason=None,
        )
