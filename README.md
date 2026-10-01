# Career Compiler

Profile-Backed, Deterministic Resume Tailoring Engine.

## Requirements
- Python >= 3.11
- Tectonic (`tectonic --version`)
- Poppler (`pdftotext -v`, `pdfinfo -v`)

## Setup
```bash
py -3.11 -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
```

## Running Verification
```bash
make lint
make typecheck
make test
```
