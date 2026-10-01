"""Pydantic domain models for Master Profile Bank."""

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
CONTROL_CHARS_REGEX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

EntityId = Annotated[
    str,
    Field(
        description="Unique identifier using alphanumeric, underscores, and dashes.",
        min_length=1,
        max_length=64,
    ),
]


def _validate_id(value: str) -> str:
    if not ID_REGEX.match(value):
        raise ValueError(f"Invalid ID '{value}'. Must match pattern '^[a-zA-Z0-9_-]{{1,64}}$'.")
    return value


def _validate_text(value: str, max_length: int = 1000) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Text cannot be empty or purely whitespace.")
    if len(cleaned) > max_length:
        raise ValueError(f"Text length {len(cleaned)} exceeds maximum limit of {max_length}.")
    if CONTROL_CHARS_REGEX.search(cleaned):
        raise ValueError("Text contains forbidden control characters.")
    return cleaned


class BulletVariant(BaseModel):
    """An authored variant of a bullet point emphasizing a specific angle."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: EntityId
    text: str
    angle: str = Field(description="Angle/focus: e.g. performance, architecture, product, general.")
    sort_order: int = 0
    is_default: bool = False
    canonical_tags: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _validate_id(v)

    @field_validator("text")
    @classmethod
    def check_text(cls, v: str) -> str:
        return _validate_text(v, max_length=1000)

    @field_validator("angle")
    @classmethod
    def check_angle(cls, v: str) -> str:
        return _validate_text(v, max_length=64)


class BulletSlot(BaseModel):
    """A logical accomplishment slot containing one or more authored variants."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: EntityId
    name: str = Field(description="Short human-readable descriptor of this accomplishment.")
    pinned: bool = Field(default=False, description="Must be selected if parent entity is included.")
    mandatory: bool = Field(default=False, description="Must be included in any generated resume.")
    variants: list[BulletVariant] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _validate_id(v)

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str) -> str:
        return _validate_text(v, max_length=128)

    @model_validator(mode="after")
    def validate_variants(self) -> "BulletSlot":
        variant_ids = [v.id for v in self.variants]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError(f"Duplicate variant IDs found in slot '{self.id}': {variant_ids}")

        defaults = [v for v in self.variants if v.is_default]
        if len(defaults) == 0:
            # Designate first variant as default if none explicitly marked
            self.variants[0].is_default = True
        elif len(defaults) > 1:
            raise ValueError(
                f"Slot '{self.id}' has multiple default variants: {[v.id for v in defaults]}. "
                "Exactly one variant must be designated as default."
            )

        return self

    def get_default_variant(self) -> BulletVariant:
        for v in self.variants:
            if v.is_default:
                return v
        return self.variants[0]


class Experience(BaseModel):
    """Professional work experience or internship."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: EntityId
    company: str
    location: str
    title: str
    start_date: str
    end_date: str
    min_bullets: int = 1
    max_bullets: int = 4
    slots: list[BulletSlot] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _validate_id(v)

    @model_validator(mode="after")
    def validate_slot_bounds(self) -> "Experience":
        if self.min_bullets < 0:
            raise ValueError(f"min_bullets must be >= 0, got {self.min_bullets}")
        if self.max_bullets < self.min_bullets:
            raise ValueError(f"max_bullets ({self.max_bullets}) cannot be less than min_bullets ({self.min_bullets})")

        slot_ids = [s.id for s in self.slots]
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError(f"Duplicate slot IDs found in experience '{self.id}': {slot_ids}")

        return self


class Project(BaseModel):
    """Personal, academic, or open-source software project."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: EntityId
    title: str
    tools: list[str] = Field(default_factory=list)
    url: str | None = None
    github_url: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    min_bullets: int = 1
    max_bullets: int = 3
    slots: list[BulletSlot] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _validate_id(v)

    @model_validator(mode="after")
    def validate_project_bounds(self) -> "Project":
        if self.min_bullets < 0:
            raise ValueError(f"min_bullets must be >= 0, got {self.min_bullets}")
        if self.max_bullets < self.min_bullets:
            raise ValueError(f"max_bullets ({self.max_bullets}) cannot be less than min_bullets ({self.min_bullets})")

        slot_ids = [s.id for s in self.slots]
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError(f"Duplicate slot IDs found in project '{self.id}': {slot_ids}")

        return self


class Education(BaseModel):
    """Educational qualification."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: EntityId
    institution: str
    location: str
    degree: str
    dates: str
    details: str | None = None

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _validate_id(v)


class Publication(BaseModel):
    """Research paper or conference publication."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: EntityId
    title: str
    venue: str
    year: int
    authors: list[str] = Field(default_factory=list)
    url: str | None = None

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _validate_id(v)


class SkillGroup(BaseModel):
    """Group of technical or domain skills."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: EntityId
    category: str
    skills: list[str] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _validate_id(v)


class ContactInfo(BaseModel):
    """User contact details."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: str
    phone: str
    email: str
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None


class Profile(BaseModel):
    """Master Profile Bank — authoritative source of all candidate career data."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: EntityId
    version: int = 1
    contact: ContactInfo
    education: list[Education] = Field(default_factory=list)
    experiences: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    publications: list[Publication] = Field(default_factory=list)
    skill_groups: list[SkillGroup] = Field(default_factory=list)
    leadership: list[BulletSlot] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _validate_id(v)

    @model_validator(mode="after")
    def validate_unique_entity_ids(self) -> "Profile":
        # Check uniqueness across experience IDs
        exp_ids = [e.id for e in self.experiences]
        if len(exp_ids) != len(set(exp_ids)):
            raise ValueError(f"Duplicate experience IDs found: {exp_ids}")

        # Check uniqueness across project IDs
        proj_ids = [p.id for p in self.projects]
        if len(proj_ids) != len(set(proj_ids)):
            raise ValueError(f"Duplicate project IDs found: {proj_ids}")

        # Check uniqueness across education IDs
        edu_ids = [ed.id for ed in self.education]
        if len(edu_ids) != len(set(edu_ids)):
            raise ValueError(f"Duplicate education IDs found: {edu_ids}")

        # Check uniqueness across leadership slot IDs
        lead_ids = [ls.id for ls in self.leadership]
        if len(lead_ids) != len(set(lead_ids)):
            raise ValueError(f"Duplicate leadership slot IDs found: {lead_ids}")

        return self
