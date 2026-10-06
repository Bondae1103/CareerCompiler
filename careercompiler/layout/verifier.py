"""LaTeX compilation runner and multi-factor PDF verification engine."""

import subprocess
import tempfile
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from careercompiler.layout.latex_escape import normalize_pdf_text_for_comparison
from careercompiler.render.runner import (
    _resolve_tool,
    extract_pdf_text,
    get_pdf_page_count,
)


@dataclass(frozen=True)
class LayoutBuildResult:
    """Structured result of LaTeX compilation and PDF verification."""

    success: bool
    page_count: int
    pdf_path: Path | None
    extracted_text: str
    warnings: list[str]
    errors: list[str]
    all_bullets_present: bool
    missing_bullets: list[str]
    fonts_embedded: bool
    is_ats_extractable: bool
    elapsed_seconds: float


class LayoutVerifier:
    """Orchestrates Tectonic compilation in an isolated directory and verifies PDF invariants."""

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout
        self.tectonic_exe = _resolve_tool("tectonic")
        self.pdffonts_exe = _resolve_tool("pdffonts")

    def check_fonts_embedded(self, pdf_path: Path) -> tuple[bool, list[str]]:
        """Verify via pdffonts that all embedded fonts have 'emb == yes'."""
        try:
            proc = subprocess.run(
                [self.pdffonts_exe, str(pdf_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                check=True,
            )
        except Exception as e:
            return False, [f"Failed to execute pdffonts: {e}"]

        lines = proc.stdout.splitlines()
        if len(lines) < 2:
            return False, ["pdffonts returned empty output"]

        # Parse data lines after header and separator
        data_lines = [line.strip() for line in lines[2:] if line.strip()]
        if not data_lines:
            return False, ["No fonts detected in PDF"]

        unembedded: list[str] = []
        for line in data_lines:
            # Columns typically: name, type, encoding, emb, sub, uni, object ID
            tokens = line.split()
            # emb column is typically 4th from right or identified by yes/no
            if "no" in tokens:
                # Find position of 'no'
                no_idx = tokens.index("no")
                # If 'no' is in emb column (before sub/uni)
                if no_idx < len(tokens) - 2:
                    unembedded.append(tokens[0])

        if unembedded:
            return False, [f"Unembedded font(s) detected: {', '.join(unembedded)}"]
        return True, []

    def compile_and_verify(
        self,
        rendered_tex: str,
        expected_bullet_texts: Sequence[str] = (),
        work_dir: Path | None = None,
    ) -> LayoutBuildResult:
        """Compile rendered LaTeX and verify single-page, text extractability, and font embedding."""
        start_time = time.perf_counter()
        warnings: list[str] = []
        errors: list[str] = []

        # If work_dir is not provided, use an isolated temporary directory
        temp_dir_ctx = None
        if work_dir is None:
            temp_dir_ctx = tempfile.TemporaryDirectory()
            target_dir = Path(temp_dir_ctx.name)
        else:
            target_dir = work_dir
            target_dir.mkdir(parents=True, exist_ok=True)

        try:
            tex_file = target_dir / "resume.tex"
            tex_file.write_text(rendered_tex, encoding="utf-8")

            # 1. Run Tectonic with shell escape disabled
            cmd = [
                self.tectonic_exe,
                "--outdir",
                str(target_dir),
                str(tex_file.name),
            ]

            proc = subprocess.run(
                cmd,
                cwd=str(target_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
            )

            # 2. Parse logs for warnings
            combined_log = (proc.stdout or "") + "\n" + (proc.stderr or "")
            for line in combined_log.splitlines():
                if "Overfull \\hbox" in line:
                    warnings.append(f"Layout warning: {line.strip()}")
                elif "Missing character:" in line:
                    warnings.append(f"Font warning: {line.strip()}")

            if proc.returncode != 0:
                errors.append(f"Tectonic compilation failed with exit code {proc.returncode}:\n{combined_log}")
                elapsed = time.perf_counter() - start_time
                return LayoutBuildResult(
                    success=False,
                    page_count=0,
                    pdf_path=None,
                    extracted_text="",
                    warnings=warnings,
                    errors=errors,
                    all_bullets_present=False,
                    missing_bullets=list(expected_bullet_texts),
                    fonts_embedded=False,
                    is_ats_extractable=False,
                    elapsed_seconds=elapsed,
                )

            pdf_path = target_dir / "resume.pdf"
            if not pdf_path.exists():
                errors.append("Tectonic exited with 0 but resume.pdf was not produced.")
                elapsed = time.perf_counter() - start_time
                return LayoutBuildResult(
                    success=False,
                    page_count=0,
                    pdf_path=None,
                    extracted_text="",
                    warnings=warnings,
                    errors=errors,
                    all_bullets_present=False,
                    missing_bullets=list(expected_bullet_texts),
                    fonts_embedded=False,
                    is_ats_extractable=False,
                    elapsed_seconds=elapsed,
                )

            # 3. Check Page Count
            page_count = get_pdf_page_count(pdf_path, timeout=self.timeout)
            if page_count != 1:
                errors.append(f"Page budget violation: PDF has {page_count} pages (strict 1-page requirement).")

            # 4. Check Text Extraction & ATS friendliness
            raw_extracted = extract_pdf_text(pdf_path, timeout=self.timeout)
            norm_extracted = normalize_pdf_text_for_comparison(raw_extracted)

            is_ats = len(norm_extracted.strip()) > 200

            # 5. Check Bullet Presence (Truth Invariant)
            missing_bullets: list[str] = []
            for b_text in expected_bullet_texts:
                norm_b = normalize_pdf_text_for_comparison(b_text)
                # First check full normalized sentence
                if norm_b not in norm_extracted:
                    # Also check significant prefix if end-of-bullet punctuation varied
                    prefix = norm_b[: min(len(norm_b), 40)]
                    if prefix not in norm_extracted:
                        missing_bullets.append(b_text)

            all_bullets_present = len(missing_bullets) == 0
            if not all_bullets_present:
                errors.append(f"{len(missing_bullets)} expected bullet(s) missing from extracted PDF text.")

            # 6. Check Embedded Fonts
            fonts_embedded, font_errs = self.check_fonts_embedded(pdf_path)
            errors.extend(font_errs)

            success = (page_count == 1) and all_bullets_present and fonts_embedded and (len(errors) == 0)
            elapsed = time.perf_counter() - start_time

            return LayoutBuildResult(
                success=success,
                page_count=page_count,
                pdf_path=pdf_path if work_dir else None,
                extracted_text=raw_extracted,
                warnings=warnings,
                errors=errors,
                all_bullets_present=all_bullets_present,
                missing_bullets=missing_bullets,
                fonts_embedded=fonts_embedded,
                is_ats_extractable=is_ats,
                elapsed_seconds=elapsed,
            )

        finally:
            if temp_dir_ctx is not None:
                temp_dir_ctx.cleanup()
