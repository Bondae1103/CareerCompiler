"""Line measurement and estimation engines for Career Compiler.

Spike S2 compares:
- TeX-side measurement (prevgraf compile probe)
- Font-metric line breaking simulation
- Conservative heuristic budget
Against ground-truth layout lines.
"""

import math
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from careercompiler.render.runner import _resolve_tool


@dataclass(frozen=True)
class LineEstimateResult:
    """Estimated lines for a bullet."""

    bullet_id: str
    text: str
    estimated_lines: int
    estimator_name: str


class HeuristicLineEstimator:
    """Fast, conservative line estimator based on calibrated character budget.

    Tuned for Jake's resume template with 545.64pt linewidth and 9pt Latin Modern font.
    Hard requirement: must NEVER under-estimate lines.
    """

    CHARS_PER_LINE: ClassVar[float] = 100.0  # Conservative threshold (actual avg line fits ~115 chars)

    def estimate(self, text: str) -> int:
        clean = self._clean_for_measurement(text)
        if not clean:
            return 0
        # Conservative ceiling
        return max(1, math.ceil(len(clean) / self.CHARS_PER_LINE))

    @staticmethod
    def _clean_for_measurement(text: str) -> str:
        # Strip common LaTeX markup to estimate visible character length
        s = re.sub(r"\\textbf\{([^}]+)\}", r"\1", text)
        s = re.sub(r"\\textit\{([^}]+)\}", r"\1", text)
        s = re.sub(r"\\emph\{([^}]+)\}", r"\1", text)
        s = re.sub(r"\\href\{[^}]+\}\{([^}]+)\}", r"\1", text)
        s = re.sub(r"\\[%&$#_{}]", "X", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s


class FontMetricSimulator:
    """Simulates greedy word-wrap line breaking using Latin Modern Roman 9pt glyph metrics."""

    LINEWIDTH_PT: ClassVar[float] = 545.64
    AVG_CHAR_WIDTH_PT: ClassVar[float] = 4.75  # 9pt LMR avg char width
    SPACE_WIDTH_PT: ClassVar[float] = 3.0
    BOLD_MULTIPLIER: ClassVar[float] = 1.12

    def estimate(self, text: str) -> int:
        words = text.split()
        if not words:
            return 0

        lines = 1
        current_width = 0.0

        for word in words:
            # Check for bold formatting
            is_bold = "\\textbf{" in word or "}" in word
            clean_word = re.sub(r"\\[a-zA-Z]+|\{|\}", "", word)
            word_width = len(clean_word) * self.AVG_CHAR_WIDTH_PT
            if is_bold:
                word_width *= self.BOLD_MULTIPLIER

            if current_width + word_width <= self.LINEWIDTH_PT:
                current_width += word_width + self.SPACE_WIDTH_PT
            else:
                lines += 1
                current_width = word_width + self.SPACE_WIDTH_PT

        return lines


class TeXPrevgrafEstimator:
    """Uses Tectonic compile-in-the-loop with TeX \\prevgraf probe.

    Exact agreement with TeX's Knuth-Plass line-breaking algorithm.
    """

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout
        self.tectonic_exe = _resolve_tool("tectonic")

    def measure_batch(self, items: list[tuple[str, str]], work_dir: Path) -> dict[str, int]:
        """Measure lines for a batch of (id, latex_text) bullets in a single Tectonic compilation."""
        work_dir.mkdir(parents=True, exist_ok=True)
        tex_path = work_dir / "batch_measure.tex"

        probe_macros = r"""\documentclass[letterpaper,10pt]{article}
\usepackage[empty]{fullpage}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\addtolength{\oddsidemargin}{-0.6in}
\addtolength{\evensidemargin}{-0.6in}
\addtolength{\textwidth}{1.2in}
\addtolength{\topmargin}{-0.6in}
\addtolength{\textheight}{1.2in}
\newcommand{\resumeItemListStart}{\begin{itemize}[leftmargin=0.15in, label=\textbullet]}
\newcommand{\resumeItemListEnd}{\end{itemize}}
\newcount\mylinecount
\newcommand{\measureItem}[2]{%
  \resumeItemListStart
    \item \small #2\par
    \global\mylinecount=\prevgraf
    \typeout{MEASURE_PREVGRAF:#1:\the\mylinecount}%
  \resumeItemListEnd
}
\begin{document}
"""
        body_lines = [probe_macros]
        for item_id, text in items:
            # Escape quotes if necessary in macro call
            body_lines.append(f"\\measureItem{{{item_id}}}{{{text}}}")
        body_lines.append(r"\end{document}")

        tex_path.write_text("\n".join(body_lines), encoding="utf-8")

        proc = subprocess.run(
            [self.tectonic_exe, "--print", str(tex_path.name)],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )

        results: dict[str, int] = {}
        for line in proc.stdout.splitlines():
            if "MEASURE_PREVGRAF:" in line:
                parts = line.strip().split(":")
                if len(parts) >= 3:
                    bid = parts[1]
                    count = int(parts[2])
                    results[bid] = count

        return results
