"""Domain models for selection diffs, score deltas, and 1-click reversions."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from careercompiler.scoring.models import ScoreBreakdown


class DiffActionType(StrEnum):
    """Categorization of what happened to a bullet slot during tailoring."""

    UNCHANGED = "UNCHANGED"
    SWAPPED = "SWAPPED"
    ADDED = "ADDED"
    OMITTED = "OMITTED"
    LLM_REWRITTEN = "LLM_REWRITTEN"


class BulletDiff(BaseModel):
    """Granular comparison of a single accomplishment slot between baseline and tailored states."""

    model_config = ConfigDict(extra="forbid")

    slot_id: str
    entity_id: str
    action: DiffActionType
    baseline_variant_id: str | None = None
    baseline_text: str | None = None
    tailored_variant_id: str | None = None
    tailored_text: str | None = None
    added_tags: list[str] = Field(default_factory=list)
    removed_tags: list[str] = Field(default_factory=list)
    line_delta: int = 0
    utility_delta: float = 0.0
    can_revert: bool = True
    revert_to_variant_id: str | None = None
    explanation: str = ""


class ScoreDelta(BaseModel):
    """Exact delta across multi-component ATS scoring between baseline and tailored resumes."""

    model_config = ConfigDict(extra="forbid")

    baseline_score: ScoreBreakdown
    tailored_score: ScoreBreakdown
    delta_total: float
    delta_lexical: float
    delta_bm25: float
    delta_semantic: float
    delta_quality: float
    newly_covered_requirements: list[str] = Field(default_factory=list)
    lost_requirements: list[str] = Field(default_factory=list)


class RevertRecord(BaseModel):
    """Audit log record for an individual slot rollback."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str
    slot_id: str
    previous_variant_id: str | None
    reverted_to_variant_id: str | None
    reason: str | None = None


class SelectionDiff(BaseModel):
    """Comprehensive resume tailoring diff with slot changes, score deltas, and audit history."""

    model_config = ConfigDict(extra="forbid")

    job_id: str | None = None
    profile_id: str
    bullet_diffs: list[BulletDiff]
    score_delta: ScoreDelta | None = None
    baseline_total_lines: int
    tailored_total_lines: int
    line_budget_delta: int
    total_swapped: int
    total_added: int
    total_omitted: int
    total_unchanged: int
    revert_history: list[RevertRecord] = Field(default_factory=list)
