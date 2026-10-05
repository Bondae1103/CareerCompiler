# SCORING.md — Resume Scoring, Quality Metrics & Utility Formulas

This document defines the mathematical models, metric quality classifications, and normalization ranges for resume evaluation and optimization.

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

## 2. Utility & Coverage Scoring Formulas (P7 Preview)

### 2.1 Lexical Requirement Coverage Score (`keyword_coverage_score`)
Given a set of extracted JD requirements \( R = \{r_1, r_2, \dots, r_n\} \), each with category weight \( w(r) \):
- \( w(r) = 1.0 \) for `MUST_HAVE` hard requirements.
- \( w(r) = 0.5 \) for `NICE_TO_HAVE` preferred qualifications.

For a selected set of resume bullets \( B \), requirement \( r \) is covered if its canonical ID \( r.\text{canonical\_id} \) matches any canonical tag in the selected bullets or skills sections:
\[
\text{covered}(r) = \begin{cases} 1 & \text{if } r.\text{canonical\_id} \in \bigcup_{b \in B} b.\text{canonical\_tags} \\ 0 & \text{otherwise} \end{cases}
\]

The submodular lexical coverage score is computed as:
\[
S_{\text{lexical}} = 100 \times \frac{\sum_{r \in R} w(r) \cdot \text{covered}(r)}{\sum_{r \in R} w(r)}
\]

### 2.2 Semantic Similarity Score
Cosine similarity between local sentence-transformers embeddings of selected bullets and target JD requirement chunks:
\[
S_{\text{semantic}} = 100 \times \frac{1}{|R|} \sum_{r \in R} \max_{b \in B} \cos(\mathbf{e}_b, \mathbf{e}_r)
\]

### 2.3 Bullet Utility Formula
For ranking candidate bullet variants within a slot:
\[
U(b) = \alpha \cdot \text{Relevance}(b, \text{JD}) + \beta \cdot \text{MetricBonus}(b) - \gamma \cdot \text{LineCost}(b)
\]
Where:
- \( \alpha = 0.60 \) (lexical + semantic match)
- \( \beta = 0.30 \) (metric quality bonus: 0.00 to 0.25)
- \( \gamma = 0.10 \) (penalty for extra lines to promote high-density formatting)
