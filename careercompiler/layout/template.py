"""LaTeX template parser and renderer with strict injection marker validation."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import ClassVar

from careercompiler.layout.latex_escape import escape_latex


class TemplateSyntaxError(Exception):
    """Raised when LaTeX template injection markers are missing, mismatched, or malformed."""


@dataclass
class TemplateBlock:
    """A parsed node in the LaTeX template tree."""

    kind: str  # "STATIC", "EXPERIENCE", "PROJECT", "SLOT", "SKILLS", "SECTION"
    block_id: str | None
    raw_content: str = ""
    children: list["TemplateBlock"] = field(default_factory=list)


class ResumeTemplate:
    """Parsed LaTeX template with validated injection markers."""

    MARKER_REGEX: ClassVar[re.Pattern[str]] = re.compile(
        r"%%(?P<action>BEGIN|END):(?P<kind>[A-Z_]+)(?::(?P<id>[a-zA-Z0-9_-]+))?%%"
    )

    def __init__(self, raw_tex: str) -> None:
        self.raw_tex = raw_tex
        self.root_blocks: list[TemplateBlock] = []
        self.slots: dict[str, TemplateBlock] = {}
        self.entities: dict[str, TemplateBlock] = {}
        self._parse()

    def _parse(self) -> None:
        """Parse raw template string into hierarchical TemplateBlock tree with strict marker validation."""
        stack: list[tuple[str, str | None, TemplateBlock]] = []
        last_pos = 0

        # Create virtual root
        root = TemplateBlock(kind="ROOT", block_id=None)
        current_block = root

        for match in self.MARKER_REGEX.finditer(self.raw_tex):
            start, end = match.span()
            action = match.group("action")
            kind = match.group("kind")
            marker_id = match.group("id")

            # Static text preceding this marker
            static_text = self.raw_tex[last_pos:start]
            if static_text:
                current_block.children.append(TemplateBlock(kind="STATIC", block_id=None, raw_content=static_text))

            last_pos = end

            if action == "BEGIN":
                # Check for duplicate ID within same kind
                if marker_id and kind == "SLOT" and marker_id in self.slots:
                    raise TemplateSyntaxError(f"Duplicate template marker ID: SLOT:{marker_id}")
                if marker_id and kind in {"EXPERIENCE", "PROJECT"} and marker_id in self.entities:
                    raise TemplateSyntaxError(f"Duplicate template marker ID: {kind}:{marker_id}")

                new_block = TemplateBlock(kind=kind, block_id=marker_id)
                current_block.children.append(new_block)

                if kind == "SLOT" and marker_id:
                    self.slots[marker_id] = new_block
                elif marker_id and kind in {"EXPERIENCE", "PROJECT"}:
                    self.entities[marker_id] = new_block

                stack.append((kind, marker_id, current_block))
                current_block = new_block

            elif action == "END":
                if not stack:
                    raise TemplateSyntaxError(f"Unexpected end marker '{match.group(0)}' without matching BEGIN")

                expected_kind, expected_id, parent_block = stack.pop()
                if kind != expected_kind or marker_id != expected_id:
                    raise TemplateSyntaxError(
                        f"Mismatched end marker: expected '%%END:{expected_kind}"
                        f"{f':{expected_id}' if expected_id else ''}%%', "
                        f"but found '{match.group(0)}'"
                    )

                current_block = parent_block

        if stack:
            unclosed_kind, unclosed_id, _ = stack[-1]
            unclosed_str = f"%%BEGIN:{unclosed_kind}{f':{unclosed_id}' if unclosed_id else ''}%%"
            raise TemplateSyntaxError(f"Unclosed template marker at end of file: {unclosed_str}")

        # Trailing static content
        trailing = self.raw_tex[last_pos:]
        if trailing:
            root.children.append(TemplateBlock(kind="STATIC", block_id=None, raw_content=trailing))

        self.root_blocks = root.children

    def render(
        self,
        slot_texts: Mapping[str, str | None],
        strip_omitted_slots: bool = True,
    ) -> str:
        """Render template with chosen variant texts injected into each slot.

        Args:
            slot_texts: Mapping from slot_id to raw authored text (or None if slot omitted).
            strip_omitted_slots: If True, completely omits \\resumeItem{} for unselected slots.
        """
        # Validate that all selected slot_ids exist in the template
        for slot_id, text in slot_texts.items():
            if text is not None and slot_id not in self.slots:
                raise TemplateSyntaxError(f"Selected slot '{slot_id}' not found in template markers.")

        def render_block(block: TemplateBlock) -> str:
            if block.kind == "STATIC":
                return block.raw_content

            if block.kind == "SLOT":
                slot_id = block.block_id or ""
                chosen_text = slot_texts.get(slot_id)
                if chosen_text is None:
                    if strip_omitted_slots:
                        return ""
                    return ""

                # Truth Invariant: text is escaped and rendered into \\resumeItem{}
                escaped = escape_latex(chosen_text)
                return f"        \\resumeItem{{{escaped}}}\n"

            # Recursive render for containers (EXPERIENCE, PROJECT, etc.)
            parts = [render_block(child) for child in block.children]
            return "".join(parts)

        return "".join(render_block(b) for b in self.root_blocks)
