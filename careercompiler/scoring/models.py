"""Domain and configuration models for resume scoring and explainability."""

import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from careercompiler.decomposition.models import MetricQuality


class RequirementWeights(BaseModel):
    """Weights assigned to JD requirement categories."""

    model_config = ConfigDict(extra="forbid")

    must_have: float = Field(default=1.0, ge=0.0)
    nice_to_have: float = Field(default=0.5, ge=0.0)


class CombinerWeights(BaseModel):
    """Linear weights for combining normalized score components (must sum to 1.0)."""

    model_config = ConfigDict(extra="forbid")

    weight_lexical: float = Field(default=0.40, ge=0.0, le=1.0)
    weight_bm25: float = Field(default=0.25, ge=0.0, le=1.0)
    weight_semantic: float = Field(default=0.20, ge=0.0, le=1.0)
    weight_quality: float = Field(default=0.15, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "CombinerWeights":
        total = self.weight_lexical + self.weight_bm25 + self.weight_semantic + self.weight_quality
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"Combiner weights must sum to 1.0, got {total:.4f}")
        return self


class MetricQualityConfig(BaseModel):
    """Score multipliers and utility bonuses for metric quality tiers."""

    model_config = ConfigDict(extra="forbid")

    none: float = 0.00
    vague: float = 0.25
    quantified: float = 0.75
    quantified_with_baseline: float = 1.00

    bonus_none: float = 0.00
    bonus_vague: float = 0.05
    bonus_quantified: float = 0.15
    bonus_quantified_with_baseline: float = 0.25


class BM25Config(BaseModel):
    """Okapi BM25 hyperparameters and corpus mode."""

    model_config = ConfigDict(extra="forbid")

    k1: float = Field(default=1.5, ge=0.0)
    b: float = Field(default=0.75, ge=0.0, le=1.0)
    k_norm: float = Field(default=5.0, gt=0.0)
    corpus_mode: str = Field(default="bank_plus_jd")


class SemanticConfig(BaseModel):
    """Configuration for local semantic embeddings."""

    model_config = ConfigDict(extra="forbid")

    default_provider: str = "hashing_ngram"
    embedding_dim: int = 128
    ngram_min: int = 2
    ngram_max: int = 4
    hf_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    hf_model_revision: str = "e4ce9877abf3ed59ced85d39f62ed50bfd257372"


class UtilityConfig(BaseModel):
    """Weights and penalties for single-bullet slot utility U(b)."""

    model_config = ConfigDict(extra="forbid")

    alpha_relevance: float = 0.60
    beta_quality: float = 0.30
    gamma_line_cost: float = 0.10
    overflow_line_cost: float = 0.05


class ScoringConfig(BaseModel):
    """Top-level configuration loaded from scoring.toml."""

    model_config = ConfigDict(extra="forbid")

    version: str = "1.0.0"
    calibration_status: str = "UNCALIBRATED"
    requirements: RequirementWeights = Field(default_factory=RequirementWeights)
    combiner: CombinerWeights = Field(default_factory=CombinerWeights)
    metric_quality: MetricQualityConfig = Field(default_factory=MetricQualityConfig)
    bm25: BM25Config = Field(default_factory=BM25Config)
    semantic: SemanticConfig = Field(default_factory=SemanticConfig)
    utility: UtilityConfig = Field(default_factory=UtilityConfig)

    @classmethod
    def load_from_toml(cls, path: Path | None = None) -> "ScoringConfig":
        """Load configuration from a TOML file path or default package path."""
        if path is None:
            path = Path(__file__).parent / "scoring.toml"
        if not path.exists():
            return cls()

        with open(path, "rb") as f:
            data = tomllib.load(f)

        meta = data.get("meta", {})
        return cls(
            version=meta.get("version", "1.0.0"),
            calibration_status=meta.get("calibration_status", "UNCALIBRATED"),
            requirements=RequirementWeights(**data.get("requirements", {})),
            combiner=CombinerWeights(**data.get("combiner", {})),
            metric_quality=MetricQualityConfig(**data.get("metric_quality", {})),
            bm25=BM25Config(**data.get("bm25", {})),
            semantic=SemanticConfig(**data.get("semantic", {})),
            utility=UtilityConfig(**data.get("utility", {})),
        )


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown guaranteeing the Explainability Invariant."""

    model_config = ConfigDict(extra="forbid")

    total_score: float = Field(ge=0.0, le=100.0)
    lexical_score: float = Field(ge=0.0, le=100.0)
    bm25_score: float = Field(ge=0.0, le=100.0)
    semantic_score: float = Field(ge=0.0, le=100.0)
    quality_score: float = Field(ge=0.0, le=100.0)

    coverage_count: int = Field(ge=0)
    total_requirements: int = Field(ge=0)
    covered_requirements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)

    component_contributions: dict[str, float] = Field(default_factory=dict)

    @field_validator("component_contributions")
    @classmethod
    def validate_contributions(cls, v: dict[str, float]) -> dict[str, float]:
        required_keys = {"lexical", "bm25", "semantic", "quality"}
        if not required_keys.issubset(v.keys()):
            raise ValueError(f"component_contributions missing required keys: {required_keys - set(v.keys())}")
        return v

    @model_validator(mode="after")
    def validate_explainability_sum(self) -> "ScoreBreakdown":
        summed = sum(self.component_contributions.values())
        if abs(self.total_score - summed) > 1e-3:
            raise ValueError(
                f"Explainability Invariant violated: total_score={self.total_score:.4f} != "
                f"sum of contributions={summed:.4f}"
            )
        return self


class BulletUtility(BaseModel):
    """Slot-level utility score and breakdown for ranking candidate variants."""

    model_config = ConfigDict(extra="forbid")

    bullet_id: str
    total_utility: float
    lexical_contribution: float
    bm25_contribution: float
    semantic_contribution: float
    quality_bonus: float
    line_penalty: float
    matched_requirements: list[str] = Field(default_factory=list)
    explanation: str


class ScorableBullet(BaseModel):
    """Minimal typed adapter for a bullet being scored."""

    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    canonical_tags: list[str] = Field(default_factory=list)
    metric_quality: MetricQuality = MetricQuality.NONE
    lines: int = 1
