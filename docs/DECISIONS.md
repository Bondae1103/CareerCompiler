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

### D-014: Tier 2 Entity Gazetteer & Normalizer Architecture (P4)
- **Date**: 2026-10-04
- **Status**: DECIDED
- **Rationale**:
  - Single Canonical Namespace: Lowercase alphanumeric slug `^[a-z0-9_-]{1,64}$` owned by Tier 2 Gazetteer. Resolves ambiguity between JD entities and resume tags.
  - Boundary-Safe Matching Engine: Uses dual case-sensitive and case-insensitive Trie structures with exact boundary verification instead of standard `\b` regexes (which fail on `C++`, `C#`, `.NET`, `Node.js`).
  - Data-Driven Disambiguation: Ambiguous short terms (`Go`, `C`, `R`, `Rust`, `Spark`, `REST`) declare explicit contextual rules (`case_sensitive`, `trigger_patterns`, `negative_patterns`, `context_keywords`) directly in the taxonomy data schema rather than scattered in code.
  - Strict License Provenance: All entities carry verified open source licenses (MIT, CC-BY-SA-4.0, or permissive open source) tracked in a structured provenance manifest. Unreviewed entries are strictly tracked and quantified.

### D-015: Tier 3 Constrained Semantic Extractor Architecture (P5)
- **Date**: 2026-10-05
- **Status**: DECIDED
- **Rationale**:
  - Offline-First Extractor: Primary extraction engine `LocalRuleExtractor` operates 100% offline with zero network or remote LLM dependency, combining Tier 1 section classification with Tier 2 entity gazetteer and cue-phrase parsing.
  - Evidence Invariant Enforcement: Post-validator strictly checks that every extracted requirement and scale indicator carries character offset spans into the source text where `source[start:end]` contains the surface form. Invalids are dropped and recorded in `dropped_items_count`.
  - Anti-Tampering & Prompt-Injection Defense: Untrusted JD text cannot elevate requirement importance above what explicit cue phrases support. Unmapped or un-attested skills cannot be injected.
  - Safe Fallback Protocol: If an optional LLM extractor fails or exhausts retries, it gracefully falls back to `LocalRuleExtractor`.
  - Deterministic Caching: `sha256(jd_text + extractor_version + config)` caches extractions in-memory and persistently on disk.

### D-016: Resume Bullet Decomposition (ACTR) & Metric Quality Architecture (P6)
- **Date**: 2026-10-05
- **Status**: DECIDED
- **Rationale**:
  - Action Verb Parsing: Extracted from bullet opening with lemmatized root, tense classification (past/present/participle), and exact character offset evidence span.
  - Technology Entity Grounding: Technologies are matched against the Tier 2 Gazetteer ensuring boundary safety and valid evidence spans where `source[start:end] == surface_form`.
  - Empirical Impact Metrics: Deterministic parsing of 8 quantified categories (baseline transitions "from X to Y", throughput, latency, percentages, multipliers, currency, scale counts, framerate) with normalized float values.
  - Negative Exclusions: Software versions (e.g. `Python 3.11`, `v1.0`), calendar years/dates (e.g. `2026`, `Sep 2023`), availability metrics (`24/7`), and contact/phone numbers are strictly excluded from empirical impact metrics.
  - Metric Quality Classification: Bullets are classified into 4 quality tiers (`NONE`, `VAGUE`, `QUANTIFIED`, `QUANTIFIED_WITH_BASELINE`) codified in `docs/SCORING.md` for deterministic optimization utility scoring.
  - Truth Invariant: Bullet text is immutable; decomposition only segments and annotates spans. `reconstruct_bullet_text` returns the exact authored text byte-for-byte.

### D-017: Multi-Component Scoring Architecture, BM25 Corpus Indexing & Explainability Invariant (P7)
- **Date**: 2026-10-05
- **Status**: DECIDED
- **Rationale**:
  - Submodular Lexical Coverage: Requirements are weighted by category (`must_have: 1.0`, `nice_to_have: 0.5`). Submodular set coverage ensures each requirement is counted at most once; duplicates yield zero marginal gain; monotonicity holds strictly.
  - BM25 Background Corpus Choice: Empirically evaluated `jd_only` ($N \approx 30$, unstable IDF), `bank_only` ($N \approx 12$, overweights rare skills), and `bank_plus_jd` ($N \approx 45-90$). Selected `bank_plus_jd` because indexing profile variants alongside JD requirements provides stable, well-calibrated IDFs that penalize generic terms and reward specific domain matches.
  - Deterministic Offline Semantic Embedder: Primary semantic embedder `DeterministicHashingEmbedder` operates with zero external network or PyTorch dependency, projecting character and subword n-grams into a 128-dimensional unit hypersphere.
  - Metric Quality Utility: Bullets are evaluated for quantification quality, boosting both selection score and bullet slot utility.
  - Explainability Invariant: The overall selection score is a linear combination of normalized components ($S_{\text{total}} = \sum_c w_c \cdot S_c$), and the engine outputs an explicit `ScoreBreakdown` where `total_score` strictly equals the sum of individual component contributions.
### D-018: Layout Template Injection Contract, Safe LaTeX Escaping & PDF Verification (P8)
- **Date**: 2026-10-06
- **Status**: DECIDED
- **Rationale**:
  - Template Injection Contract: `templates/resume.tex` utilizes explicit LaTeX comment markers (`%%BEGIN:EXPERIENCE:<id>%%`, `%%BEGIN:SLOT:<id>%%` ... `%%END:...%%`). Markers are fully transparent to native TeX compilers while enabling strict stack-based template tree parsing. Unclosed, mismatched, or duplicate markers raise explicit `TemplateSyntaxError` exceptions; guessing is strictly forbidden.
  - Safe LaTeX Escaping & Control Neutralization: Backslash is escaped first to `\textbackslash{}`, followed by special delimiters (`&`, `%`, `$`, `#`, `_`, `{`, `}`, `~`, `^`, `<`, `>`, `|`, `"`) and unicode mappings. Raw control sequences and ASCII non-printable control characters are strictly sanitized to prevent injection attacks or corrupted TeX execution.
  - Empirical Page Budget Boundary: Measured via compile experiments that standard header, education, skills, and leadership leave room for exactly 30 bullet lines on 1 page. Selections exceeding capacity cause page overflow.
  - Multi-Factor Verification Invariants: Compilation uses Tectonic with shell escape disabled, temporary isolated directories per build, and verifies:
    1. Strict single-page fit (`page_count == 1`).
    2. Zero missing bullets (Truth Invariant verified via `pdftotext` with ligature and line-wrap normalization).
    3. Fully embedded fonts (verified via `pdffonts` where all fonts have `emb == yes`).
    4. Text extractability (ATS compliance check).

### D-019: ILP Selection Formulation, Closed-Loop Verification & Truth Invariant Enforcement (P9)
- **Date**: 2026-10-07
- **Status**: DECIDED
- **Rationale**:
  - Deterministic Exact Solver: Modeled bullet selection as an Integer Linear Programming (ILP) problem solved using Google OR-Tools CP-SAT (`ortools.sat.python.cp_model`) with a fixed random seed (`seed=42`) and single-threaded search (`num_search_workers=1`).
  - Integer Scaling & Objective Parity: Coverage weights and variant utilities are integer-scaled ($1000 \cdot \text{ReqScore} + 10 \cdot \sum \text{utility} - 1 \cdot \text{lines}$) to achieve exact bit-level objective value parity against an exhaustive combinatorial `BruteForceOptimizer` reference solver verified across $\ge 200$ randomized test instances.
  - Multi-Level Constraint Satisfaction:
    1. Slot exclusivity: At most 1 variant per slot ($\sum x_{s, v} \le 1$), or exactly 1 if mandatory or pinned ($\sum x_{s, v} = 1$).
    2. Entity bounds: Entity-level constraints strictly enforce $\text{min\_bullets} \le \sum x \le \text{max\_bullets}$.
    3. Capacity budget: Total line consumption across selected bullets cannot exceed available line capacity.
    4. Submodular requirement linking: Requirement coverage variables $cov_r \in \{0, 1\}$ are bounded by $cov_r \le \sum_{v \in \text{matches}} x_{s, v}$ and $cov_r \ge x_{s, v}$ ensuring submodular diminishing returns.
    5. Lexicographical tie-breaking: Primary coverage, secondary utility, tertiary line tie-breaker preferring fewer lines.
  - Structured Infeasibility Diagnostics: When an instance cannot be satisfied, a structured diagnosis engine identifies the root conflict type (`LINE_BUDGET`, `MAX_BULLETS_CONFLICT`, `MIN_BULLETS_UNSATISFIABLE`, or `CONSTRAINTS_CONFLICT`) with exact required lines and conflicting slot identifiers.
  - Closed-Loop Compile Verification & Dynamic Budget Backoff: `ClosedLoopOptimizer` integrates `ILPOptimizer`, `ResumeTemplate`, and `LayoutVerifier`. If layout verification detects page overflow ($> 1$ page), it dynamically decrements the line budget by 1 and re-solves (up to 5 iterations).
  - Byte-for-Byte Truth Invariant: An emitted bullet must exist in the author's Master Profile Bank and match its source text byte-for-byte. Any deviation or hallucinated text raises a fatal `TruthInvariantViolationError`.

### D-020: Granular Selection Diffing, Score Deltas & 1-Click Truth-Invariant Reversion (P10)
- **Date**: 2026-10-07
- **Status**: DECIDED
- **Rationale**:
  - Deterministic Baseline Definition: The user's baseline selection is determined deterministically by selecting the author's marked default variant (`is_default=True`, or `sort_order` lowest) for each slot across their Master Profile Bank (`build_baseline_selection`).
  - Granular Slot Diffing: Every slot is categorized into exact semantic actions:
    - `UNCHANGED`: baseline bullet retained
    - `SWAPPED`: different authored variant selected to boost keyword alignment or utility
    - `ADDED`: slot included from profile to fill capacity budget
    - `OMITTED`: slot omitted to respect strict 1-page line budget constraints
    - `LLM_REWRITTEN`: bullet was dynamically reworded under Decision D-004
  - Explainable Score Deltas: When evaluated against a target JD, the engine calculates exact component score deltas ($\Delta_{\text{total}} = S_{\text{tailored}} - S_{\text{baseline}}$, $\Delta_{\text{lexical}}$, $\Delta_{\text{bm25}}$, $\Delta_{\text{semantic}}$, $\Delta_{\text{quality}}$), pinpointing newly covered requirements and any trade-off losses.
  - 1-Click Rollback & Truth Invariant: Users can revert individual slots or roll back the entire tailored resume in 1 click (`revert_slot`, `revert_all`). All rollbacks enforce the Truth Invariant (reverting only to verified authored variants in the Master Profile Bank) and audit-log every change with UTC timestamps, previous variant IDs, target variant IDs, and reasons.
  - Entity Bounds Preservation: Rollbacks validate entity constraints ($\text{min\_bullets} \le \text{count} \le \text{max\_bullets}$), preventing illegal states.
