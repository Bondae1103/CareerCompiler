"""Integration tests for Career Compiler FastAPI REST API."""

import pytest
from starlette.testclient import TestClient

from careercompiler.api.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_api_health_check(client: TestClient) -> None:
    """Health check endpoint returns status ok and version."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_api_get_profile(client: TestClient) -> None:
    """Profile endpoint returns the active candidate master profile."""
    resp = client.get("/api/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert "contact" in data
    assert "experiences" in data
    assert "projects" in data
    assert data["contact"]["name"] == "Anoop Nair"


def test_api_parse_jd(client: TestClient) -> None:
    """JD parse endpoint extracts hard requirements and keywords."""
    jd_payload = {"text": "Seeking a Backend Engineer proficient in Python, Docker, and AWS."}
    resp = client.post("/api/jds/parse", json=jd_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["hard_requirements"]) >= 2
    cids = [r["canonical_id"] for r in data["hard_requirements"]]
    assert "python" in cids
    assert "docker" in cids


def test_api_tailor_and_revert_workflow(client: TestClient) -> None:
    """End-to-end API test: tailor resume, verify diff, and test 1-click slot revert."""
    tailor_payload = {
        "jd_text": "We are looking for a Senior Developer with Python, Docker, and FastAPI experience.",
        "capacity_lines": 30,
    }
    resp = client.post("/api/tailor", json=tailor_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "selection" in data
    assert "diff" in data
    assert data["total_lines"] <= 30
    assert len(data["markdown_report"]) > 50

    # Test Revert
    diff = data["diff"]
    swapped_slots = [bd for bd in diff["bullet_diffs"] if bd["action"] == "SWAPPED"]
    if swapped_slots:
        target_slot = swapped_slots[0]["slot_id"]
        revert_payload = {
            "slot_id": target_slot,
            "reason": "Test rollback",
        }
        rev_resp = client.post("/api/revert", json=revert_payload)
        assert rev_resp.status_code == 200
        rev_data = rev_resp.json()
        assert rev_data["status"] == "reverted"
        assert len(rev_data["revert_records"]) == 1
        assert rev_data["revert_records"][0]["slot_id"] == target_slot


def test_api_tex_and_pdf_download(client: TestClient) -> None:
    """Verify LaTeX source and compiled PDF download endpoints."""
    # Tailor first
    tailor_payload = {
        "jd_text": "We need an engineer experienced in Python, Docker, and FastAPI.",
        "capacity_lines": 30,
    }
    client.post("/api/tailor", json=tailor_payload)

    tex_resp = client.get("/api/tex")
    assert tex_resp.status_code == 200
    assert "\\documentclass" in tex_resp.text

    pdf_resp = client.get("/api/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000


def test_api_serves_frontend_root(client: TestClient) -> None:
    """Verify that root / serves the built frontend dashboard."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "html" in resp.headers.get("content-type", "")

