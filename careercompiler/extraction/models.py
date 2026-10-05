"""Domain models for Tier 3 Constrained Semantic Extractor (JD Chunk Schema)."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RequirementCategory(StrEnum):
    """Categorical classification of candidate qualifications."""

    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"


class ExtractedRequirement(BaseModel):
    """A single skill, qualification, or competency extracted from JD text."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(description="Unique deterministic ID for this extracted requirement.")
    canonical_id: str | None = Field(
        default=None,
        description="Resolved canonical taxonomy ID, or None if unmapped.",
    )
    surface_form: str = Field(description="Exact surface form of skill or qualification.")
    evidence_span: tuple[int, int] = Field(
        description="Character offset span [start, end] into raw source JD text."
    )
    evidence_text: str = Field(description="Exact substring of the source text at evidence_span.")
    category: RequirementCategory = Field(description="Requirement category (must_have vs nice_to_have).")
    required_years: float | None = Field(
        default=None,
        description="Minimum years of experience required, attested in evidence text.",
    )
    importance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Normalized importance score between 0.0 and 1.0.",
    )
    cue_phrase: str | None = Field(
        default=None,
        description="Cue phrase indicating requirement level (e.g. 'required', 'preferred').",
    )
    unmapped: bool = Field(
        default=False,
        description="True if term could not be mapped to the canonical taxonomy catalog.",
    )

    @model_validator(mode="after")
    def validate_spans_and_evidence(self) -> "ExtractedRequirement":
        start, end = self.evidence_span
        if start < 0:
            raise ValueError(f"Span start ({start}) must be non-negative.")
        if end <= start:
            raise ValueError(f"Span end ({end}) must be strictly greater than start ({start}).")
        if len(self.evidence_text) != (end - start):
            raise ValueError(
                f"Evidence text length ({len(self.evidence_text)}) does not match span length ({end - start})."
            )
        return self


class ScaleIndicator(BaseModel):
    """Scale, throughput, telemetry, or volume metric present in JD."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(description="Unique identifier for this scale indicator.")
    metric: str = Field(description="Metric domain or dimension (e.g. 'throughput', 'users', 'data_volume').")
    value: str = Field(description="Quantified scale metric surface string (e.g. '10M+', '45k ops/sec').")
    evidence_span: tuple[int, int] = Field(
        description="Character offset span [start, end] into raw source JD text."
    )
    evidence_text: str = Field(description="Exact substring of source text at evidence_span.")

    @model_validator(mode="after")
    def validate_scale_spans(self) -> "ScaleIndicator":
        start, end = self.evidence_span
        if start < 0:
            raise ValueError(f"Span start ({start}) must be non-negative.")
        if end <= start:
            raise ValueError(f"Span end ({end}) must be strictly greater than start ({start}).")
        if len(self.evidence_text) != (end - start):
            raise ValueError(
                f"Evidence text length ({len(self.evidence_text)}) does not match span length ({end - start})."
            )
        return self


class ExtractedJD(BaseModel):
    """Structured extraction output container for a Job Description."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    role_title: str = Field(description="Extracted or inferred role title.")
    role_title_span: tuple[int, int] | None = Field(
        default=None,
        description="Character offset span of the role title in JD text, if directly attested.",
    )
    hard_requirements: list[ExtractedRequirement] = Field(
        default_factory=list,
        description="Mandatory / must-have requirements.",
    )
    preferred_qualifications: list[ExtractedRequirement] = Field(
        default_factory=list,
        description="Bonus / preferred qualifications.",
    )
    scale_indicators: list[ScaleIndicator] = Field(
        default_factory=list,
        description="Identified scale and throughput dimensions.",
    )
    dropped_items_count: int = Field(
        default=0,
        description="Counter of candidate items dropped due to validation failure.",
    )
    validation_warnings: list[str] = Field(
        default_factory=list,
        description="Audit log of dropped items and validation reasons.",
    )
    extractor_name: str = Field(description="Name of the extractor that produced this chunk.")
    extractor_version: str = Field(default="1.0.0", description="Version of the extractor.")
    cache_key: str = Field(description="Deterministic SHA-256 hash identifying input and configuration.")

    @property
    def all_requirements(self) -> list[ExtractedRequirement]:
        """Convenience property returning combined list of hard and preferred requirements."""
        return self.hard_requirements + self.preferred_qualifications
