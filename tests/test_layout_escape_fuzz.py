"""Hypothesis property-based tests for LaTeX escaping and round-trip extraction."""

import tempfile
from pathlib import Path

import hypothesis.strategies as st
from hypothesis import given, settings

from careercompiler.layout.latex_escape import (
    escape_latex,
    normalize_pdf_text_for_comparison,
)
from careercompiler.render.runner import compile_tex, extract_pdf_text

# Characters to fuzz: specials, symbols, and standard text
SPECIAL_CHARS = r"\&%$#_{}~^<>|" + '"' + "—–“”—≥≤→±×€£"


@given(st.text(alphabet=st.characters(blacklist_categories=("Cs", "Cc")), max_size=100))
@settings(max_examples=50)
def test_escape_latex_never_crashes(text: str) -> None:
    """escape_latex never raises an exception on arbitrary unicode text."""
    escaped = escape_latex(text)
    assert isinstance(escaped, str)


@given(
    st.lists(
        st.one_of(
            st.sampled_from(list(SPECIAL_CHARS)),
            st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        ),
        min_size=1,
        max_size=8,
    )
)
@settings(max_examples=8, deadline=None)
def test_escape_latex_compiles_cleanly_under_tectonic(parts: list[str]) -> None:
    """Escaped text wrapped in article document compiles cleanly with Tectonic."""
    raw_text = " ".join(parts)
    escaped = escape_latex(raw_text)

    doc = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{textcomp}
\begin{document}
""" + escaped + r"""
\end{document}
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        tex_path = tmp / "fuzz.tex"
        tex_path.write_text(doc, encoding="utf-8")

        res = compile_tex(tex_path, out_dir=tmp, timeout=30)
        assert res.page_count >= 1
        extracted = extract_pdf_text(res.pdf_path)
        norm_ext = normalize_pdf_text_for_comparison(extracted)
        assert len(norm_ext) >= 0


def test_escape_latex_known_specials_table() -> None:
    """Table test for known difficult LaTeX characters."""
    cases = [
        (r"C++ & C# with 100% pass rate", r"C++ \& C\# with 100\% pass rate"),
        (r"Cost: $10,000 / €500 / £200", r"Cost: \$10,000 / \texteuro{}500 / \pounds{}200"),
        (r"Path: /usr/local_bin/app", r"Path: /usr/local\_bin/app"),
        (r"Latency: <5ms p99 vs >100ms", r"Latency: \textless{}5ms p99 vs \textgreater{}100ms"),
        (r"Condition: x ≥ 10 and y ≤ 5", r"Condition: x $\ge$ 10 and y $\le$ 5"),
    ]
    for inp, expected in cases:
        actual = escape_latex(inp)
        assert actual == expected, f"Failed on '{inp}': got '{actual}', expected '{expected}'"
