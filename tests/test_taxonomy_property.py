"""Property-based tests for BoundarySafeMatcher invariants."""

import hypothesis.strategies as st
from hypothesis import given, settings

from careercompiler.taxonomy.normalizer import get_default_normalizer

normalizer = get_default_normalizer()
catalog = normalizer.catalog

# Sample representative tokens to construct realistic and adversarial inputs
SAMPLE_TOKENS = [
    "Python", "python", "py", "Java", "JavaScript", "C++", "C#", "C", "Go", "go",
    "Rust", "rust", "R", "r", "R&D", ".NET", "Node.js", "node", "Next.js", "React",
    "React Native", "Docker", "Docker Compose", "Kubernetes", "K8s", "Postgres",
    "PostgreSQL", "psql", "FastAPI", "Redis", "Celery", "REST", "RESTful", "CI/CD",
    "and", "with", "or", "in", "developer", "engineer", "let's", "to", "the", "system",
    "architecture", "algorithms", "microservices", "100%", "v1.0", "API", "team",
]


@st.composite
def generated_technical_text(draw: st.DrawFn) -> str:
    # Pick a sequence of tokens interspersed with random whitespace, delimiters, or punctuation
    tokens = draw(st.lists(st.sampled_from(SAMPLE_TOKENS), min_size=1, max_size=15))
    delimiters = draw(st.lists(st.sampled_from([" ", ", ", "/", " / ", "; ", ". ", " - ", " (", ") "]), min_size=len(tokens), max_size=len(tokens)+1))
    pieces: list[str] = []
    for i, tok in enumerate(tokens):
        pieces.append(tok)
        if i < len(delimiters):
            pieces.append(delimiters[i])
    return "".join(pieces)


@settings(max_examples=100, deadline=None)
@given(text=generated_technical_text())
def test_matcher_invariants(text: str) -> None:
    matches = normalizer.normalize(text)

    # Invariant 1: Source slice byte-identical to surface_form
    for m in matches:
        assert text[m.start:m.end] == m.surface_form, (
            f"Offset mismatch! text[{m.start}:{m.end}]='{text[m.start:m.end]}' != surface_form='{m.surface_form}'"
        )

    # Invariant 2: Strictly non-overlapping and sorted by start
    for i in range(len(matches) - 1):
        m1 = matches[i]
        m2 = matches[i + 1]
        assert m1.end <= m2.start, (
            f"Overlapping spans detected! Match {m1} overlaps with {m2} in text '{text}'"
        )

    # Invariant 3: All canonical IDs exist in taxonomy catalog
    for m in matches:
        entity = catalog.get_by_id(m.canonical_id)
        assert entity is not None, f"Canonical ID '{m.canonical_id}' not found in taxonomy catalog"

    # Invariant 4: Exact determinism across repeat calls
    repeat_matches = normalizer.normalize(text)
    assert matches == repeat_matches


@settings(max_examples=50, deadline=None)
@given(text=st.text(min_size=0, max_size=200))
def test_matcher_arbitrary_string_safety(text: str) -> None:
    """Ensure matcher never crashes on arbitrary Unicode, symbols, or empty strings."""
    matches = normalizer.normalize(text)
    for m in matches:
        assert text[m.start:m.end] == m.surface_form
        assert m.end > m.start
        assert catalog.get_by_id(m.canonical_id) is not None
