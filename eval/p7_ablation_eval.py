"""Ablation evaluation script comparing scoring configurations across authentic real JDs.

Evaluates:
1. Lexical Only
2. Lexical + BM25
3. Lexical + BM25 + Semantic
4. Full (Lexical + BM25 + Semantic + Quality)
"""

import sys
from pathlib import Path

from careercompiler.decomposition.decomposer import BulletDecomposer
from careercompiler.extraction.rule_extractor import LocalRuleExtractor
from careercompiler.parsing.resume_parser import parse_latex_resume
from careercompiler.scoring.models import (
    CombinerWeights,
    ScorableBullet,
    ScoringConfig,
)
from careercompiler.scoring.scorer import ResumeScorer


def run_ablation() -> None:
    print("=" * 80)
    print("CAREER COMPILER — PHASE P7 SCORING ABLATION EVALUATION")
    print("=" * 80)

    # 1. Ingest User Resume
    tex_path = Path("resume.tex")
    if not tex_path.exists():
        print("Error: resume.tex not found")
        sys.exit(1)

    profile = parse_latex_resume(tex_path.read_text(encoding="utf-8"))
    decomposer = BulletDecomposer()
    decomp_map = decomposer.decompose_profile(profile)

    bullets: list[ScorableBullet] = []
    for vid, d in decomp_map.items():
        bullets.append(
            ScorableBullet(
                id=vid,
                text=d.raw_text,
                canonical_tags=d.canonical_tags,
                metric_quality=d.metric_quality,
            )
        )

    print(f"Loaded {len(bullets)} resume bullets from master profile.\n")

    # 2. Configurations for Ablation
    configs = {
        "Lexical Only": ScoringConfig(
            combiner=CombinerWeights(
                weight_lexical=1.0,
                weight_bm25=0.0,
                weight_semantic=0.0,
                weight_quality=0.0,
            )
        ),
        "+ BM25": ScoringConfig(
            combiner=CombinerWeights(
                weight_lexical=0.60,
                weight_bm25=0.40,
                weight_semantic=0.0,
                weight_quality=0.0,
            )
        ),
        "+ Semantic": ScoringConfig(
            combiner=CombinerWeights(
                weight_lexical=0.50,
                weight_bm25=0.30,
                weight_semantic=0.20,
                weight_quality=0.0,
            )
        ),
        "Full (+ Quality)": ScoringConfig.load_from_toml(),
    }

    scorers = {name: ResumeScorer(cfg) for name, cfg in configs.items()}
    extractor = LocalRuleExtractor()

    # 3. Evaluate across 10 Real JDs
    jd_dir = Path("data/raw_jds")
    jd_files = sorted(jd_dir.glob("*.txt"))

    print(f"{'Job Description':<40} | {'Lexical':<9} | {'+ BM25':<9} | {'+ Semantic':<11} | {'Full':<9}")
    print("-" * 88)

    for jdf in jd_files:
        jd_text = jdf.read_text(encoding="utf-8")
        extracted_jd = extractor.extract(jd_text)

        scores = {}
        for name, scorer in scorers.items():
            breakdown = scorer.score_selection(bullets, extracted_jd)
            scores[name] = breakdown.total_score

        short_name = jdf.stem[:38]
        print(
            f"{short_name:<40} | "
            f"{scores['Lexical Only']:>7.2f}% | "
            f"{scores['+ BM25']:>7.2f}% | "
            f"{scores['+ Semantic']:>9.2f}% | "
            f"{scores['Full (+ Quality)']:>7.2f}%"
        )

    print("-" * 88)
    print("\nCalibration Status: UNCALIBRATED (Human golden selections pending).")
    print("=" * 80)


if __name__ == "__main__":
    run_ablation()
