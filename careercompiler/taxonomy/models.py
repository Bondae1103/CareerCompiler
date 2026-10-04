"""Domain models for Tier 2 Entity Gazetteer and Taxonomy."""

import re
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CANONICAL_ID_REGEX = re.compile(r"^[a-z0-9_-]{1,64}$")


class EntityType(StrEnum):
    """Categorical type for taxonomy entities."""

    LANGUAGE = "language"
    FRAMEWORK = "framework"
    LIBRARY = "library"
    DATABASE = "database"
    CLOUD = "cloud"
    TOOL = "tool"
    DEVOPS = "devops"
    CONCEPT = "concept"
    METHODOLOGY = "methodology"
    PLATFORM = "platform"


class DisambiguationRule(BaseModel):
    """Declarative disambiguation rule for ambiguous or short entities."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_sensitive: bool = True
    requires_context: bool = False
    context_keywords: list[str] = Field(default_factory=list)
    trigger_patterns: list[str] = Field(default_factory=list)
    negative_patterns: list[str] = Field(default_factory=list)


class TaxonomyEntity(BaseModel):
    """Canonical taxonomy entity definition with licensing and provenance."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    canonical_id: Annotated[
        str,
        Field(
            description="Globally unique canonical identifier in lowercase slug format.",
            min_length=1,
            max_length=64,
        ),
    ]
    display_name: str = Field(description="Canonical human-readable display name.")
    type: EntityType = Field(description="Categorical entity classification.")
    aliases: list[str] = Field(min_length=1, description="Recognized aliases and surface forms.")
    ambiguous: bool = Field(default=False, description="Flag indicating common-word or collision ambiguity.")
    disambiguation_rules: list[DisambiguationRule] = Field(
        default_factory=list,
        description="Data-driven rules evaluated before accepting a match.",
    )
    source: str = Field(description="Provenance source repository or dataset.")
    license: str = Field(description="Open source license governing redistribution.")
    version: str = Field(default="1.0.0", description="Taxonomy dataset version.")
    reviewed: bool = Field(default=True, description="Human or peer review status flag.")

    @field_validator("canonical_id")
    @classmethod
    def validate_canonical_id(cls, v: str) -> str:
        if not CANONICAL_ID_REGEX.match(v):
            raise ValueError(f"Invalid canonical_id '{v}'. Must match pattern '^[a-z0-9_-]{{1,64}}$'.")
        return v

    @field_validator("aliases")
    @classmethod
    def validate_aliases(cls, v: list[str]) -> list[str]:
        cleaned: list[str] = []
        for alias in v:
            a = alias.strip()
            if not a:
                raise ValueError("Aliases cannot be empty strings.")
            if a not in cleaned:
                cleaned.append(a)
        if not cleaned:
            raise ValueError("Entity must have at least one valid alias.")
        return cleaned


class EntityMatch(BaseModel):
    """An exact, boundary-safe entity match in text."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    canonical_id: str
    surface_form: str
    start: int = Field(ge=0, description="0-indexed start character offset in source text.")
    end: int = Field(gt=0, description="0-indexed exclusive end character offset in source text.")
    confidence_source: str = Field(default="exact_alias")
    entity_type: EntityType | None = None

    @model_validator(mode="after")
    def validate_offsets(self) -> "EntityMatch":
        if self.end <= self.start:
            raise ValueError(f"end ({self.end}) must be strictly greater than start ({self.start})")
        return self


class TaxonomyCatalog(BaseModel):
    """In-memory collection of taxonomy entities with lookup indexes."""

    model_config = ConfigDict(extra="forbid")

    entities: list[TaxonomyEntity] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_canonical_ids(self) -> "TaxonomyCatalog":
        ids: set[str] = set()
        for e in self.entities:
            if e.canonical_id in ids:
                raise ValueError(f"Duplicate canonical_id '{e.canonical_id}' in taxonomy catalog.")
            ids.add(e.canonical_id)
        return self

    def get_by_id(self, canonical_id: str) -> TaxonomyEntity | None:
        """Lookup entity by canonical ID."""
        for e in self.entities:
            if e.canonical_id == canonical_id:
                return e
        return None

    def canonicalize(self, term: str) -> str | None:
        """Resolve a term to canonical_id using exact and case-insensitive alias lookups."""
        term_clean = term.strip()
        if not term_clean:
            return None

        # 1. Exact match against canonical_id
        canonical_low = term_clean.lower()
        entity = self.get_by_id(canonical_low)
        if entity:
            return entity.canonical_id

        # 2. Exact match against aliases
        for e in self.entities:
            for alias in e.aliases:
                if alias == term_clean:
                    return e.canonical_id

        # 3. Case-insensitive alias match (for unambiguous entities)
        for e in self.entities:
            if not e.ambiguous:
                for alias in e.aliases:
                    if alias.lower() == canonical_low:
                        return e.canonical_id

        return None
