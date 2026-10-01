# ENVIRONMENT.md — System & Toolchain Specification

This document records the exact runtime environment and toolchain versions verified in this session.

---

## Operating System & Shell
- **OS**: Windows 11 Home Single Language (`Windows-10-10.0.26200-SP0` / 64-bit AMD64)
- **Shell**: PowerShell (Windows)

---

## Toolchain & Runtime Versions

| Tool | Version | Executable Location | Notes |
| :--- | :--- | :--- | :--- |
| **Python** | `3.11.9` (`py -3.11`) | `C:\Users\Anoop\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe` | Verified via `py -3.11`. |
| **Git** | `2.53.0.windows.2` | `C:\Program Files\Git\cmd\git.exe` | Verified via `git --version`. |
| **Node.js** | `v22.14.0` | `C:\Program Files\nodejs\node.exe` | Verified via `node --version`. |
| **npm** | `10.9.2` | `C:\Program Files\nodejs\npm.cmd` | Verified via `npm --version`. |
| **Tectonic** | `0.17.0` | `C:\Users\Anoop\AppData\Local\Programs\tectonic\tectonic.exe` | Installed via official release archive; added to User PATH. |
| **Poppler** (`pdftotext`, `pdfinfo`) | `25.07.0` | `C:\Users\Anoop\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin` | Installed via winget (`oschwartz10612.Poppler`); added to User PATH. |

---

## Tectonic Bundle & Network Behavior (§1.4)
- **First-run compilation**: Tectonic dynamically downloads format definitions, TeX engines (`xelatex.ini`, `latex.ltx`), packages (`article.cls`, `titlesec`, `hyperref`), and Latin Modern OpenType fonts on demand.
  - Initial cold download elapsed time: ~199 seconds.
- **Cached compilation**: Subsequent runs use local cache stored in `%LOCALAPPDATA%\Tectonic\cache`.
  - Cached elapsed time: **493 ms** (hello-world) / **620 ms** (full resume).
- **Template Compatibility Note**:
  - `glyphtounicode.tex` contains pdfTeX-specific primitives (`\pdfglyphtounicode`, `\pdfgentounicode`) which raise an `Undefined control sequence` under XeTeX/Tectonic.
  - Wrapping with `\usepackage{iftex}\ifPDFTeX ... \fi` makes `resume.tex` seamlessly dual-compatible with both XeTeX/Tectonic and standard pdfLaTeX.
  - Successfully verified compile of `resume.tex` into a valid **1-page PDF** (`Pages: 1`).
