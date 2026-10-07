"""Closed-loop resume optimization and compile verification pipeline."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from careercompiler.layout.template import ResumeTemplate
from careercompiler.layout.verifier import LayoutVerifier
from careercompiler.optimizer.models import (
    InfeasibilityReason,
    OptimizationResult,
    Selection,
    TruthInvariantViolationError,
)
from careercompiler.optimizer.solver import ILPOptimizer


class ClosedLoopOptimizer:
    """Orchestrates ILP bullet selection with closed-loop LaTeX compilation and Truth Invariant checks."""

    DEFAULT_TEMPLATE_PATH = Path("templates/resume.tex")
    DEFAULT_CAPACITY_LINES = 30
    DEFAULT_MAX_ITERATIONS = 5

    def __init__(
        self,
        solver: ILPOptimizer | None = None,
        verifier: LayoutVerifier | None = None,
        template: ResumeTemplate | None = None,
        template_path: Path | None = None,
        initial_capacity_lines: int = DEFAULT_CAPACITY_LINES,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> None:
        self.solver = solver or ILPOptimizer()
        self.verifier = verifier or LayoutVerifier()
        self.initial_capacity_lines = initial_capacity_lines
        self.max_iterations = max_iterations

        if template is not None:
            self.template: ResumeTemplate | None = template
        elif template_path is not None:
            self.template = ResumeTemplate(template_path.read_text(encoding="utf-8"))
        elif self.DEFAULT_TEMPLATE_PATH.exists():
            self.template = ResumeTemplate(self.DEFAULT_TEMPLATE_PATH.read_text(encoding="utf-8"))
        else:
            self.template = None

    def verify_truth_invariant(self, entities: Sequence[Any], selection: Selection) -> None:
        """Assert that every selected bullet strictly exists in the authored bank variants and matches byte-for-byte.

        Raises:
            TruthInvariantViolationError: If an emitted bullet does not byte-identically match an authored bank variant.
        """
        authored_dict: dict[tuple[str, str], str] = {}
        for entity in entities:
            for slot in entity.slots:
                for variant in slot.variants:
                    authored_dict[(slot.id, variant.id)] = variant.text

        for bullet in selection.selected_bullets:
            key = (bullet.slot_id, bullet.variant_id)
            if key not in authored_dict:
                raise TruthInvariantViolationError(
                    f"Truth Invariant Violation: Selected bullet '{bullet.variant_id}' in slot '{bullet.slot_id}' "
                    f"does not exist in the authored profile bank."
                )
            authored_text = authored_dict[key]
            if bullet.text != authored_text:
                raise TruthInvariantViolationError(
                    f"Truth Invariant Violation: Bullet text for variant '{bullet.variant_id}' in slot '{bullet.slot_id}' "
                    f"has been modified from authored bank text.\n"
                    f"Expected: '{authored_text}'\n"
                    f"Emitted:  '{bullet.text}'"
                )

    def optimize_and_verify(
        self,
        entities: Any,
        requirements: Sequence[Any],
        capacity_lines: int | None = None,
        work_dir: Path | None = None,
        enforce_truth_invariant: bool = True,
    ) -> OptimizationResult:
        """Solve bullet selection, verify Truth Invariant, and verify closed-loop 1-page compilation.

        If layout verification detects page overflow (> 1 page), decrements line capacity by 1
        and re-solves, up to max_iterations.
        """
        # Support passing a Profile domain model directly
        if hasattr(entities, "experiences") and hasattr(entities, "projects"):
            raw_entities = list(entities.experiences) + list(entities.projects)
        else:
            raw_entities = list(entities)

        current_capacity = capacity_lines if capacity_lines is not None else self.initial_capacity_lines
        last_result: OptimizationResult | None = None
        last_errors: list[str] = []

        for iteration in range(1, self.max_iterations + 1):
            opt_result = self.solver.optimize(raw_entities, requirements, capacity_lines=current_capacity)
            opt_result.iterations = iteration
            last_result = opt_result

            if not opt_result.success or opt_result.selection is None:
                # Infeasible under current capacity
                return opt_result

            # 1. Truth Invariant check
            if enforce_truth_invariant:
                self.verify_truth_invariant(raw_entities, opt_result.selection)

            # 2. Template compile check
            if self.template is None:
                # No template provided; return solver-level success
                opt_result.compile_verified = False
                return opt_result

            slot_texts = opt_result.selection.get_slot_variant_text_map()
            rendered_tex = self.template.render(slot_texts)
            expected_texts = [b.text for b in opt_result.selection.selected_bullets]

            build_res = self.verifier.compile_and_verify(
                rendered_tex,
                expected_bullet_texts=expected_texts,
                work_dir=work_dir,
            )

            if build_res.success:
                return OptimizationResult(
                    success=True,
                    selection=opt_result.selection,
                    infeasibility_reason=None,
                    iterations=iteration,
                    compile_verified=True,
                    pdf_path=build_res.pdf_path,
                    verification_errors=[],
                )

            last_errors = build_res.errors

            # If page overflowed, decrement budget by 1 line and re-solve
            if build_res.page_count > 1:
                current_capacity -= 1
                continue
            else:
                # Unrecoverable error (e.g. LaTeX compile crash or missing bullets)
                return OptimizationResult(
                    success=False,
                    selection=opt_result.selection,
                    infeasibility_reason=None,
                    iterations=iteration,
                    compile_verified=False,
                    pdf_path=build_res.pdf_path,
                    verification_errors=build_res.errors,
                )

        # If loop finishes without success
        return OptimizationResult(
            success=False,
            selection=last_result.selection if last_result else None,
            infeasibility_reason=InfeasibilityReason(
                conflict_type="LINE_BUDGET",
                details=f"Failed to achieve single-page fit after {self.max_iterations} iterations.",
                conflicting_slots=[],
                required_lines=current_capacity,
                available_lines=self.initial_capacity_lines,
            ),
            iterations=self.max_iterations,
            compile_verified=False,
            verification_errors=last_errors or ["Exceeded maximum closed-loop optimization iterations."],
        )
