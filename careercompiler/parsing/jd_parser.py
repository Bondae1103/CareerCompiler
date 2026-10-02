"""Tier 1 Hierarchical Job Description Parser."""

import re
from dataclasses import dataclass, field

from careercompiler.parsing.models import (
    DocItem,
    DocSection,
    DocSpan,
    ParsedDocument,
    SectionKind,
)

# Heading classification patterns
HEADING_PATTERNS: list[tuple[SectionKind, re.Pattern[str]]] = [
    (
        SectionKind.PREFERRED,
        re.compile(
            r"^(?:#{1,6}\s+)?(?:\*\*)?(?:preferred qualifications|nice to have|bonus|desired skills|good to have|preferred)(?:\*\*)?[:\s]*$",
            re.IGNORECASE,
        ),
    ),
    (
        SectionKind.REQUIREMENTS,
        re.compile(
            r"^(?:#{1,6}\s+)?(?:\*\*)?(?:required qualifications|prerequisites|eligibility|requirements|basic qualifications|must have|who we(?:'|’)?re looking for|selection process|minimum qualifications|qualifications)(?:\*\*)?[:\s]*$",
            re.IGNORECASE,
        ),
    ),
    (
        SectionKind.RESPONSIBILITIES,
        re.compile(
            r"^(?:#{1,6}\s+)?(?:\*\*)?(?:responsibilities|what you(?:'|’)?ll do|what you will do|what you will work on|role (?:and|&) responsibilities|key responsibilities|indicative objectives|project objectives|lane\s+\d+\s*\|.*|what will you do)(?:\*\*)?[:\s]*$",
            re.IGNORECASE,
        ),
    ),
    (
        SectionKind.BENEFITS,
        re.compile(
            r"^(?:#{1,6}\s+)?(?:\*\*)?(?:why\s+[a-zA-Z0-9_-]+|what interns can expect|build your career here|benefits|perks|stipend|what we offer|compensation|duration|location)(?:\*\*)?[:\s]*$",
            re.IGNORECASE,
        ),
    ),
    (
        SectionKind.ABOUT,
        re.compile(
            r"^(?:#{1,6}\s+)?(?:\*\*)?(?:about us|about the business|who we are|about\s+[a-zA-Z0-9_-]+|company highlights|company overview|job summary|overview|about the company)(?:\*\*)?[:\s]*$",
            re.IGNORECASE,
        ),
    ),
]

# Bullet start pattern
BULLET_PATTERN = re.compile(
    r"^[ \t]*([•●▪*—\-\u25aa\u2022\u25cf\u2014]|\d{1,2}[\.\)]|\([a-zA-Z0-9]\))[ \t]+"
)


def _classify_heading(line_text: str) -> SectionKind | None:
    stripped = line_text.strip()
    # Strip markdown headers and bold wrappers for matching
    norm = re.sub(r"^#{1,6}\s+", "", stripped)
    norm = re.sub(r"^\*\*(.*?)\*\*$", r"\1", norm).strip()

    for kind, pattern in HEADING_PATTERNS:
        if pattern.match(norm) or pattern.match(stripped):
            return kind
    return None


@dataclass
class _RawSectionBlock:
    title: str | None = None
    title_span: DocSpan | None = None
    kind: SectionKind = SectionKind.UNCLASSIFIED
    lines: list[tuple[int, int, str]] = field(default_factory=list)


def parse_job_description(source: str) -> ParsedDocument:
    """Parse raw job description text into a typed document tree with exact source offsets."""
    if not source:
        return ParsedDocument(raw_text="")

    # Break into lines while recording exact (start, end) offsets in source
    line_spans: list[tuple[int, int, str]] = []
    curr = 0
    for line in source.splitlines(keepends=True):
        line_len = len(line)
        line_spans.append((curr, curr + line_len, line))
        curr += line_len

    # Identify heading lines and section breaks
    section_blocks: list[_RawSectionBlock] = []
    current_block = _RawSectionBlock()
    section_blocks.append(current_block)

    for start, end, line in line_spans:
        line_stripped = line.strip()
        kind = _classify_heading(line_stripped) if line_stripped else None

        if kind is not None:
            # New section detected
            title_span = DocSpan(start=start, end=end, raw_text=source[start:end])
            current_block = _RawSectionBlock(
                title=line_stripped,
                title_span=title_span,
                kind=kind,
            )
            section_blocks.append(current_block)
        else:
            current_block.lines.append((start, end, line))

    parsed_sections: list[DocSection] = []
    item_counter = 0

    for s_idx, block in enumerate(section_blocks):
        lines = block.lines
        block_title = block.title
        block_title_span = block.title_span
        block_kind = block.kind

        if not lines and block_title_span is None:
            continue

        items: list[DocItem] = []
        i = 0
        while i < len(lines):
            l_start, l_end, l_text = lines[i]
            if not l_text.strip():
                i += 1
                continue

            bullet_match = BULLET_PATTERN.match(l_text)
            if bullet_match:
                # Group bullet and its continuation lines
                marker = bullet_match.group(1)
                item_start = l_start
                item_end = l_end
                i += 1
                while i < len(lines):
                    next_start, next_end, next_text = lines[i]
                    if not next_text.strip():
                        # blank line marks end of bullet
                        break
                    # If next line is another bullet or heading, stop
                    if BULLET_PATTERN.match(next_text) or _classify_heading(next_text.strip()):
                        break
                    item_end = next_end
                    i += 1

                item_counter += 1
                items.append(
                    DocItem(
                        id=f"item_{item_counter}",
                        item_type="bullet",
                        span=DocSpan(start=item_start, end=item_end, raw_text=source[item_start:item_end]),
                        bullet_marker=marker,
                    )
                )
            else:
                # Group contiguous non-blank lines into a paragraph
                item_start = l_start
                item_end = l_end
                i += 1
                while i < len(lines):
                    next_start, next_end, next_text = lines[i]
                    if not next_text.strip():
                        break
                    if BULLET_PATTERN.match(next_text) or _classify_heading(next_text.strip()):
                        break
                    item_end = next_end
                    i += 1

                item_counter += 1
                items.append(
                    DocItem(
                        id=f"item_{item_counter}",
                        item_type="paragraph",
                        span=DocSpan(start=item_start, end=item_end, raw_text=source[item_start:item_end]),
                    )
                )

        if not items and block_title_span is None:
            continue

        # Determine section span
        sec_start = block_title_span.start if block_title_span else items[0].span.start
        sec_end = items[-1].span.end if items else (block_title_span.end if block_title_span else sec_start)

        parsed_sections.append(
            DocSection(
                id=f"sec_{s_idx}",
                title=block_title,
                title_span=block_title_span,
                kind=block_kind,
                span=DocSpan(start=sec_start, end=sec_end, raw_text=source[sec_start:sec_end]),
                items=items,
            )
        )

    doc = ParsedDocument(raw_text=source, sections=parsed_sections)
    return doc
