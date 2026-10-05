"""Tests for extraction domain models and validation invariants."""

import pytest
from pydantic import ValidationError

from careercompiler.extraction.models import (
    ExtractedJD,
    ExtractedRequirement,
    RequirementCategory,
    ScaleIndicator,
)


def test_valid_extracted_requirement() -> None:
    req = ExtractedRequirement(
        id="req_1",
        canonical_id="python",
        surface_form="Python",
        evidence_span=(10, 25),
        evidence_text="Required Python",
        category=RequirementCategory.MUST_HAVE,
        required_years=3.0,
        importance=0.9,
        cue_phrase="Required",
        unmapped=False,
    )
    assert req.id == "req_1"
    assert req.canonical_id == "python"
    assert req.required_years == 3.0
    assert req.importance == 0.9


def test_requirement_span_invariants() -> None:
    # Negative start
    with pytest.raises(ValidationError):
        ExtractedRequirement(
            id="req_1",
            surface_form="Python",
            evidence_span=(-1, 10),
            evidence_text="test text",
            category=RequirementCategory.MUST_HAVE,
        )

    # End <= start
    with pytest.raises(ValidationError):
        ExtractedRequirement(
            id="req_1",
            surface_form="Python",
            evidence_span=(10, 10),
            evidence_text="",
            category=RequirementCategory.MUST_HAVE,
        )

    # evidence_text length does not match span
    with pytest.raises(ValidationError) as exc:
        ExtractedRequirement(
            id="req_1",
            surface_form="Python",
            evidence_span=(10, 20),
            evidence_text="too short",  # length 9 != 10
            category=RequirementCategory.MUST_HAVE,
        )
    assert "length" in str(exc.value)


def test_valid_scale_indicator() -> None:
    ind = ScaleIndicator(
        id="scale_1",
        metric="throughput",
        value="50k ops/sec",
        evidence_span=(5, 16),
        evidence_text="50k ops/sec",
    )
    assert ind.id == "scale_1"
    assert ind.value == "50k ops/sec"


def test_scale_indicator_span_invariants() -> None:
    with pytest.raises(ValidationError):
        ScaleIndicator(
            id="scale_1",
            metric="throughput",
            value="50k ops/sec",
            evidence_span=(10, 5),  # end < start
            evidence_text="test",
        )


def test_extracted_jd_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        ExtractedJD(  # type: ignore[call-arg]
            role_title="Backend Engineer",
            extractor_name="TestExtractor",
            cache_key="abc",
            unexpected_field="disallowed",
        )
