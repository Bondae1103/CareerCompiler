# DECISIONS.md — Architecture & Design Decisions Log

This document records all architectural decisions, audit resolutions, and technical baselines.

---

## Spec Audit Decisions (§2)

### D-001: Technology Stack Selection (A1)
- **Date**: 2026-10-01
- **Status**: APPROVED (Confirmed by Human)
- **Rationale**:
  - Core Language: **Python 3.11+** (using `py -3.11` in this Windows environment). Pydantic v2 with strict validation and typed interfaces.
  - Core Architecture: Pure library (`careercompiler/`) with zero web/UI imports. CLI second, FastAPI third, React + Vite UI last (P11).
  - Storage: **SQLite** via Python standard library `sqlite3` + JSON export/import for Master Profile Bank.
  - Lexical Search: Deterministic BM25 implementation.
  - Semantic Search: Local embeddings via `sentence-transformers` with explicitly pinned model identifier and revision hash, cached by `sha256(model_rev + text)`.
  - Optimization Solver: Exact integer programming (ILP) using `ortools` (CP-SAT) with fixed random seed and single-threaded determinism.
  - PDF Compilation: **Tectonic CLI 0.17.0** invoked via `subprocess.run([...])` without shell expansion.
  - Quality Tooling: `pytest`, `hypothesis`, `ruff`, `mypy --strict`.

### D-002: Canonical ID Namespace Ownership (A2)
- **Date**: 2026-10-01
- **Status**: DECIDED
- **Rationale**: Single canonical ID namespace owned by Tier 2 Gazetteer. Both JD extraction and resume tagging strictly resolve against this catalog. Code and test fixtures assert that every `canonical_id` exists in the taxonomy.

### D-003: Evidence Invariant for Resume Concepts (A3)
- **Date**: 2026-10-01
- **Status**: DECIDED
- **Rationale**: Every extracted `domain_concept` must have a valid character `evidence_span` in the source bullet text. If an entity is inferred rather than directly attested, it must be stored in `inferred_concepts` with `inferred=True` and is strictly excluded from lexical keyword coverage scores.

### D-004: Bullet Rewording and LLM Rewrites (A4)
- **Date**: 2026-10-01
- **Status**: APPROVED (Confirmed by Human: Permit dynamic LLM rewrites)
- **Rationale**: The human confirmed that dynamic LLM rewrites of bullet text are permitted (relaxing strict author-only variants for those specific rewrites). To preserve high signal and prevent hallucinations, any dynamic rewrite:
  1. Must be clearly identified with `type="llm_rewritten"` in the diff and selection state.
  2. Must be reversible to the original authored variant in 1 click.
  3. Must pass validation asserting no hallucinated technologies or metrics beyond the author's input.
  4. The engine will still support pure variant swapping as the deterministic baseline.

### D-005: Scoring Nomenclature & Metric Definition (A5)
- **Date**: 2026-10-01
- **Status**: DECIDED
- **Rationale**: The engine will not claim to simulate proprietary third-party ATS systems. The metric is explicitly named `keyword_coverage_score` ("ATS-style coverage") in code, UI, and documentation, governed by formulas in `docs/SCORING.md`.

### D-006: Accuracy & Evaluation Claims (A6)
- **Date**: 2026-10-01
- **Status**: DECIDED
- **Rationale**: Unmeasurable marketing claims ("zero false positives", "100% accuracy") are prohibited. Only deterministic algorithmic properties (e.g. boundary-safe tokenization, alias matching) are guaranteed by tests; Tier 3 semantic extraction will report measured precision and recall on a labeled evaluation set.

### D-007: Taxonomy Provenance and Licensing (A7)
- **Date**: 2026-10-01
- **Status**: DECIDED
- **Rationale**: A curated, reviewed seed catalog of >= 200 technical entities will be established first. Scaling to larger datasets requires verified permissive open licenses (e.g. Stack Overflow tag synonyms CC BY-SA, GitHub Linguist MIT) tracked in a provenance manifest.

### D-008: Baseline for Score Deltas and Reversion (A8)
- **Date**: 2026-10-01
- **Status**: DECIDED
- **Rationale**: Baseline selection is defined as the user's `default_variant_id` for each slot (or first variant by `sort_order`). The score delta is strictly defined as `score(current_selection) - score(baseline_selection)` under the same scorer.

### D-009: Job Description Ingestion Channel (A9)
- **Date**: 2026-10-01
- **Status**: DECIDED
- **Rationale**: Direct text paste is the primary input method. URL scraping is deferred to P11 with strict SSRF controls and fallback to direct paste upon any failure.

### D-010: Privacy and Local-First Processing (A10)
- **Date**: 2026-10-01
- **Status**: APPROVED (Confirmed by Human)
- **Rationale**: Default processing is 100% local (local rule extractor, local embeddings, local solver, local Tectonic). Any remote LLM call must be an explicit user opt-in and fully audited.

### D-011: Line Measurement Estimator Selection (Spike S2)
- **Date**: 2026-10-01
- **Status**: DECIDED
- **Context & Measured Results (52 Varied Bullets)**:
  | Estimator | Exact Agreement | Over-estimates | Under-estimates | Latency |
  | :--- | :--- | :--- | :--- | :--- |
  | **TeX `\prevgraf` Batch Probe** (Ground Truth) | 52/52 (100.0%) | 0 (0.0%) | 0 (0.0%) | ~1.5s per batch |
  | **FontMetricSimulator** (Glyph width simulation) | 47/52 (90.4%) | 5 (9.6%) | **0 (0.0%)** | < 0.1ms per bullet |
  | **HeuristicLineEstimator** (Conservative threshold) | 31/52 (59.6%) | 21 (40.4%) | **0 (0.0%)** | < 0.01ms per bullet |
- **Rationale**:
  - The hard requirement is that the production estimator must **never under-estimate** lines (conservative), while maintaining high accuracy so the optimizer does not unnecessarily omit content.
  - `FontMetricSimulator` achieved **90.4% exact agreement with 0 under-estimates** across all 52 varied bullets (real bullets, boundary lengths, URLs, LaTeX escapes, and symbols).
  - Selected strategy: **Two-Tier Estimator**:
    1. `FontMetricSimulator` serves as the primary fast estimator in the ILP solver loop.
    2. Final compile gate is always a real compile using `compile_tex` (Tectonic) verifying `pages == 1`. If `pages > 1`, capacity is decremented and re-solved.

### D-012: Profile Domain Model ID Scheme & Storage Invariants (P2)
- **Date**: 2026-10-01
- **Status**: DECIDED
- **Rationale**:
  - Entity ID Scheme: Slug format `^[a-zA-Z0-9_-]{1,64}$` to allow clear semantic names (e.g. `exp_thermo_b1`, `v1_perf`) while preventing path traversal or shell characters.
  - Text Immutability: User-authored text is trimmed of leading and trailing whitespace only. Internal whitespace, Unicode, punctuation, and casing are preserved verbatim.
  - No Control Characters: Reject characters in ranges `\x00-\x08`, `\x0b-\x0c`, `\x0e-\x1f` to prevent corrupted TeX input.
  - Storage Strategy: SQLite backed via standard library `sqlite3` storing canonical JSON payloads with schema versioning table, supporting deterministic JSON serialization (sorted keys, 2-space indentation) for byte-identical round-trips.

### D-013: Tier 1 Document Tree Parser Specifications & Heading Taxonomy (P3)
- **Date**: 2026-10-02
- **Status**: DECIDED
- **Rationale**:
  - Section Classification Taxonomy: Fixed canonical enum `SectionKind` (`RESPONSIBILITIES`, `REQUIREMENTS`, `PREFERRED`, `ABOUT`, `BENEFITS`, `UNCLASSIFIED`). Unknown or heading-less sections are strictly assigned to `UNCLASSIFIED`.
  - Evidence & Offset Invariant: All document nodes store `start` and `end` character offsets referencing the unmodified source text. Code verifies `source[node.start:node.end] == node.raw_text`.
  - Zero-Loss Text Coverage: The concatenated leaf spans of a parsed document cover 100% of all non-whitespace characters in the input document. Nothing is silently dropped.
  - Resume Import Intake: An existing resume (`.tex` or plain text) is parsed into an editable *draft* `Profile` requiring explicit user confirmation before saving to the Master Profile Bank.



