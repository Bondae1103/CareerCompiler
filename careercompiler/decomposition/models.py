"""Domain models for Phase P6 Resume Bullet Decomposition (ACTR)."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from careercompiler.taxonomy.models import EntityMatch


class MetricQuality(StrEnum):
    """Categorical quality tier of accomplishment metrics in resume text."""

    NONE = "none"
    VAGUE = "vague"
    QUANTIFIED = "quantified"
    QUANTIFIED_WITH_BASELINE = "quantified_with_baseline"


class ImpactMetric(BaseModel):
    """An empirical metric extracted from bullet text with reversible normalization."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(description="Unique identifier for this metric.")
    raw_text: str = Field(description="Exact substring of the metric in source bullet text.")
    raw_span: tuple[int, int] = Field(description="Character offset span [start, end] into source text.")
    normalized_value: float = Field(description="Numerically parsed value (e.g. 45000.0 for '45k').")
    unit: str = Field(description="Extracted measurement unit (e.g. '%', 'ops/sec', 'ms', 'fps', 'count').")
    direction: str | None = Field(default=None, description="'increase', 'decrease', or 'absolute'.")
    baseline_value: float | None = Field(default=None, description="Pre-existing baseline if 'from X to Y'.")
    metric_type: str = Field(default="general", description="Metric dimension (throughput, latency, percentage).")

    @model_validator(mode="after")
    def validate_metric_span(self) -> "ImpactMetric":
        start, end = self.raw_span
        if start < 0:
            raise ValueError(f"Span start ({start}) must be non-negative.")
        if end <= start:
            raise ValueError(f"Span end ({end}) must be strictly greater than start ({start}).")
        if len(self.raw_text) != (end - start):
            raise ValueError(
                f"raw_text length ({len(self.raw_text)}) does not match span length ({end - start})."
            )
        return self


class ActionVerb(BaseModel):
    """Primary action verb initiating the accomplishment statement."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    verb: str = Field(description="Lemmatized or canonical action verb.")
    raw_span: tuple[int, int] = Field(description="Character offset span [start, end] in source text.")
    surface_form: str = Field(description="Exact surface string in source text.")
    tense: str = Field(default="past", description="Verb tense (past, present).")

    @model_validator(mode="after")
    def validate_verb_span(self) -> "ActionVerb":
        start, end = self.raw_span
        if start < 0 or end <= start or len(self.surface_form) != (end - start):
            raise ValueError(f"Invalid verb span [{start}, {end}] for '{self.surface_form}'.")
        return self


class DomainConcept(BaseModel):
    """Evidenced technical or business domain concept (A3 invariant)."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    concept: str = Field(description="Canonical concept slug or descriptor.")
    raw_span: tuple[int, int] = Field(description="Character offset span [start, end] in source text.")
    surface_form: str = Field(description="Exact surface substring in source text.")
    inferred: bool = Field(default=False, description="Flag for inferred non-lexical concepts.")

    @model_validator(mode="after")
    def validate_concept_span(self) -> "DomainConcept":
        start, end = self.raw_span
        if start < 0 or end <= start or len(self.surface_form) != (end - start):
            raise ValueError(f"Invalid concept span [{start}, {end}] for '{self.surface_form}'.")
        return self


class BulletDecomposition(BaseModel):
    """Full ACTR decomposition of an authored bullet variant."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    raw_text: str = Field(description="Full unmodified source bullet text.")
    action_verb: ActionVerb | None = Field(default=None, description="Initiating action verb.")
    technologies: list[EntityMatch] = Field(default_factory=list, description="Tier 2 entity matches.")
    domain_concepts: list[DomainConcept] = Field(default_factory=list, description="Evidenced domain concepts.")
    impact_metrics: list[ImpactMetric] = Field(default_factory=list, description="Extracted empirical metrics.")
    metric_quality: MetricQuality = Field(default=MetricQuality.NONE, description="Empirical quality tier.")
    canonical_tags: list[str] = Field(
        default_factory=list,
        description="Unified canonical IDs from technologies and evidenced concepts.",
    )
    cache_key: str = Field(description="SHA-256 hash of source bullet text.")
