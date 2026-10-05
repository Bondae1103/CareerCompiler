"""Main scoring orchestrator combining Lexical, BM25, Semantic, and Quality models."""

from collections.abc import Sequence

from careercompiler.decomposition.models import MetricQuality
from careercompiler.extraction.models import ExtractedJD
from careercompiler.scoring.bm25 import BM25Scorer
from careercompiler.scoring.lexical import LexicalScorer
from careercompiler.scoring.models import (
    BulletUtility,
    ScorableBullet,
    ScoreBreakdown,
    ScoringConfig,
)
from careercompiler.scoring.semantic import SemanticScorer


class ResumeScorer:
    """Deterministic resume scorer enforcing Explainability and Monotonicity invariants."""

    def __init__(self, config: ScoringConfig | None = None) -> None:
        self.config = config or ScoringConfig.load_from_toml()
        self.lexical_scorer = LexicalScorer(self.config.requirements)
        self.bm25_scorer = BM25Scorer(self.config.bm25)
        self.semantic_scorer = SemanticScorer(self.config.semantic)

    def compute_quality_score(self, bullets: Sequence[ScorableBullet]) -> float:
        """Compute normalized quality score across candidate bullets."""
        if not bullets:
            return 0.0

        mq_cfg = self.config.metric_quality
        quality_map = {
            MetricQuality.QUANTIFIED_WITH_BASELINE: mq_cfg.quantified_with_baseline,
            MetricQuality.QUANTIFIED: mq_cfg.quantified,
            MetricQuality.VAGUE: mq_cfg.vague,
            MetricQuality.NONE: mq_cfg.none,
        }

        total_ratio = sum(quality_map.get(b.metric_quality, 0.0) for b in bullets)
        raw = 100.0 * (total_ratio / len(bullets))
        return min(100.0, max(0.0, round(raw, 4)))

    def score_selection(
        self,
        bullets: Sequence[ScorableBullet],
        jd: ExtractedJD,
        extra_skills: Sequence[str] | None = None,
        bank_bullet_texts: Sequence[str] | None = None,
    ) -> ScoreBreakdown:
        """Compute full selection score breakdown satisfying the Explainability Invariant."""
        # 1. Component scores
        lex_res = self.lexical_scorer.score_coverage(bullets, jd, extra_skills)
        bm25_score = self.bm25_scorer.score_selection(bullets, jd, bank_bullet_texts)
        sem_score = self.semantic_scorer.score_selection(bullets, jd)
        qual_score = self.compute_quality_score(bullets)

        # 2. Weighted component contributions
        comb = self.config.combiner
        c_lex = round(comb.weight_lexical * lex_res.score, 4)
        c_bm25 = round(comb.weight_bm25 * bm25_score, 4)
        c_sem = round(comb.weight_semantic * sem_score, 4)
        c_qual = round(comb.weight_quality * qual_score, 4)

        # 3. Sum contributions to guarantee Explainability Invariant
        total_score = round(c_lex + c_bm25 + c_sem + c_qual, 4)

        contributions = {
            "lexical": c_lex,
            "bm25": c_bm25,
            "semantic": c_sem,
            "quality": c_qual,
        }

        return ScoreBreakdown(
            total_score=total_score,
            lexical_score=lex_res.score,
            bm25_score=bm25_score,
            semantic_score=sem_score,
            quality_score=qual_score,
            coverage_count=lex_res.coverage_count,
            total_requirements=lex_res.total_count,
            covered_requirements=lex_res.covered_ids,
            missing_requirements=lex_res.missing_ids,
            component_contributions=contributions,
        )

    def score_bullet_utility(
        self,
        bullet: ScorableBullet,
        jd: ExtractedJD,
        bank_bullet_texts: Sequence[str] | None = None,
    ) -> BulletUtility:
        """Compute slot-level utility for ranking bullet variants."""
        # Matched canonical tags
        reqs = jd.all_requirements
        bullet_tags = {t.lower() for t in bullet.canonical_tags}
        matched = [
            (r.canonical_id or r.surface_form)
            for r in reqs
            if (r.canonical_id or r.surface_form).lower() in bullet_tags
        ]

        lex_rel = (len(matched) / max(1, len(reqs))) if reqs else 1.0
        bm25_rel = self.bm25_scorer.score_single_bullet(bullet.text, jd, bank_bullet_texts) / 100.0
        sem_rel = self.semantic_scorer.score_single_bullet(bullet.text, jd) / 100.0

        # Metric bonus
        mq_cfg = self.config.metric_quality
        bonus_map = {
            MetricQuality.QUANTIFIED_WITH_BASELINE: mq_cfg.bonus_quantified_with_baseline,
            MetricQuality.QUANTIFIED: mq_cfg.bonus_quantified,
            MetricQuality.VAGUE: mq_cfg.bonus_vague,
            MetricQuality.NONE: mq_cfg.bonus_none,
        }
        quality_bonus = bonus_map.get(bullet.metric_quality, 0.0)

        # Line penalty
        overflow_lines = max(0, bullet.lines - 1)
        line_penalty = overflow_lines * self.config.utility.overflow_line_cost

        # Overall utility
        u_cfg = self.config.utility
        lex_c = round(u_cfg.alpha_relevance * 0.50 * lex_rel, 4)
        bm25_c = round(u_cfg.alpha_relevance * 0.30 * bm25_rel, 4)
        sem_c = round(u_cfg.alpha_relevance * 0.20 * sem_rel, 4)
        qual_c = round(u_cfg.beta_quality * quality_bonus, 4)
        line_p = round(u_cfg.gamma_line_cost * line_penalty, 4)

        total_u = round(lex_c + bm25_c + sem_c + qual_c - line_p, 4)

        explanation = (
            f"Utility {total_u:.4f} (Matched: {len(matched)} reqs, "
            f"Quality: {bullet.metric_quality.value}, Lines: {bullet.lines})"
        )

        return BulletUtility(
            bullet_id=bullet.id,
            total_utility=total_u,
            lexical_contribution=lex_c,
            bm25_contribution=bm25_c,
            semantic_contribution=sem_c,
            quality_bonus=qual_c,
            line_penalty=line_p,
            matched_requirements=matched,
            explanation=explanation,
        )
