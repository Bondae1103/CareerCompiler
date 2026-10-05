"""Deterministic submodular lexical requirement coverage scorer."""

from collections.abc import Iterable

from careercompiler.extraction.models import ExtractedJD, ExtractedRequirement
from careercompiler.scoring.models import RequirementWeights, ScorableBullet


class LexicalCoverageResult:
    """Detailed result of lexical coverage evaluation."""

    def __init__(
        self,
        score: float,
        covered_ids: list[str],
        missing_ids: list[str],
        total_weight: float,
        covered_weight: float,
    ) -> None:
        self.score = score
        self.covered_ids = covered_ids
        self.missing_ids = missing_ids
        self.total_weight = total_weight
        self.covered_weight = covered_weight

    @property
    def coverage_count(self) -> int:
        return len(self.covered_ids)

    @property
    def total_count(self) -> int:
        return len(self.covered_ids) + len(self.missing_ids)


class LexicalScorer:
    """Submodular lexical requirement coverage scorer."""

    def __init__(self, weights: RequirementWeights | None = None) -> None:
        self.weights = weights or RequirementWeights()

    def get_requirement_weight(self, req: ExtractedRequirement) -> float:
        """Get the numerical weight for a requirement based on its category."""
        category_str = req.category.value if hasattr(req.category, "value") else str(req.category)
        if category_str == "must_have":
            return self.weights.must_have
        elif category_str == "nice_to_have":
            return self.weights.nice_to_have
        return self.weights.nice_to_have

    def score_coverage(
        self,
        bullets: Iterable[ScorableBullet],
        jd: ExtractedJD,
        extra_skills: Iterable[str] | None = None,
    ) -> LexicalCoverageResult:
        """Score submodular requirement coverage across bullets and optional extra skill tags."""
        # 1. Aggregate candidate canonical tags into a unified set
        candidate_tags: set[str] = set()
        for b in bullets:
            for tag in b.canonical_tags:
                candidate_tags.add(tag.lower())

        if extra_skills:
            for s in extra_skills:
                candidate_tags.add(s.lower())

        # 2. Evaluate coverage over all JD requirements
        covered_ids: list[str] = []
        missing_ids: list[str] = []
        total_weight = 0.0
        covered_weight = 0.0

        for req in jd.all_requirements:
            w = self.get_requirement_weight(req)
            total_weight += w

            req_key = (req.canonical_id or req.surface_form).lower()
            reported_id = req.canonical_id or req.surface_form
            # A requirement is covered if its canonical_id or surface form is present
            if req_key in candidate_tags:
                covered_ids.append(reported_id)
                covered_weight += w
            else:
                missing_ids.append(reported_id)

        # Deterministic sorting
        covered_ids.sort()
        missing_ids.sort()

        if total_weight <= 0.0:
            score = 100.0
        else:
            score = round(100.0 * (covered_weight / total_weight), 4)

        return LexicalCoverageResult(
            score=score,
            covered_ids=covered_ids,
            missing_ids=missing_ids,
            total_weight=total_weight,
            covered_weight=covered_weight,
        )

    def marginal_delta(
        self,
        candidate_bullet: ScorableBullet,
        current_selection: Iterable[ScorableBullet],
        jd: ExtractedJD,
        extra_skills: Iterable[str] | None = None,
    ) -> float:
        """Compute the marginal score increase obtained by adding candidate_bullet."""
        base_res = self.score_coverage(current_selection, jd, extra_skills)
        combined = list(current_selection) + [candidate_bullet]
        new_res = self.score_coverage(combined, jd, extra_skills)
        return max(0.0, round(new_res.score - base_res.score, 4))
