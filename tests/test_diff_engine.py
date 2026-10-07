"""Tests for DiffEngine calculating slot-level diffs and score deltas."""

from dataclasses import dataclass, field

from careercompiler.diff.engine import DiffEngine
from careercompiler.diff.models import DiffActionType
from careercompiler.extraction.models import (
    ExtractedJD,
    ExtractedRequirement,
    RequirementCategory,
)
from careercompiler.optimizer.models import SelectedBullet, Selection
from careercompiler.scoring.scorer import ResumeScorer


@dataclass
class Variant:
    id: str
    text: str
    is_default: bool = False
    lines: int = 1
    utility: float = 0.5
    is_llm_rewritten: bool = False
    canonical_tags: list[str] = field(default_factory=list)


@dataclass
class Slot:
    id: str
    variants: list[Variant]


@dataclass
class Entity:
    id: str
    slots: list[Slot]


def test_diff_engine_detects_all_action_types() -> None:
    """DiffEngine correctly classifies UNCHANGED, SWAPPED, ADDED, OMITTED, and LLM_REWRITTEN actions."""
    # s1: unchanged (v1_1 -> v1_1)
    # s2: swapped (v2_1 -> v2_2)
    # s3: omitted (v3_1 -> None)
    # s4: added (None -> v4_1)
    # s5: llm rewritten (v5_1 -> v5_rewritten)

    v1_1 = Variant("v1_1", "Unchanged bullet", lines=1, utility=0.5, canonical_tags=["python"])
    v2_1 = Variant("v2_1", "Baseline variant", lines=1, utility=0.4, canonical_tags=["docker"])
    v2_2 = Variant("v2_2", "Tailored variant", lines=2, utility=0.8, canonical_tags=["docker", "kubernetes"])
    v3_1 = Variant("v3_1", "Omitted bullet", lines=1, utility=0.3, canonical_tags=["sql"])
    v4_1 = Variant("v4_1", "Added bullet", lines=1, utility=0.7, canonical_tags=["fastapi"])
    v5_1 = Variant("v5_1", "Original draft", lines=1, utility=0.5, canonical_tags=["aws"])
    v5_rewritten = Variant("v5_rewritten", "Dynamic rewrite", lines=1, utility=0.9, is_llm_rewritten=True, canonical_tags=["aws"])

    slots = [
        Slot("s1", [v1_1]),
        Slot("s2", [v2_1, v2_2]),
        Slot("s3", [v3_1]),
        Slot("s4", [v4_1]),
        Slot("s5", [v5_1, v5_rewritten]),
    ]
    entity = Entity("exp_1", slots)

    baseline = Selection(
        selected_bullets=[
            SelectedBullet(slot_id="s1", variant_id="v1_1", entity_id="exp_1", text=v1_1.text, lines=1, utility=0.5, canonical_tags=["python"]),
            SelectedBullet(slot_id="s2", variant_id="v2_1", entity_id="exp_1", text=v2_1.text, lines=1, utility=0.4, canonical_tags=["docker"]),
            SelectedBullet(slot_id="s3", variant_id="v3_1", entity_id="exp_1", text=v3_1.text, lines=1, utility=0.3, canonical_tags=["sql"]),
            SelectedBullet(slot_id="s5", variant_id="v5_1", entity_id="exp_1", text=v5_1.text, lines=1, utility=0.5, canonical_tags=["aws"]),
        ],
        slot_assignment={"s1": "v1_1", "s2": "v2_1", "s3": "v3_1", "s4": None, "s5": "v5_1"},
        total_lines=4,
        covered_requirements=["aws", "docker", "python", "sql"],
        objective_value=10.0,
        solve_time_seconds=0.01,
        solver_status="OPTIMAL",
    )

    tailored = Selection(
        selected_bullets=[
            SelectedBullet(slot_id="s1", variant_id="v1_1", entity_id="exp_1", text=v1_1.text, lines=1, utility=0.5, canonical_tags=["python"]),
            SelectedBullet(slot_id="s2", variant_id="v2_2", entity_id="exp_1", text=v2_2.text, lines=2, utility=0.8, canonical_tags=["docker", "kubernetes"]),
            SelectedBullet(slot_id="s4", variant_id="v4_1", entity_id="exp_1", text=v4_1.text, lines=1, utility=0.7, canonical_tags=["fastapi"]),
            SelectedBullet(slot_id="s5", variant_id="v5_rewritten", entity_id="exp_1", text=v5_rewritten.text, lines=1, utility=0.9, canonical_tags=["aws"]),
        ],
        slot_assignment={"s1": "v1_1", "s2": "v2_2", "s3": None, "s4": "v4_1", "s5": "v5_rewritten"},
        total_lines=5,
        covered_requirements=["aws", "docker", "fastapi", "kubernetes", "python"],
        objective_value=15.0,
        solve_time_seconds=0.01,
        solver_status="OPTIMAL",
    )

    engine = DiffEngine()
    diff = engine.compute_diff(baseline, tailored, [entity], job_id="job_backend")

    assert diff.total_unchanged == 1
    assert diff.total_swapped == 2  # s2 (swapped) + s5 (llm_rewritten)
    assert diff.total_added == 1
    assert diff.total_omitted == 1
    assert diff.line_budget_delta == 1

    actions_by_slot = {bd.slot_id: bd.action for bd in diff.bullet_diffs}
    assert actions_by_slot["s1"] == DiffActionType.UNCHANGED
    assert actions_by_slot["s2"] == DiffActionType.SWAPPED
    assert actions_by_slot["s3"] == DiffActionType.OMITTED
    assert actions_by_slot["s4"] == DiffActionType.ADDED
    assert actions_by_slot["s5"] == DiffActionType.LLM_REWRITTEN

    # Check s2 tag delta and line delta
    s2_diff = next(bd for bd in diff.bullet_diffs if bd.slot_id == "s2")
    assert s2_diff.added_tags == ["kubernetes"]
    assert s2_diff.removed_tags == []
    assert s2_diff.line_delta == 1
    assert s2_diff.utility_delta == 0.4
    assert s2_diff.can_revert is True
    assert s2_diff.revert_to_variant_id == "v2_1"


def test_diff_engine_computes_exact_score_delta() -> None:
    """DiffEngine computes exact component-level score deltas when scorer and JD are provided."""
    v1 = Variant("v1", "Developed REST APIs using Python and FastAPI.", lines=1, canonical_tags=["python", "fastapi"])
    v2 = Variant("v2", "Architected containerized microservices on AWS with Docker.", lines=1, canonical_tags=["aws", "docker"])

    s1 = Slot("s1", [v1, v2])
    entity = Entity("exp_1", [s1])

    # Baseline has v1 (covers python)
    baseline = Selection(
        selected_bullets=[
            SelectedBullet(slot_id="s1", variant_id="v1", entity_id="exp_1", text=v1.text, lines=1, utility=0.5, canonical_tags=["python", "fastapi"])
        ],
        slot_assignment={"s1": "v1"},
        total_lines=1,
        covered_requirements=["fastapi", "python"],
        objective_value=1.0,
        solve_time_seconds=0.01,
        solver_status="OPTIMAL",
    )

    # Tailored has v2 (covers docker and aws)
    tailored = Selection(
        selected_bullets=[
            SelectedBullet(slot_id="s1", variant_id="v2", entity_id="exp_1", text=v2.text, lines=1, utility=0.8, canonical_tags=["aws", "docker"])
        ],
        slot_assignment={"s1": "v2"},
        total_lines=1,
        covered_requirements=["aws", "docker"],
        objective_value=2.0,
        solve_time_seconds=0.01,
        solver_status="OPTIMAL",
    )

    req1 = ExtractedRequirement(
        id="r1",
        canonical_id="docker",
        surface_form="Docker",
        evidence_span=(10, 16),
        evidence_text="Docker",
        category=RequirementCategory.MUST_HAVE,
    )
    req2 = ExtractedRequirement(
        id="r2",
        canonical_id="aws",
        surface_form="AWS",
        evidence_span=(21, 24),
        evidence_text="AWS",
        category=RequirementCategory.MUST_HAVE,
    )
    jd = ExtractedJD(
        role_title="Backend Engineer",
        hard_requirements=[req1, req2],
        preferred_qualifications=[],
        scale_indicators=[],
        extractor_name="test_extractor",
        cache_key="test_cache_key",
    )

    scorer = ResumeScorer()
    engine = DiffEngine(scorer=scorer)

    diff = engine.compute_diff(baseline, tailored, [entity], jd=jd)

    assert diff.score_delta is not None
    sd = diff.score_delta
    # Tailored covers docker and aws (100% of JD), baseline covers neither (0%)
    assert sd.tailored_score.total_score > sd.baseline_score.total_score
    assert sd.delta_total == round(sd.tailored_score.total_score - sd.baseline_score.total_score, 4)
    assert set(sd.newly_covered_requirements) == {"docker", "aws"}
