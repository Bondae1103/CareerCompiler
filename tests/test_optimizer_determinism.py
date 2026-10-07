"""Determinism tests ensuring identical optimizer results across repeated runs."""

import hashlib
import json
from dataclasses import dataclass, field

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


def test_optimizer_strict_determinism_20_runs() -> None:
    """Validate 20 repeated runs on a complex instance yield bit-identical selections and hashes."""
    # Build a realistic candidate profile slice
    e1_s1 = Slot("exp_1_s1", [
        Variant("e1_s1_v1", "Architected distributed streaming engine with Kafka and Go.", 2, 0.85, ["kafka", "go", "distributed_systems"]),
        Variant("e1_s1_v2", "Built event streaming pipeline in Go.", 1, 0.65, ["go", "streaming"]),
    ])
    e1_s2 = Slot("exp_1_s2", [
        Variant("e1_s2_v1", "Engineered REST APIs with FastAPI and PostgreSQL.", 1, 0.75, ["fastapi", "postgresql", "python"]),
        Variant("e1_s2_v2", "Designed high-performance SQL schemas.", 1, 0.50, ["postgresql", "sql"]),
    ], mandatory=True)
    e1_s3 = Slot("exp_1_s3", [
        Variant("e1_s3_v1", "Integrated Redis cache reducing p99 latency by 40%.", 1, 0.90, ["redis", "performance"]),
    ])

    e2_s1 = Slot("proj_1_s1", [
        Variant("p1_s1_v1", "Deployed microservices on AWS EKS with Terraform and Docker.", 2, 0.80, ["aws", "kubernetes", "docker", "terraform"]),
        Variant("p1_s1_v2", "Containerized backend with Docker.", 1, 0.40, ["docker"]),
    ])
    e2_s2 = Slot("proj_1_s2", [
        Variant("p1_s2_v1", "Implemented automated CI/CD pipelines via GitHub Actions.", 1, 0.70, ["ci_cd", "github_actions"]),
    ])

    entities = [
        Entity("exp_1", [e1_s1, e1_s2, e1_s3], min_bullets=1, max_bullets=3),
        Entity("proj_1", [e2_s1, e2_s2], min_bullets=1, max_bullets=2),
    ]

    reqs = [
        ("r1", "go", 1.0),
        ("r2", "fastapi", 1.0),
        ("r3", "redis", 0.5),
        ("r4", "kubernetes", 1.0),
        ("r5", "ci_cd", 0.5),
    ]

    capacity = 4

    hashes: list[str] = []

    for _ in range(20):
        solver = ILPOptimizer(random_seed=42)
        res = solver.optimize(entities, reqs, capacity_lines=capacity)
        assert res.success is True
        assert res.selection is not None

        # Build deterministic fingerprint
        payload = {
            "objective_value": res.selection.objective_value,
            "total_lines": res.selection.total_lines,
            "slot_assignment": res.selection.slot_assignment,
            "covered_requirements": res.selection.covered_requirements,
        }
        raw_json = json.dumps(payload, sort_keys=True).encode("utf-8")
        h = hashlib.sha256(raw_json).hexdigest()
        hashes.append(h)

    # All 20 hashes must be identical
    assert len(set(hashes)) == 1, f"Determinism violated: found multiple hashes: {set(hashes)}"
