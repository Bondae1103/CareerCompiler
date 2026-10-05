"""Tests for LLMExtractor post-validation, retries, and fallback behavior."""

from typing import Any

from careercompiler.extraction.llm_extractor import LLMExtractor
from careercompiler.extraction.models import RequirementCategory


class MockSuccessLLMClient:
    provider = "mock_provider"
    model = "mock_model"
    version = "1.0.0"

    def __init__(self, jd_text: str) -> None:
        self.jd_text = jd_text

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        # Return a response with valid spans matching the prompt's JD
        python_idx = self.jd_text.find("Python")
        return {
            "role_title": "Backend Lead",
            "role_title_span": [0, 10],
            "hard_requirements": [
                {
                    "id": "mock_req_1",
                    "canonical_id": "python",
                    "surface_form": "Python",
                    "evidence_span": [python_idx, python_idx + 6],
                    "category": "must_have",
                    "required_years": 5.0,
                    "importance": 0.95,
                    "cue_phrase": "required",
                }
            ],
            "preferred_qualifications": [],
            "scale_indicators": [],
        }


class MockFailingLLMClient:
    provider = "mock_failing"
    model = "mock_model"
    version = "1.0.0"

    def __init__(self) -> None:
        self.call_count = 0

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        self.call_count += 1
        raise RuntimeError("LLM API service unavailable (503)")


def test_llm_extractor_disabled_by_default() -> None:
    jd = "Backend Developer. Required skills: Python and Docker."
    extractor = LLMExtractor(enabled=False)

    extracted = extractor.extract(jd)
    assert extracted.extractor_name == "LocalRuleExtractor"
    cids = {r.canonical_id for r in extracted.hard_requirements}
    assert "python" in cids
    assert "docker" in cids


def test_llm_extractor_success_with_post_validation() -> None:
    jd = "Backend Developer. Required skills: 5 years of Python."
    client = MockSuccessLLMClient(jd)
    extractor = LLMExtractor(llm_client=client, enabled=True)

    extracted = extractor.extract(jd)
    assert "LLMExtractor" in extracted.extractor_name
    assert extracted.role_title == "Backend Lead"
    assert len(extracted.hard_requirements) == 1
    req = extracted.hard_requirements[0]
    assert req.canonical_id == "python"
    assert req.surface_form == "Python"
    assert req.category == RequirementCategory.MUST_HAVE
    assert jd[req.evidence_span[0] : req.evidence_span[1]] == "Python"


def test_llm_extractor_fallback_on_error() -> None:
    jd = "Backend Developer. Required skills: Python and Docker."
    client = MockFailingLLMClient()
    extractor = LLMExtractor(llm_client=client, enabled=True, max_retries=1)

    extracted = extractor.extract(jd)
    # Failed client exhausted retries -> gracefully fell back to LocalRuleExtractor
    assert client.call_count == 2
    assert extracted.extractor_name == "LocalRuleExtractor"
    cids = {r.canonical_id for r in extracted.hard_requirements}
    assert "python" in cids
    assert "docker" in cids
