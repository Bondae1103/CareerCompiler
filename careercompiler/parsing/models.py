"""Data structures for Tier 1 Hierarchical Document Tree Parser."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class SectionKind(StrEnum):
    """Canonical classification for document sections."""

    RESPONSIBILITIES = "responsibilities"
    REQUIREMENTS = "requirements"
    PREFERRED = "preferred"
    ABOUT = "about"
    BENEFITS = "benefits"
    UNCLASSIFIED = "unclassified"


class DocSpan(BaseModel):
    """Character span with exact source start and end offsets."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    start: int = Field(ge=0, description="0-indexed start character offset in original source.")
    end: int = Field(ge=0, description="0-indexed exclusive end character offset in original source.")
    raw_text: str = Field(description="Exact substring of source[start:end].")

    @property
    def clean_text(self) -> str:
        """Normalized text with collapsed whitespace for comparison."""
        return " ".join(self.raw_text.split())


class DocItem(BaseModel):
    """A leaf item: bullet, list item, or paragraph clause."""

    model_config = ConfigDict(extra="forbid")

    id: str
    item_type: str = Field(description="'bullet', 'paragraph', 'header', or 'clause'")
    span: DocSpan
    bullet_marker: str | None = None
    indent_level: int = 0


class DocSection(BaseModel):
    """A logical document section."""

    model_config = ConfigDict(extra="forbid")

    id: str
    title: str | None = None
    title_span: DocSpan | None = None
    kind: SectionKind
    span: DocSpan
    items: list[DocItem] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    """Full hierarchical document tree."""

    model_config = ConfigDict(extra="forbid")

    raw_text: str
    sections: list[DocSection] = Field(default_factory=list)

    def all_leaf_items(self) -> list[DocItem]:
        """Flatten and return all leaf items across all sections."""
        items: list[DocItem] = []
        for sec in self.sections:
            items.extend(sec.items)
        return items

    def verify_offsets(self) -> bool:
        """Verify that every span matches the source text exactly."""
        for sec in self.sections:
            if self.raw_text[sec.span.start : sec.span.end] != sec.span.raw_text:
                return False
            if sec.title_span:
                if self.raw_text[sec.title_span.start : sec.title_span.end] != sec.title_span.raw_text:
                    return False
            for item in sec.items:
                if self.raw_text[item.span.start : item.span.end] != item.span.raw_text:
                    return False
        return True

    def calculate_non_whitespace_coverage(self) -> float:
        """Calculate the proportion of non-whitespace characters in source covered by leaf items."""
        covered_indices: set[int] = set()
        for item in self.all_leaf_items():
            for i in range(item.span.start, item.span.end):
                if not self.raw_text[i].isspace():
                    covered_indices.add(i)

        # Also include section titles if not already items
        for sec in self.sections:
            if sec.title_span:
                for i in range(sec.title_span.start, sec.title_span.end):
                    if not self.raw_text[i].isspace():
                        covered_indices.add(i)

        total_non_whitespace = sum(1 for c in self.raw_text if not c.isspace())
        if total_non_whitespace == 0:
            return 1.0

        return len(covered_indices) / total_non_whitespace
