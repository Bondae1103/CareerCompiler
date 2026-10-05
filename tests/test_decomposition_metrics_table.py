"""Table-driven test suite for impact metric extraction and normalization."""

import pytest

from careercompiler.decomposition.metrics import (
    classify_metric_quality,
    extract_impact_metrics,
)
from careercompiler.decomposition.models import MetricQuality

# (text, expected_metric_count, expected_normalized_values, expected_units, expected_quality)
METRIC_TEST_CASES = [
    # Spec example 1: 45k ops/sec
    (
        "Engineered Raft consensus achieving 45k ops/sec across 5-node cluster.",
        1,
        [45000.0],
        ["ops/sec"],
        MetricQuality.QUANTIFIED,
    ),
    # Spec example 2: <5ms p99
    (
        "Optimized Redis cache layer to achieve <5ms p99 latency under load.",
        1,
        [5.0],
        ["ms"],
        MetricQuality.QUANTIFIED,
    ),
    # Percentages
    (
        "Automated regression testing pipelines cutting feedback latency by 35%.",
        1,
        [35.0],
        ["%"],
        MetricQuality.QUANTIFIED,
    ),
    (
        "Directed recruitment funnels to drive 21% net club growth.",
        1,
        [21.0],
        ["%"],
        MetricQuality.QUANTIFIED,
    ),
    (
        "Attained 100% Recall@5 and 0% hallucination rate on benchmarks.",
        2,
        [100.0, 0.0],
        ["%", "%"],
        MetricQuality.QUANTIFIED,
    ),
    # Latencies
    (
        "Real-time pathology detection under 50ms latency.",
        1,
        [50.0],
        ["ms"],
        MetricQuality.QUANTIFIED,
    ),
    # Framerate
    (
        "Implemented LIF dynamics at 60fps on HTML5 Canvas.",
        1,
        [60.0],
        ["fps"],
        MetricQuality.QUANTIFIED,
    ),
    # Multipliers
    (
        "Refactored indexing pipeline to yield 2x throughput speedup.",
        1,
        [2.0],
        ["x"],
        MetricQuality.QUANTIFIED,
    ),
    # Scale counts with suffixes
    (
        "Modelled 158K neurons across phylogenetic mutation graphs.",
        1,
        [158000.0],
        ["neurons"],
        MetricQuality.QUANTIFIED,
    ),
    (
        "Tested across 13,753 clinical isolates to jointly predict phenotypes.",
        1,
        [13753.0],
        ["clinical isolates"],
        MetricQuality.QUANTIFIED,
    ),
    # Baseline Transition
    (
        "Reduced mean query latency from 120ms to 45ms across all endpoints.",
        1,
        [45.0],
        ["transition"],
        MetricQuality.QUANTIFIED_WITH_BASELINE,
    ),
    # Currency
    (
        "Raised $8.5M series A funding from top tier investors.",
        1,
        [8500000.0],
        ["usd"],
        MetricQuality.QUANTIFIED,
    ),
    # Vague (No numbers, but qualitative claims)
    (
        "Worked on improving and optimizing database query performance.",
        0,
        [],
        [],
        MetricQuality.VAGUE,
    ),
    # None (Descriptive only)
    (
        "Constructed object-oriented backend microservices with FastAPI.",
        0,
        [],
        [],
        MetricQuality.NONE,
    ),
]


@pytest.mark.parametrize(
    "text,expected_count,expected_values,expected_units,expected_quality",
    METRIC_TEST_CASES,
)
def test_metric_extraction_and_normalization(
    text: str,
    expected_count: int,
    expected_values: list[float],
    expected_units: list[str],
    expected_quality: MetricQuality,
) -> None:
    metrics = extract_impact_metrics(text)
    assert len(metrics) == expected_count

    actual_values = [m.normalized_value for m in metrics]
    assert actual_values == expected_values

    actual_units = [m.unit for m in metrics]
    assert actual_units == expected_units

    # Verify span invariance for every extracted metric
    for m in metrics:
        start, end = m.raw_span
        assert text[start:end] == m.raw_text

    quality = classify_metric_quality(text, metrics)
    assert quality == expected_quality
