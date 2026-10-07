"""Parity tests between CP-SAT ILPOptimizer and exact BruteForceOptimizer."""

import random
from dataclasses import dataclass, field

from careercompiler.optimizer.brute_force import BruteForceOptimizer
from careercompiler.optimizer.solver import ILPOptimizer


@dataclass
class MockVariant:
    id: str
    text: str
    lines: int
    utility: float
    canonical_tags: list[str] = field(default_factory=list)


@dataclass
class MockSlot:
    id: str
    variants: list[MockVariant]
    mandatory: bool = False
    pinned: bool = False


@dataclass
class MockEntity:
    id: str
    slots: list[MockSlot]
    min_bullets: int = 0
    max_bullets: int = 999


def test_optimizer_brute_force_parity_200_instances() -> None:
    """Validate ILPOptimizer achieves exact objective value parity with BruteForceOptimizer across >= 200 random instances."""
    rng = random.Random(1337)
    ilp_solver = ILPOptimizer(weight_scale=1000, utility_scale=10, random_seed=42)
    bf_solver = BruteForceOptimizer(weight_scale=1000, utility_scale=10)

    tags_pool = ["python", "docker", "fastapi", "redis", "sql", "aws", "pytest", "c++"]

    total_instances = 220
    evaluated = 0

    for i in range(total_instances):
        # Generate 1 or 2 entities
        num_entities = rng.choice([1, 2])
        entities = []
        slot_counter = 0

        for e_idx in range(num_entities):
            num_slots = rng.randint(1, 3)
            slots = []
            for _ in range(num_slots):
                slot_id = f"s_{slot_counter}"
                slot_counter += 1
                num_variants = rng.randint(1, 2)
                variants = []
                for v_idx in range(num_variants):
                    v_id = f"v_{slot_id}_{v_idx}"
                    v_lines = rng.choice([1, 2])
                    v_util = round(rng.uniform(0.0, 1.0), 2)
                    v_tags = rng.sample(tags_pool, k=rng.randint(0, 2))
                    variants.append(
                        MockVariant(
                            id=v_id,
                            text=f"Text for {v_id}",
                            lines=v_lines,
                            utility=v_util,
                            canonical_tags=v_tags,
                        )
                    )
                is_mandatory = rng.random() < 0.25
                slots.append(MockSlot(id=slot_id, variants=variants, mandatory=is_mandatory))

            min_b = rng.randint(0, 1)
            max_b = rng.randint(min_b, max(min_b, len(slots)))
            entities.append(MockEntity(id=f"e_{e_idx}", slots=slots, min_bullets=min_b, max_bullets=max_b))

        # Generate requirements
        num_reqs = rng.randint(1, 4)
        reqs = []
        for r_idx in range(num_reqs):
            req_tag = rng.choice(tags_pool)
            req_weight = rng.choice([0.5, 1.0])
            reqs.append((f"req_{r_idx}", req_tag, req_weight))

        capacity = rng.randint(1, 6)

        # Solve both
        bf_res = bf_solver.solve(entities, reqs, capacity_lines=capacity)
        ilp_res = ilp_solver.optimize(entities, reqs, capacity_lines=capacity)

        if bf_res is None:
            assert not ilp_res.success, f"Instance {i}: BF found no solution, but ILP claimed success!"
        else:
            assert ilp_res.success, (
                f"Instance {i}: BF found feasible solution with score {bf_res.objective_value}, "
                f"but ILP claimed infeasible! Reason: {ilp_res.infeasibility_reason}"
            )
            assert ilp_res.selection is not None
            assert ilp_res.selection.objective_value == bf_res.objective_value, (
                f"Instance {i}: Objective mismatch! ILP={ilp_res.selection.objective_value} vs BF={bf_res.objective_value}"
            )
            assert ilp_res.selection.total_lines <= capacity

        evaluated += 1

    assert evaluated >= 200
