"""Tests for LaTeX compilation and PDF verification."""

from pathlib import Path

from careercompiler.layout.template import ResumeTemplate
from careercompiler.layout.verifier import LayoutVerifier


def test_verifier_canonical_resume_single_page_success() -> None:
    """Canonical template compiles to exactly 1 page with embedded fonts and present bullets."""
    tex_path = Path("templates/resume.tex")
    raw_tex = tex_path.read_text(encoding="utf-8")
    tpl = ResumeTemplate(raw_tex)

    # Use default contents of slots
    expected_sample_bullets = [
        "Architected modular end-to-end and REST API test frameworks using Playwright and OOP design patterns, achieving 100% test coverage across enterprise cloud services and microservices.",
        "Automated common ETL tasks and data utilities in high-performance POSIX Linux, reducing manual compute overhead and batch data transformation latency by 60%.",
    ]

    slot_texts = {
        "exp_1_slot_1": expected_sample_bullets[0],
        "exp_1_slot_2": "Engineered Agentic AI workflows and structured prompt optimization pipelines within CI/CD, automating regression test synthesis to cut feedback cycle latency by 35%.",
        "exp_1_slot_3": "Collaborated in cross-functional Agile teams (Scrum/Kanban) via Jira and Confluence, authoring SOLID-compliant test harnesses to standardize enterprise cloud quality.",
        "exp_2_slot_1": expected_sample_bullets[1],
        "exp_2_slot_2": "Engineered fault-tolerant Linux Bash pipelines and batch processing scripts, optimizing disk I/O, process concurrency, and memory utilization for molecular research datasets.",
        "proj_1_slot_1": "Architected an asynchronous, distributed backend microservice with FastAPI, Celery, and Redis as a message broker for concurrent ingestion and structural parsing of documents.",
        "proj_1_slot_2": "Engineered a hybrid retrieval engine combining PubMedBERT embeddings with BM25 indexing in Qdrant, attaining 100% Recall@5 and 0% hallucination rate on 27 benchmarks.",
        "proj_1_slot_3": "Implemented low-latency streaming via Server-Sent Events (SSE) with post-hoc citation verification; containerized with Docker Compose and authored a 44-test Pytest suite (100% pass rate).",
        "proj_2_slot_1": "Engineered a real-time simulation engine in TypeScript modeling the 158K-neuron Drosophila connectome, implementing Leaky Integrate-and-Fire (LIF) dynamics at 60fps on HTML5 Canvas.",
        "proj_2_slot_2": "Built an offline Python pipeline normalizing 1,100+ synaptic inputs; authored an automated Vitest suite verifying 1,000 escape trajectories with 2D boundary collision physics.",
        "proj_3_slot_1": "Architected a multi-task Graph Convolutional Network (GCN) in PyTorch Geometric across 13,753 clinical isolates to jointly predict resistance phenotypes across 9 anti-TB drugs.",
        "proj_3_slot_2": "Engineered Jaccard-weighted phylogenetic mutation graphs across 157 loci; conducted ablation studies and was selected for institutional showcase at Gravitas 2026.",
    }

    rendered = tpl.render(slot_texts)

    verifier = LayoutVerifier(timeout=60)
    result = verifier.compile_and_verify(rendered, expected_bullet_texts=expected_sample_bullets)

    assert result.success is True
    assert result.page_count == 1
    assert result.fonts_embedded is True
    assert result.all_bullets_present is True
    assert result.missing_bullets == []
    assert result.is_ats_extractable is True


def test_verifier_detects_page_overflow() -> None:
    """When a resume overflows onto 2 pages, the verifier fails and reports page count = 2."""
    tex_path = Path("templates/resume.tex")
    raw_tex = tex_path.read_text(encoding="utf-8")
    tpl = ResumeTemplate(raw_tex)
    slot_texts = dict.fromkeys(tpl.slots, "Default accomplishment statement.")
    # Enlarge 8 slots to push layout past page 1 capacity
    for s in list(tpl.slots.keys())[:8]:
        slot_texts[s] = (
            "Extended multi-line engineering achievement detailing distributed database "
            "optimizations, consensus log replication, network topology telemetry, "
            "and architectural benchmarks across high-throughput clusters. " * 3
        )
    overflow_tex = tpl.render(slot_texts)

    verifier = LayoutVerifier(timeout=60)
    result = verifier.compile_and_verify(overflow_tex)

    assert result.success is False
    assert result.page_count == 2
    assert any("Page budget violation: PDF has 2 pages" in err for err in result.errors)


def test_verifier_detects_missing_expected_bullet() -> None:
    """Verifier detects when an expected bullet was omitted from the rendered PDF."""
    tex_path = Path("templates/resume.tex")
    raw_tex = tex_path.read_text(encoding="utf-8")
    tpl = ResumeTemplate(raw_tex)

    # Omit exp_1_slot_1
    slot_texts: dict[str, str | None] = {s: f"Bullet text for {s}" for s in tpl.slots if s != "exp_1_slot_1"}
    slot_texts["exp_1_slot_1"] = None

    rendered = tpl.render(slot_texts)

    missing_expected = "Crucial bullet that was omitted from the selection."
    verifier = LayoutVerifier(timeout=60)
    result = verifier.compile_and_verify(rendered, expected_bullet_texts=[missing_expected])

    assert result.success is False
    assert result.all_bullets_present is False
    assert missing_expected in result.missing_bullets
