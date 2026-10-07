"""Domain and result models for resume selection and ILP optimization."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class TruthInvariantViolationError(Exception):
    """Raised when an emitted bullet does not byte-identically match an authored bank variant."""


class SelectedBullet(BaseModel):
    """A chosen bullet variant assigned to a slot."""

    model_config = ConfigDict(extra="forbid")

    slot_id: str
    variant_id: str
    entity_id: str
    text: str
    lines: int
    utility: float
    canonical_tags: list[str] = Field(default_factory=list)


class InfeasibilityReason(BaseModel):
    """Structured explanation of why constraint satisfaction failed."""

    model_config = ConfigDict(extra="forbid")

    conflict_type: str  # "LINE_BUDGET", "MIN_BULLETS_OVERFLOW", "MANDATORY_CONFLICT"
    details: str
    conflicting_slots: list[str] = Field(default_factory=list)
    required_lines: int = 0
    available_lines: int = 0


class Selection(BaseModel):
    """Complete slot-to-variant assignment chosen by the optimizer."""

    model_config = ConfigDict(extra="forbid")

    selected_bullets: list[SelectedBullet]
    slot_assignment: dict[str, str | None]  # slot_id -> variant_id or None
    total_lines: int
    covered_requirements: list[str]
    objective_value: float
    solve_time_seconds: float
    solver_status: str  # "OPTIMAL", "FEASIBLE", "INFEASIBLE"

    def get_slot_variant_text_map(self) -> dict[str, str | None]:
        """Mapping from slot_id to text for direct rendering in ResumeTemplate."""
        text_map: dict[str, str | None] = {}
        bullet_map = {b.slot_id: b.text for b in self.selected_bullets}
        for slot_id in self.slot_assignment:
            text_map[slot_id] = bullet_map.get(slot_id, None)
        return text_map


class OptimizationResult(BaseModel):
    """Result of optimization with optional compile verification."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    selection: Selection | None = None
    infeasibility_reason: InfeasibilityReason | None = None
    iterations: int = 1
    compile_verified: bool = False
    pdf_path: Path | None = None
    verification_errors: list[str] = Field(default_factory=list)
