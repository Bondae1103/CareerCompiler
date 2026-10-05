# SCORING.md — Resume Scoring, Quality Metrics & Utility Formulas

This document defines the mathematical models, metric quality classifications, normalization ranges, and configuration specifications for resume scoring, ranking, and optimization.

---

## 1. Metric Quality Classification (P6)

Every bullet point is analyzed to determine the degree of empirical quantification in its accomplishment statement.

| Category | Description | Criteria | Quality Bonus |
| :--- | :--- | :--- | :--- |
| `NONE` | Purely descriptive; no performance, latency, scale, or business outcome mentioned. | No metric patterns, impact verbs, or comparative indicators detected. | `0.00` |
| `VAGUE` | Qualitative impact claimed without concrete measurement. | Contains impact cue words (e.g., *improved*, *optimized*, *faster*, *reduced bottlenecks*, *scaled*, *enhanced*) but lacks specific numbers or units. | `+0.05` |
| `QUANTIFIED` | Quantified outcome with concrete number and unit. | Contains at least one verified numerical metric (percentage, throughput, latency, count, currency, multiplier) directly attested in the source text. | `+0.15` |
| `QUANTIFIED_WITH_BASELINE` | Quantified outcome featuring both baseline and end state. | Contains comparative trajectory (*from X to Y*, *cut by Z% from W*, *grew from A to B*) with verified numbers for both states. | `+0.25` |

### Negative Exclusions for Impact Metrics
The following numerical patterns are explicitly **disqualified** from being classified as impact metrics:
1. **Software Versions**: e.g., `Python 3.11`, `PostgreSQL 16`, `v2.0`, `YOLOv8`, `ES6`, `HTML5`, `C++20`.
2. **Calendar Dates & Years**: e.g., `2023`, `2024`, `2025`, `2026`, `May 2026`, `Semester 1`.
3. **Availability / Time Slices**: e.g., `24/7`, `9 to 5`, `round-the-clock`.
4. **Identifiers & Phone Numbers**: e.g., `+91 8547560400`, `NCT01234567`.

---

## 2. BM25 Corpus Evaluation & Findings

BM25 relies on Inverse Document Frequency ($IDF$):
\[
\text{IDF}(t) = \ln\left( \frac{N - n(t) + 0.5}{n(t) + 0.5} + 1.0 \right)
\]
Where $N$ is the number of documents in the background corpus, and $n(t)$ is the number of documents containing term $t$.

### Empirical Comparison of Corpus Choices
When matching resume bullets ($N_{\text{bullets}} \approx 12-50$) against Job Description requirement chunks ($N_{\text{chunks}} \approx 15-40$):

1. **`jd_only` Corpus ($N \approx 30$)**:
   - *Defect*: Terms appearing in many JD chunks (e.g., `software`, `experience`, `engineering`) have severely depressed IDF. Terms absent from the JD have no frequency context.
   - *Result*: Noisy scores heavily skewed towards arbitrary JD chunk splits.
2. **`bank_only` Corpus ($N \approx 12-50$)**:
   - *Defect*: Extremely small $N$. If candidate has only 12 bullets, common resume verbs (`built`, `engineered`) dominate, while rare skills receive disproportionate weight.
3. **`bank_plus_jd` Corpus ($N \approx 45-90$) [RECOMMENDED & SELECTED]**:
   - *Advantage*: Indexes both candidate profile variants and target JD requirement chunks simultaneously.
   - *Behavior*: Domain-wide commonalities (`software`, `team`, `development`) are consistently down-weighted, while specialized technical skills (`qdrant`, `fastapi`, `celery`, `lif`) maintain stable, informative IDF values.

---

## 3. Mathematical Scoring Components

### 3.1 Lexical Requirement Coverage Score ($S_{\text{lexical}}$)
Given extracted JD requirements $R = \{r_1, r_2, \dots, r_n\}$, each requirement $r$ has category weight $w(r)$:
- $w(r) = 1.0$ for `must_have` hard requirements.
- $w(r) = 0.5$ for `nice_to_have` preferred qualifications.

For a candidate selection of resume bullets and skills $B$:
\[
\text{covered}(r) = \begin{cases} 1 & \text{if } r.\text{canonical\_id} \in \bigcup_{b \in B} b.\text{canonical\_tags} \\ 0 & \text{otherwise} \end{cases}
\]

Submodular set coverage ensures each requirement is counted **at most once**, regardless of how many bullets repeat the skill:
\[
S_{\text{lexical}} = \begin{cases} 100.0 \times \frac{\sum_{r \in R} w(r) \cdot \text{covered}(r)}{\sum_{r \in R} w(r)} & \text{if } \sum_{r \in R} w(r) > 0 \\ 100.0 & \text{if } |R| = 0 \end{cases}
\]

*Monotonicity Invariant*: Adding a bullet to $B$ never decreases $S_{\text{lexical}}$. Redundant bullets covering already-covered requirements yield $\Delta S_{\text{lexical}} = 0$.

---

### 3.2 BM25 Relevance Score ($S_{\text{bm25}}$)
Using Okapi BM25 parameters $k_1 = 1.5$, $b = 0.75$, indexed over the `bank_plus_jd` corpus.
For each requirement chunk $r \in R$ treated as a query, the maximum BM25 match across selected bullets $b \in B$ is aggregated:
\[
\text{raw\_bm25}(r, B) = \max_{b \in B} \text{BM25}(b, r)
\]
Normalized across requirements:
\[
S_{\text{bm25}} = \min\left(100.0, \; \frac{100.0}{|R|} \sum_{r \in R} \tanh\left(\frac{\text{raw\_bm25}(r, B)}{k_{\text{norm}}}\right)\right)
\]
Where $k_{\text{norm}} = 5.0$ scales typical BM25 values into $[0, 1]$.

---

### 3.3 Semantic Similarity Score ($S_{\text{semantic}}$)
Cosine similarity between normalized embedding vectors of selected bullets $\mathbf{e}_b$ and JD requirement chunks $\mathbf{e}_r$:
\[
\cos(\mathbf{e}_b, \mathbf{e}_r) = \frac{\mathbf{e}_b \cdot \mathbf{e}_r}{\|\mathbf{e}_b\|_2 \|\mathbf{e}_r\|_2}
\]
For selection $B$ across requirements $R$:
\[
S_{\text{semantic}} = \frac{100.0}{|R|} \sum_{r \in R} \max\left(0.0, \; \max_{b \in B} \cos(\mathbf{e}_b, \mathbf{e}_r)\right)
\]
*(Embeddings use deterministic offline hashing n-gram features by default, or pinned `sentence-transformers/all-MiniLM-L6-v2` when installed).*

---

### 3.4 Metric Quality Score ($S_{\text{quality}}$)
Measures the average accomplishment strength of selected bullets $B$:
\[
S_{\text{quality}} = \frac{100.0}{|B|} \sum_{b \in B} \text{QualityRatio}(b)
\]
Where:
- $\text{QualityRatio}(\text{QUANTIFIED\_WITH\_BASELINE}) = 1.00$
- $\text{QualityRatio}(\text{QUANTIFIED}) = 0.75$
- $\text{QualityRatio}(\text{VAGUE}) = 0.25$
- $\text{QualityRatio}(\text{NONE}) = 0.00$

---

## 4. Selection Combiner & Explainability Invariant

The total resume selection score $S_{\text{total}} \in [0.0, 100.0]$ is a linear combination of the normalized components:
\[
S_{\text{total}} = w_{\text{lex}} \cdot S_{\text{lexical}} + w_{\text{bm25}} \cdot S_{\text{bm25}} + w_{\text{sem}} \cdot S_{\text{semantic}} + w_{\text{qual}} \cdot S_{\text{quality}}
\]

### Explainability Invariant (Strict)
Every score returned by the engine includes a detailed `ScoreBreakdown` mapping each component to its exact point contribution:
\[
\text{contribution}(c) = w_c \cdot S_c
\]
\[
S_{\text{total}} = \sum_{c \in \{\text{lexical}, \text{bm25}, \text{semantic}, \text{quality}\}} \text{contribution}(c)
\]
No magic numbers or unaccounted adjustments are permitted.

---

## 5. Per-Bullet Slot Utility Formula $U(b)$

To rank bullet variants within a specific `BulletSlot`:
\[
U(b) = \alpha \cdot \text{Relevance}(b, \text{JD}) + \beta \cdot \text{MetricBonus}(b) - \gamma \cdot \text{LineCost}(b)
\]
Where:
- $\text{Relevance}(b, \text{JD}) = 0.5 \cdot \text{LexicalMatch}(b, R) + 0.5 \cdot \max_{r \in R} \cos(\mathbf{e}_b, \mathbf{e}_r)$
- $\text{MetricBonus}(b) \in \{0.00, 0.05, 0.15, 0.25\}$
- $\text{LineCost}(b) = \max(0, \text{lines}(b) - 1) \times 0.05$ (penalizes multi-line overflow)

---

## 6. Configuration & Calibration Status

Default weights are version-controlled in `careercompiler/scoring/scoring.toml`.
Current calibration status: `UNCALIBRATED` (marked pending human labeled resume-JD golden selections).
