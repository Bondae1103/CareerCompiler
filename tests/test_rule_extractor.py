"""Tests for LocalRuleExtractor offline extraction and evidence invariant enforcement."""

from careercompiler.extraction.models import RequirementCategory
from careercompiler.extraction.rule_extractor import LocalRuleExtractor

SAMPLE_JD = """Job Title: Senior Backend Engineer

About Us:
We build high throughput distributed platforms serving 10M+ users globally.

Required Qualifications:
• 3+ years of experience with Python and FastAPI in production.
• Strong experience with PostgreSQL database schema design and optimization.
• Must have hands-on knowledge of Docker and Kubernetes container orchestration.
• Bachelor's degree in Computer Science or related field.

Preferred Qualifications:
• Experience with Redis caching and Celery task queues is a plus.
• Familiarity with AWS Lambda and Amazon S3.
• Knowledge of Golang and microservices architecture.
"""


def test_rule_extractor_standalone_offline() -> None:
    extractor = LocalRuleExtractor()
    extracted = extractor.extract(SAMPLE_JD)

    # 1. Role title
    assert extracted.role_title == "Senior Backend Engineer"
    assert extracted.role_title_span is not None
    assert SAMPLE_JD[extracted.role_title_span[0] : extracted.role_title_span[1]] == "Senior Backend Engineer"

    # 2. Hard requirements
    hard_cids = {r.canonical_id for r in extracted.hard_requirements if r.canonical_id}
    assert "python" in hard_cids
    assert "fastapi" in hard_cids
    assert "postgresql" in hard_cids
    assert "docker" in hard_cids
    assert "kubernetes" in hard_cids

    for r in extracted.hard_requirements:
        assert r.category == RequirementCategory.MUST_HAVE
        # Evidence Invariant
        start, end = r.evidence_span
        assert SAMPLE_JD[start:end] == r.evidence_text
        assert r.surface_form.lower() in r.evidence_text.lower()

    # Python should have required_years == 3.0
    python_req = next(r for r in extracted.hard_requirements if r.canonical_id == "python")
    assert python_req.required_years == 3.0
    assert "3" in python_req.evidence_text

    # 3. Preferred qualifications
    pref_cids = {r.canonical_id for r in extracted.preferred_qualifications if r.canonical_id}
    assert "redis" in pref_cids
    assert "celery" in pref_cids
    assert "aws-lambda" in pref_cids
    assert "aws-s3" in pref_cids
    assert "golang" in pref_cids
    assert "microservices" in pref_cids

    for r in extracted.preferred_qualifications:
        assert r.category == RequirementCategory.NICE_TO_HAVE
        start, end = r.evidence_span
        assert SAMPLE_JD[start:end] == r.evidence_text
        assert r.surface_form.lower() in r.evidence_text.lower()

    # 4. Scale indicators
    assert len(extracted.scale_indicators) >= 1
    users_indicator = next(
        (ind for ind in extracted.scale_indicators if "10M+" in ind.value), None
    )
    assert users_indicator is not None
    assert users_indicator.metric == "users_or_records"
    start, end = users_indicator.evidence_span
    assert SAMPLE_JD[start:end] == users_indicator.evidence_text

    # 5. Dropped items count on clean JD should be 0
    assert extracted.dropped_items_count == 0


def test_rule_extractor_empty_jd() -> None:
    extractor = LocalRuleExtractor()
    extracted = extractor.extract("")
    assert extracted.hard_requirements == []
    assert extracted.preferred_qualifications == []
    assert extracted.scale_indicators == []
    assert extracted.dropped_items_count == 0
