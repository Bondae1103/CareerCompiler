"""Property-based tests for impact metric extraction invariants using Hypothesis."""

import hypothesis.strategies as st
from hypothesis import given, settings

from careercompiler.decomposition.decomposer import decompose_bullet
from careercompiler.decomposition.metrics import extract_impact_metrics

METRIC_TEMPLATES = [
    "achieved {val}% improvement",
    "reduced latency by {val}ms",
    "handled {val}k ops/sec",
    "processed {val}M requests",
    "speedup of {val}x",
    "cost reduced by ${val}k",
    "serving {val} users",
    "trained across {val} isolates",
]


@st.composite
def generated_accomplishment_text(draw: st.DrawFn) -> str:
    template = draw(st.sampled_from(METRIC_TEMPLATES))
    val = draw(st.integers(min_value=1, max_value=999))
    filler = draw(st.sampled_from([
        "Architected scalable backend with FastAPI and Redis",
        "Optimized Docker container workloads on Kubernetes",
        "Engineered deep learning pipelines in PyTorch",
        "Streamlined automated testing in CI/CD with Pytest",
    ]))
    return f"{filler} and {template.format(val=val)}."


@settings(max_examples=100, deadline=None)
@given(text=generated_accomplishment_text())
def test_metric_property_invariants(text: str) -> None:
    metrics = extract_impact_metrics(text)

    for m in metrics:
        # 1. Evidence Invariant
        start, end = m.raw_span
        assert text[start:end] == m.raw_text

        # 2. No number in output absent from source text
        # Check that characters from raw_text actually exist in source text
        assert m.raw_text in text

    # 3. Non-overlapping spans
    for i in range(len(metrics) - 1):
        assert metrics[i].raw_span[1] <= metrics[i + 1].raw_span[0]


@settings(max_examples=50, deadline=None)
@given(text=st.text(min_size=0, max_size=200))
def test_decomposer_never_crashes_on_arbitrary_text(text: str) -> None:
    decomp = decompose_bullet(text)
    assert decomp is not None
    assert decomp.raw_text == text.strip()
    for m in decomp.impact_metrics:
        assert m.raw_text in text
        start, end = m.raw_span
        assert text.strip()[start:end] == m.raw_text
