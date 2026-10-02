"""Acceptance tests for Tier 1 JD parser: Offset Invariants & Zero-Loss Coverage."""

from careercompiler.parsing.jd_parser import parse_job_description
from careercompiler.parsing.models import SectionKind


def test_offset_invariant_simple() -> None:
    text = """Job Summary:
We are looking for a Software Engineer.

Responsibilities:
• Design and build distributed systems.
• Maintain CI/CD pipelines.

Required Qualifications:
• 3+ years experience with Python.
• Strong understanding of SQL.
"""
    doc = parse_job_description(text)
    assert doc.verify_offsets() is True
    assert doc.calculate_non_whitespace_coverage() == 1.0

    # Verify sections
    kinds = [s.kind for s in doc.sections]
    assert SectionKind.ABOUT in kinds
    assert SectionKind.RESPONSIBILITIES in kinds
    assert SectionKind.REQUIREMENTS in kinds


def test_synthetic_edge_case_no_headings() -> None:
    """Document with no headings must produce an UNCLASSIFIED section covering all text."""
    text = """First paragraph of an unstructured job posting.
Still in the first block with details.

Another block with more details and requirements without explicit headers.
"""
    doc = parse_job_description(text)
    assert doc.verify_offsets() is True
    assert doc.calculate_non_whitespace_coverage() == 1.0
    assert len(doc.sections) == 1
    assert doc.sections[0].kind == SectionKind.UNCLASSIFIED


def test_synthetic_edge_case_markdown_and_html_paste() -> None:
    """Markdown headers and HTML entity artifacts."""
    text = """# Company Overview
We build cloud systems &amp; web apps.

## Key Responsibilities
* Implement RESTful APIs using FastAPI.
* Write comprehensive test suites with Pytest.

### Preferred Qualifications
- Experience with Docker &amp; Kubernetes.
- Familiarity with CI/CD tools (GitHub Actions).
"""
    doc = parse_job_description(text)
    assert doc.verify_offsets() is True
    assert doc.calculate_non_whitespace_coverage() == 1.0

    kinds = [s.kind for s in doc.sections]
    assert SectionKind.ABOUT in kinds
    assert SectionKind.RESPONSIBILITIES in kinds
    assert SectionKind.PREFERRED in kinds


def test_synthetic_edge_case_all_caps_headings() -> None:
    text = """WHAT YOU WILL DO
• Develop software features in Python.
• Collaborate with cross-functional teams.

REQUIREMENTS
• Bachelor's degree in Computer Science.
• Proficient in data structures and algorithms.
"""
    doc = parse_job_description(text)
    assert doc.verify_offsets() is True
    assert doc.calculate_non_whitespace_coverage() == 1.0

    kinds = [s.kind for s in doc.sections]
    assert SectionKind.RESPONSIBILITIES in kinds
    assert SectionKind.REQUIREMENTS in kinds


def test_synthetic_edge_case_nested_and_numbered_bullets() -> None:
    text = """Responsibilities:
1. First major responsibility covering architecture.
   Continuation line for first item.
2. Second major responsibility covering deployment.

Must Have:
(a) Strong proficiency in Python or Go.
(b) Experience with PostgreSQL databases.
"""
    doc = parse_job_description(text)
    assert doc.verify_offsets() is True
    assert doc.calculate_non_whitespace_coverage() == 1.0
