"""Tests for LaTeX template parsing, marker validation, and rendering."""

from pathlib import Path

import pytest

from careercompiler.layout.template import ResumeTemplate, TemplateSyntaxError


def test_parse_canonical_resume_template() -> None:
    """Canonical templates/resume.tex parses all slots and entities without errors."""
    tex_path = Path("templates/resume.tex")
    tpl = ResumeTemplate(tex_path.read_text(encoding="utf-8"))

    assert len(tpl.slots) == 12
    assert "exp_1_slot_1" in tpl.slots
    assert "proj_1_slot_1" in tpl.slots
    assert len(tpl.entities) == 5
    assert "exp_1" in tpl.entities
    assert "proj_1" in tpl.entities


def test_render_with_custom_variants() -> None:
    """Rendering replaces slot contents with escaped variant text and omits unselected slots."""
    raw_tpl = r"""
\documentclass{article}
\begin{document}
\begin{itemize}
%%BEGIN:SLOT:slot_1%%
\resumeItem{Default item 1}
%%END:SLOT:slot_1%%
%%BEGIN:SLOT:slot_2%%
\resumeItem{Default item 2}
%%END:SLOT:slot_2%%
\end{itemize}
\end{document}
"""
    tpl = ResumeTemplate(raw_tpl)

    # Slot 1 customized with specials, Slot 2 omitted (None)
    rendered = tpl.render({
        "slot_1": "Engineered C++ & Python (100% test coverage) with $10k cost reduction.",
        "slot_2": None,
    })

    assert r"\resumeItem{Engineered C++ \& Python (100\% test coverage) with \$10k cost reduction.}" in rendered
    assert "Default item 2" not in rendered


def test_template_syntax_unclosed_marker_raises() -> None:
    """Unclosed BEGIN marker raises TemplateSyntaxError."""
    bad_tpl = r"""
\documentclass{article}
\begin{document}
%%BEGIN:SLOT:slot_unclosed%%
\resumeItem{Test}
\end{document}
"""
    with pytest.raises(TemplateSyntaxError, match="Unclosed template marker"):
        ResumeTemplate(bad_tpl)


def test_template_syntax_mismatched_end_marker_raises() -> None:
    """Mismatched END marker raises TemplateSyntaxError."""
    bad_tpl = r"""
\documentclass{article}
\begin{document}
%%BEGIN:EXPERIENCE:exp_1%%
%%BEGIN:SLOT:slot_1%%
\resumeItem{Test}
%%END:EXPERIENCE:exp_1%%
%%END:SLOT:slot_1%%
\end{document}
"""
    with pytest.raises(TemplateSyntaxError, match="Mismatched end marker"):
        ResumeTemplate(bad_tpl)


def test_template_syntax_duplicate_slot_id_raises() -> None:
    """Duplicate slot ID raises TemplateSyntaxError."""
    bad_tpl = r"""
\documentclass{article}
\begin{document}
%%BEGIN:SLOT:dup_slot%%
\resumeItem{Item 1}
%%END:SLOT:dup_slot%%
%%BEGIN:SLOT:dup_slot%%
\resumeItem{Item 2}
%%END:SLOT:dup_slot%%
\end{document}
"""
    with pytest.raises(TemplateSyntaxError, match="Duplicate template marker ID"):
        ResumeTemplate(bad_tpl)


def test_render_with_unknown_slot_raises() -> None:
    """Rendering with unknown slot ID raises TemplateSyntaxError."""
    tpl = ResumeTemplate(r"""
\documentclass{article}
\begin{document}
%%BEGIN:SLOT:valid_slot%%
\resumeItem{Valid}
%%END:SLOT:valid_slot%%
\end{document}
""")
    with pytest.raises(TemplateSyntaxError, match="Selected slot 'unknown_slot' not found"):
        tpl.render({"unknown_slot": "Some text"})
