# SPEC.md — Career Compiler: Project Specification

## 1. User Vision & Requirements (Verbatim)

### Original Vision Statement (2026-10-01)
> "The user can either input their resumes or add all of their projects and experiences on this platform. then, the user can keep inputting JDs as they come so that the app generates specific resumes for that role. these resumes would go through several iterative ATS scoring to find the optimum and users should also be able to revert any of the changes."
>
> "make a small product description of this project. (just the basic workflow and vision behind it). also, i really want the chunking algo to be very accurate (ie, the resume/user data as well as the JDs shud be perfectly chunked into correct keywords)"

---

## 2. Product Description & High-Level Workflow

### Vision
Transform the job application process from "blindly spraying static resumes" or "trusting black-box AI rewrites" into a **deterministic, profile-backed career compiler**. It matches verified experiences to any Job Description with high-precision keyword optimization, pixel-perfect 1-page LaTeX rendering, and total user control with granular bullet-level diffing and rollbacks.

### End-to-End Workflow
1. **Master Profile Intake**: Enter education, work experiences, side projects, research, and technical skills once. For each project, multiple bullet variations emphasize different angles (performance, architecture, product impact).
2. **JD Deconstruction & Chunking**: Decompose raw job descriptions into hard technical skills, domain concepts, and implicit scale requirements with character-offset evidence spans.
3. **Smart Selection & Optimization**: Algorithmic selection (ILP/exact solver) of the highest-scoring combination of real projects and bullets that:
   - Maximizes lexical keyword coverage (exact matches).
   - Maximizes semantic alignment with the role.
   - Strictly respects physical line-budget constraints to guarantee a 1-page fit.
4. **Transparent Diff & 1-Click Revert**: Side-by-side inspect what was swapped, added, or omitted, accompanied by keyword score deltas. Individual bullets can be reverted with one click.
5. **Deterministic LaTeX PDF Compilation**: Inject selected bullets directly into the LaTeX template (`resume.tex`) and compile via Tectonic.

---

## 3. High-Accuracy Chunking Architecture

1. **Tier 1: Hierarchical Document Tree Parser (AST)**:
   - Breaks text into typed blocks: `[Section] -> [Entity/Role] -> [Bullet/Clause]` with exact character start/end offsets.
2. **Tier 2: Deterministic Entity Gazetteer + Normalizer**:
   - Matches against an open taxonomy of tech terms.
   - Resolves aliases (e.g. `K8s` -> `kubernetes`, `React.js` -> `react`, `Postgres` -> `postgresql`).
   - Boundary-safe, case-sensitive matching for ambiguous short terms (`Go`, `C`, `R`).
3. **Tier 3: Constrained Semantic Extractor**:
   - Schema-constrained parsing into Action-Context-Tool-Result (ACTR) tuples for resumes.
   - Categorized requirement buckets (Must-Have vs. Nice-to-Have, Hard Requirements, Scale Indicators) for JDs.
