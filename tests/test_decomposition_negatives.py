"""Negative tests ensuring versions, dates, 24/7, and identifiers are not impact metrics."""

import pytest

from careercompiler.decomposition.metrics import extract_impact_metrics

NEGATIVE_CASES = [
    # Software versions
    "Developed backend using Python 3.11 and FastAPI.",
    "Database hosted on PostgreSQL 16 with replication.",
    "Upgraded core libraries to v2.0 for stability.",
    "Integrated computer vision pipeline using YOLOv8 models.",
    "Frontend authored in HTML5 and modern ES6.",
    "Compiled high performance modules under C++20 standard.",
    "Microservices running on Node.js 18 LTS runtime.",
    "Built mobile application with React Native 0.72.",
    # Dates and calendar years
    "Internship completed between May 2026 and July 2026.",
    "Certified by Anthropic in Jul 2026.",
    "Presented research at Gravitas 2026 institutional showcase.",
    "Earned top honors at AgriThon Hackathon 2025.",
    "Student in the Class of 2024 cohort.",
    # Availability
    "Provided 24/7 on-call production support for services.",
    "Ensuring 24/7 uptime across enterprise clusters.",
    # Phone numbers
    "Contact candidate at +91 8547560400 for inquiries.",
    "Call (555) 123-4567 for references.",
]


@pytest.mark.parametrize("text", NEGATIVE_CASES)
def test_negative_metric_exclusions(text: str) -> None:
    metrics = extract_impact_metrics(text)
    assert len(metrics) == 0, (
        f"Expected 0 metrics for negative case: '{text}', but got {[(m.raw_text, m.unit, m.normalized_value) for m in metrics]}"
    )
