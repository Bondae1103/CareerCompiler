"""Tectonic compilation runner and poppler inspection utilities."""

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class CompileError(Exception):
    """Raised when LaTeX/Tectonic compilation fails."""


class TectonicNotFoundError(Exception):
    """Raised when the tectonic executable cannot be located."""


class TectonicTimeoutError(Exception):
    """Raised when compilation exceeds the configured timeout."""


@dataclass(frozen=True)
class CompileResult:
    """Result of a Tectonic compilation."""

    pdf_path: Path
    page_count: int
    extracted_text: str
    stdout: str
    stderr: str
    elapsed_seconds: float


def _resolve_tool(tool_name: str) -> str:
    """Locate tool on PATH or common installation locations."""
    path = shutil.which(tool_name)
    if path:
        return path

    # Check Windows user programs directory fallback
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        candidates = [
            Path(local_app_data) / "Programs" / "tectonic" / f"{tool_name}.exe",
            Path(local_app_data) / "Microsoft" / "WindowsApps" / f"{tool_name}.exe",
        ]
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)

    # Check winget poppler fallback
    if tool_name in {"pdfinfo", "pdftotext", "pdffonts"}:
        winget_pkgs = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
        if winget_pkgs.is_dir():
            for bin_file in winget_pkgs.glob(f"**/{tool_name}.exe"):
                if bin_file.is_file():
                    return str(bin_file)

    return tool_name


def get_pdf_page_count(pdf_path: Path, timeout: int = 10) -> int:
    """Extract page count from PDF using pdfinfo."""
    pdfinfo_exe = _resolve_tool("pdfinfo")
    try:
        proc = subprocess.run(
            [pdfinfo_exe, str(pdf_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=True,
        )
    except FileNotFoundError as err:
        raise FileNotFoundError(f"pdfinfo executable not found: {pdfinfo_exe}") from err
    except subprocess.CalledProcessError as err:
        raise CompileError(f"pdfinfo failed on {pdf_path}: {err.stderr}") from err

    match = re.search(r"Pages:\s+(\d+)", proc.stdout)
    if not match:
        raise CompileError(f"Could not parse page count from pdfinfo output:\n{proc.stdout}")
    return int(match.group(1))


def extract_pdf_text(pdf_path: Path, timeout: int = 10) -> str:
    """Extract text from PDF using pdftotext."""
    pdftotext_exe = _resolve_tool("pdftotext")
    try:
        proc = subprocess.run(
            [pdftotext_exe, str(pdf_path), "-"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=True,
        )
    except FileNotFoundError as err:
        raise FileNotFoundError(f"pdftotext executable not found: {pdftotext_exe}") from err
    except subprocess.CalledProcessError as err:
        raise CompileError(f"pdftotext failed on {pdf_path}: {err.stderr}") from err

    return proc.stdout


def compile_tex(
    tex_path: Path,
    out_dir: Path | None = None,
    timeout: int = 60,
) -> CompileResult:
    """Compile a .tex file to PDF using Tectonic.

    Args:
        tex_path: Absolute or relative path to the .tex file.
        out_dir: Directory where the PDF should be placed. Defaults to tex_path.parent.
        timeout: Subprocess timeout in seconds.

    Returns:
        CompileResult containing the PDF path, page count, and extracted text.

    Raises:
        TectonicNotFoundError: If tectonic is not installed.
        TectonicTimeoutError: If compilation exceeds the timeout.
        CompileError: If tectonic exits with non-zero status.
    """
    if not tex_path.is_file():
        raise FileNotFoundError(f"LaTeX source file not found: {tex_path}")

    target_dir = out_dir if out_dir is not None else tex_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    tectonic_exe = _resolve_tool("tectonic")
    cmd = [
        tectonic_exe,
        "--outdir",
        str(target_dir),
        str(tex_path),
    ]

    import time
    start_time = time.perf_counter()

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except FileNotFoundError as err:
        raise TectonicNotFoundError(f"Tectonic executable not found: {tectonic_exe}") from err
    except subprocess.TimeoutExpired as err:
        raise TectonicTimeoutError(
            f"Tectonic compilation timed out after {timeout} seconds on {tex_path}"
        ) from err

    elapsed = time.perf_counter() - start_time

    if proc.returncode != 0:
        error_msg = (
            f"Tectonic compilation failed with exit code {proc.returncode}.\n"
            f"STDOUT:\n{proc.stdout}\n"
            f"STDERR:\n{proc.stderr}"
        )
        raise CompileError(error_msg)

    pdf_name = f"{tex_path.stem}.pdf"
    pdf_path = target_dir / pdf_name
    if not pdf_path.is_file():
        raise CompileError(f"Tectonic exited with 0 but expected output PDF was not found at {pdf_path}")

    pages = get_pdf_page_count(pdf_path, timeout=timeout)
    text = extract_pdf_text(pdf_path, timeout=timeout)

    return CompileResult(
        pdf_path=pdf_path,
        page_count=pages,
        extracted_text=text,
        stdout=proc.stdout,
        stderr=proc.stderr,
        elapsed_seconds=elapsed,
    )
