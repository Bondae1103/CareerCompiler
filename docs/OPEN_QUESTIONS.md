# OPEN_QUESTIONS.md — Spec Audit & Blocking Inquiries

This document tracks all ambiguities, blockers, and questions requiring human input.

---

## Resolved Inquiries
- **Q-001 [RESOLVED - 2026-10-01]**: Stack confirmed (Python 3.11, SQLite, ortools CP-SAT, Tectonic, React+Vite).
- **Q-002 [RESOLVED - 2026-10-01]**: Human confirmed permitting dynamic LLM rewrites of bullet text (relaxing strict author-only variants for those specific rewrites, while preserving 1-click revert, anti-hallucination validation, and author-written variants as default/baseline).
- **Q-003 [RESOLVED - 2026-10-01]**: Human confirmed local-first default with explicit opt-in for remote LLM calls.

---

## Non-Blocking Open Questions / Roadmap Proposals

### Q-004: Tectonic and Poppler Distribution on Windows
- **Status**: Investigating installation methods. Poppler is available via winget (`oschwartz10612.Poppler`). Tectonic is downloadable via official PowerShell installer or GitHub binary release. Verification in progress for P1 Spike S1.

### Q-005: Evaluation Labeled Dataset
- **Status**: Need real labeled JD samples and ideal bullet selections for calibration in P7/P12.
