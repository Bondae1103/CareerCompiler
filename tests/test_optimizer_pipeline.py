"""Integration tests for the closed-loop optimization and compile verification pipeline."""

from dataclasses import dataclass, field
from pathlib import Path

from careercompiler.layout.template import ResumeTemplate
from careercompiler.layout.verifier import LayoutVerifier
from careercompiler.optimizer.pipeline import ClosedLoopOptimizer
from careercompiler.optimizer.solver import ILPOptimizer


@dataclass
class Variant:
    id: str
    text: str
    lines: int = 1
    utility: float = 0.5
    canonical_tags: list[str] = field(default_factory=list)


@dataclass
class Slot:
    id: str
    variants: list[Variant]
    mandatory: bool = False
    pinned: bool = False


@dataclass
class Entity:
    id: str
    slots: list[Slot]
    min_bullets: int = 0
    max_bullets: int = 999


def test_closed_loop_pipeline_compiles_canonical_profile() -> None:
    """ClosedLoopOptimizer solves, checks Truth Invariant, compiles with Tectonic, and verifies 1-page fit."""
    tex_path = Path("templates/resume.tex")
    tpl = ResumeTemplate(tex_path.read_text(encoding="utf-8"))

    # Construct entities matching template slots
    exp_1 = Entity("exp_1", [
        Slot("exp_1_slot_1", [Variant("e1_v1", "Architected modular end-to-end and REST API test frameworks using Playwright and OOP design patterns, achieving 100% test coverage across enterprise cloud services.", lines=2, utility=0.9, canonical_tags=["playwright", "oop", "rest-api"])], mandatory=True),
        Slot("exp_1_slot_2", [Variant("e1_v2", "Engineered Agentic AI workflows and structured prompt optimization pipelines within CI/CD, automating regression test synthesis to cut feedback cycle latency by 35%.", lines=2, utility=0.85, canonical_tags=["agentic-ai", "ci-cd", "prompt-engineering"])]),
        Slot("exp_1_slot_3", [Variant("e1_v3", "Collaborated in cross-functional Agile teams (Scrum/Kanban) via Jira and Confluence, authoring SOLID-compliant test harnesses to standardize enterprise cloud quality.", lines=2, utility=0.7, canonical_tags=["agile", "jira", "solid"])]),
    ], min_bullets=1, max_bullets=3)

    exp_2 = Entity("exp_2", [
        Slot("exp_2_slot_1", [Variant("e2_v1", "Automated common ETL tasks and data utilities in high-performance POSIX Linux, reducing manual compute overhead and batch data transformation latency by 60%.", lines=2, utility=0.8, canonical_tags=["linux", "bash", "python"])]),
        Slot("exp_2_slot_2", [Variant("e2_v2", "Engineered fault-tolerant Linux Bash pipelines and batch processing scripts, optimizing disk I/O, process concurrency, and memory utilization for molecular research datasets.", lines=2, utility=0.75, canonical_tags=["bash", "linux", "concurrency"])]),
    ], min_bullets=1, max_bullets=2)

    proj_1 = Entity("proj_1", [
        Slot("proj_1_slot_1", [Variant("p1_v1", "Architected an asynchronous, distributed backend microservice with FastAPI, Celery, and Redis as a message broker for concurrent ingestion and structural parsing of documents.", lines=2, utility=0.95, canonical_tags=["fastapi", "celery", "redis", "microservices"])], mandatory=True),
        Slot("proj_1_slot_2", [Variant("p1_v2", "Engineered a hybrid retrieval engine combining PubMedBERT embeddings with BM25 indexing in Qdrant, attaining 100% Recall@5 and 0% hallucination rate on 27 benchmarks.", lines=2, utility=0.9, canonical_tags=["qdrant", "redis", "fastapi"])]),
        Slot("proj_1_slot_3", [Variant("p1_v3", "Implemented low-latency streaming via Server-Sent Events (SSE) with post-hoc citation verification; containerized with Docker Compose and authored a 44-test Pytest suite (100% pass rate).", lines=2, utility=0.8, canonical_tags=["docker", "pytest", "fastapi"])]),
    ], min_bullets=1, max_bullets=3)

    proj_2 = Entity("proj_2", [
        Slot("proj_2_slot_1", [Variant("p2_v1", "Engineered a real-time simulation engine in TypeScript modeling the 158K-neuron Drosophila connectome, implementing Leaky Integrate-and-Fire (LIF) dynamics at 60fps on HTML5 Canvas.", lines=2, utility=0.7, canonical_tags=["typescript", "html"])]),
        Slot("proj_2_slot_2", [Variant("p2_v2", "Built an offline Python pipeline normalizing 1,100+ synaptic inputs; authored an automated Vitest suite verifying 1,000 escape trajectories with 2D boundary collision physics.", lines=2, utility=0.65, canonical_tags=["python", "vitest"])]),
    ], min_bullets=1, max_bullets=2)

    proj_3 = Entity("proj_3", [
        Slot("proj_3_slot_1", [Variant("p3_v1", "Architected a multi-task Graph Convolutional Network (GCN) in PyTorch Geometric across 13,753 clinical isolates to jointly predict resistance phenotypes across 9 anti-TB drugs.", lines=2, utility=0.85, canonical_tags=["pytorch", "pytorch-geometric", "python"])]),
        Slot("proj_3_slot_2", [Variant("p3_v2", "Engineered Jaccard-weighted phylogenetic mutation graphs across 157 loci; conducted ablation studies and was selected for institutional showcase at Gravitas 2026.", lines=2, utility=0.75, canonical_tags=["pytorch", "scikit-learn"])]),
    ], min_bullets=1, max_bullets=2)

    entities = [exp_1, exp_2, proj_1, proj_2, proj_3]

    requirements = [
        ("r1", "fastapi", 1.0),
        ("r2", "redis", 1.0),
        ("r3", "playwright", 1.0),
        ("r4", "docker", 0.5),
        ("r5", "linux", 0.5),
    ]

    pipeline = ClosedLoopOptimizer(
        solver=ILPOptimizer(random_seed=42),
        verifier=LayoutVerifier(timeout=60),
        template=tpl,
        initial_capacity_lines=24,
        max_iterations=3,
    )

    result = pipeline.optimize_and_verify(entities, requirements, enforce_truth_invariant=True)

    assert result.success is True
    assert result.compile_verified is True
    assert result.selection is not None
    assert result.selection.total_lines <= 24
    assert result.verification_errors == []
    # Verify mandatory slots included
    assert result.selection.slot_assignment["exp_1_slot_1"] == "e1_v1"
    assert result.selection.slot_assignment["proj_1_slot_1"] == "p1_v1"
