"""Acceptance tests for Spike S1 (Tectonic compile + PDF text & page extraction)."""

from pathlib import Path

import pytest

from careercompiler.render.runner import CompileError, compile_tex


def test_spike_s1_minimal_compile(tmp_path: Path) -> None:
    """Verify compiling a minimal .tex to PDF via Tectonic."""
    tex_path = tmp_path / "spike_s1.tex"
    tex_path.write_text(
        r"""\documentclass{article}
\begin{document}
Career Compiler Spike S1 Verification Token
\end{document}
""",
        encoding="utf-8",
    )

    result = compile_tex(tex_path, out_dir=tmp_path, timeout=30)
    assert result.pdf_path.is_file()
    assert result.page_count == 1
    assert "Career Compiler Spike S1 Verification Token" in result.extracted_text
    assert result.elapsed_seconds < 10.0


def test_spike_s1_syntax_error_handling(tmp_path: Path) -> None:
    """Verify that malformed LaTeX raises a typed CompileError with error details."""
    tex_path = tmp_path / "broken.tex"
    tex_path.write_text(
        r"""\documentclass{article}
\begin{document}
\undefinedmacroThatDoesNotExist
\end{document}
""",
        encoding="utf-8",
    )

    with pytest.raises(CompileError) as exc_info:
        compile_tex(tex_path, out_dir=tmp_path, timeout=30)
    assert "Undefined control sequence" in str(exc_info.value) or "halted" in str(exc_info.value)
