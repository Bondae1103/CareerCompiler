"""Spike S2: 50-Bullet Line Measurement Harness.

Compares:
1. TeX-side measurement via \\prevgraf probe (Ground Truth)
2. FontMetricSimulator (greedy character-width simulation)
3. HeuristicLineEstimator (conservative character threshold)
"""

import json
from pathlib import Path
from typing import Any

from careercompiler.layout.estimator import (
    FontMetricSimulator,
    HeuristicLineEstimator,
    TeXPrevgrafEstimator,
)

# 52 varied test bullets
TEST_BULLETS: list[tuple[str, str]] = [
    # 1-11: Real bullets from Anoop Nair's resume.tex
    ("real_01", r"Architected modular end-to-end and REST API test frameworks using \textbf{Playwright} and \textbf{OOP design patterns}, achieving \textbf{100\% test coverage} across enterprise cloud services and microservices."),
    ("real_02", r"Engineered \textbf{Agentic AI} workflows and structured \textbf{prompt optimization} pipelines within CI/CD, automating regression test synthesis to cut feedback cycle latency by \textbf{35\%}."),
    ("real_03", r"Collaborated in cross-functional \textbf{Agile teams (Scrum/Kanban) via Jira and Confluence}, authoring \textbf{SOLID}-compliant test harnesses to standardize enterprise cloud quality."),
    ("real_04", r"Automated common ETL tasks and data utilities in high-performance \textbf{POSIX Linux}, reducing manual compute overhead and batch data transformation latency by \textbf{60\%}."),
    ("real_05", r"Engineered fault-tolerant \textbf{Linux Bash pipelines} and batch processing scripts, optimizing disk I/O, process concurrency, and memory utilization for molecular research datasets."),
    ("real_06", r"Architected an asynchronous, distributed backend microservice with \textbf{FastAPI}, \textbf{Celery}, and \textbf{Redis} as a message broker for concurrent ingestion and structural parsing of documents."),
    ("real_07", r"Engineered a hybrid retrieval engine combining \textbf{PubMedBERT} embeddings with BM25 indexing in \textbf{Qdrant}, attaining \textbf{100\% Recall@5} and \textbf{0\% hallucination rate} on 27 benchmarks."),
    ("real_08", r"Implemented low-latency streaming via \textbf{Server-Sent Events (SSE)} with post-hoc citation verification; containerized with \textbf{Docker Compose} and authored a \textbf{44-test Pytest suite (100\% pass rate)}."),
    ("real_09", r"Engineered a real-time simulation engine in \textbf{TypeScript} modeling the 158K-neuron Drosophila connectome, implementing Leaky Integrate-and-Fire (\textbf{LIF}) dynamics at 60fps on HTML5 Canvas."),
    ("real_10", r"Built an offline \textbf{Python pipeline} normalizing 1,100+ synaptic inputs; authored an automated \textbf{Vitest suite verifying 1,000 escape trajectories} with 2D boundary collision physics."),
    ("real_11", r"Architected a multi-task \textbf{Graph Convolutional Network (GCN)} in \textbf{PyTorch Geometric} across 13,753 \textbf{clinical isolates} to jointly predict resistance phenotypes across 9 anti-TB drugs."),

    # 12-20: Short bullets (Expected 1 line)
    ("short_01", r"Maintained internal developer documentation and onboarding guides across engineering teams."),
    ("short_02", r"Configured automated GitHub Actions workflows for continuous integration and unit testing."),
    ("short_03", r"Awarded Certificate of Merit and cash prize for achieving a \textbf{9.42 GPA} in Semester 1."),
    ("short_04", r"Certified in AI Fluency Framework \& Foundations by \textbf{Anthropic} (Issued Jul 2026)."),
    ("short_05", r"Implemented secure JWT authentication and role-based access control for admin dashboard."),
    ("short_06", r"Designed relational schemas and indexed queries in PostgreSQL for sub-10ms lookup times."),
    ("short_07", r"Authored 50+ unit tests with Pytest, achieving 98\% branch coverage on billing service."),
    ("short_08", r"Refactored legacy monolith into three modular Go microservices communicating via gRPC."),
    ("short_09", r"Deployed containerized services to AWS ECS with auto-scaling policies based on CPU usage."),

    # 21-30: Boundary bullets (Near 1-line to 2-line threshold, ~95-125 chars)
    ("boundary_01", r"Engineered asynchronous worker tasks with Celery and Redis to process background video transcoding jobs reliably."),
    ("boundary_02", r"Optimized MySQL database queries and added composite indexes, reducing p95 query latency from 240ms to 45ms."),
    ("boundary_03", r"Developed responsive frontend components in React and Tailwind CSS, improving Lighthouse accessibility score to 100."),
    ("boundary_04", r"Streamlined Docker images using multi-stage builds, slashing image size by 75\% and accelerating deploy times."),
    ("boundary_05", r"Implemented rate limiting and DDoS mitigation using Redis token-bucket algorithms on API gateway endpoints."),
    ("boundary_06", r"Collaborated with product managers to define technical requirements and sprint backlogs in Jira and Linear."),
    ("boundary_07", r"Conducted automated vulnerability scans using Snyk and Trivy within CI/CD pipelines to prevent CVE regressions."),
    ("boundary_08", r"Integrated Prometheus metrics and Grafana dashboards for real-time observability of production microservices."),
    ("boundary_09", r"Automated infrastructure provisioning using Terraform scripts, enforcing strict least-privilege IAM policies."),
    ("boundary_10", r"Designed RESTful API contracts following OpenAPI 3.0 standards, enabling seamless cross-team client SDK generation."),

    # 31-40: Medium-Long bullets (Expected 2 lines, ~150-230 chars)
    ("med_01", r"Architected a fault-tolerant event sourcing pipeline with Apache Kafka and Flink, streaming 50,000 transaction events per second with zero data loss during simulated broker failovers."),
    ("med_02", r"Engineered distributed consensus protocols based on Raft in Go, achieving 45k ops/sec throughput with sub-5ms p99 write latency across a five-node geo-distributed cluster."),
    ("med_03", r"Spearheaded cloud migration of on-premises workloads to AWS, orchestrating Terraform modules, Kubernetes clusters, and automated blue-green deployments with zero downtime."),
    ("med_04", r"Constructed graph neural network pipelines in PyTorch Geometric to analyze biological interaction networks, identifying 12 novel drug target candidates with 91\% cross-validated accuracy."),
    ("med_05", r"Implemented automated end-to-end integration test suites in TypeScript with Playwright, running nightly parallel regression runs across Chromium, Firefox, and WebKit browsers."),
    ("med_06", r"Built real-time collaborative document editing backend using Operational Transformation algorithms and WebSockets, supporting up to 200 concurrent editors per document room."),
    ("med_07", r"Led team of four engineers to deliver customer analytics platform ahead of schedule, conducting daily standups, architectural design reviews, and pairing sessions."),
    ("med_08", r"Designed and benchmarked custom vector similarity search algorithms in C++, achieving 4x throughput improvement over standard HNSW baselines on 1M 128-dimensional vectors."),
    ("med_09", r"Engineered automated bioinformatics parsing scripts in Python to process multi-gigabyte FASTQ and BAM sequencing files, decreasing compute hours by 40\% across HPC nodes."),
    ("med_10", r"Authored comprehensive architectural decision records (ADRs) and API documentation, reducing new engineer ramp-up time from three weeks to four business days."),

    # 41-48: Long bullets (Expected 3 lines, ~260-350 chars)
    ("long_01", r"Architected and deployed a multi-tenant enterprise SaaS backend using FastAPI, PostgreSQL, and Redis, serving 150,000 monthly active users while maintaining 99.99\% uptime SLA; implemented distributed tracing with OpenTelemetry and Jaeger to isolate latency bottlenecks across 14 decoupled microservices."),
    ("long_02", r"Engineered an automated regression testing framework utilizing Playwright, Docker, and GitHub Actions, orchestrating 1,200+ parallel test executions across multiple staging environments; reduced developer deployment feedback loop from 45 minutes to under 8 minutes while preventing 23 critical release regressions."),
    ("long_03", r"Developed a high-throughput genomic variant calling pipeline combining BWA-MEM alignment and GATK variant discovery algorithms; optimized compute resource allocation on Slurm cluster to process 500 whole-genome sequencing samples simultaneously, reducing aggregate pipeline turnaround time by 65\%."),
    ("long_04", r"Designed and implemented distributed caching architecture using Redis Cluster and consistent hashing algorithms, offloading 85\% of read queries from primary PostgreSQL instances and preventing catastrophic cascade failures during peak seasonal promotional traffic spikes."),
    ("long_05", r"Led cross-functional migration from legacy monolithic Django architecture to modern microservices in Go and Python, defining gRPC protocol buffer contracts, decomposing relational schemas into domain-driven data stores, and training 15 developers on distributed systems best practices."),
    ("long_06", r"Implemented privacy-preserving federated learning platform using PyTorch and differential privacy mechanisms, enabling collaborative medical imaging model training across three partner hospitals without centralized patient health information exposure."),
    ("long_07", r"Engineered custom memory allocator in C for high-frequency trading simulation engine, eliminating OS heap allocation lock contention and achieving deterministic sub-microsecond tick processing latency under simulated market burst conditions."),
    ("long_08", r"Built distributed web crawler and parsing engine in Python and asyncio, ingesting and deduplicating 20 million technical forum posts daily; authored custom tokenization pipelines to feed fine-tuned domain-specific language models."),

    # 49-52: Edge case bullets (URLs, long unbroken tokens, heavy LaTeX escapes)
    ("edge_01", r"Maintained open-source documentation at \href{https://github.com/Bondae1103/Paleo-RAG}{https://github.com/Bondae1103/Paleo-RAG} with 100\% test coverage and automated badge status."),
    ("edge_02", r"Tested extreme tokenization: \texttt{org.springframework.boot.autoconfigure.EnableAutoConfiguration} and \texttt{DistributedTransactionCoordinatorManagerService}."),
    ("edge_03", r"Handled complex symbols: 100\% test coverage, \$5,000 cost savings, \#1 rank in hackathon, \& 50\% reduction in I/O wait times with \_custom\_allocator."),
    ("edge_04", r"Integrated \href{https://portfolio-website-anoop.vercel.app}{portfolio} and \href{https://github.com/Bondae1103}{GitHub} repositories with continuous automated deployment webhooks."),
]


def run_harness() -> dict[str, Any]:
    work_dir = Path("eval_spike_s2_sandbox")
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"Running Spike S2 harness on {len(TEST_BULLETS)} varied bullets...")

    # 1. Ground truth via TeX prevgraf probe
    tex_measurer = TeXPrevgrafEstimator(timeout=30)
    ground_truth = tex_measurer.measure_batch(TEST_BULLETS, work_dir)

    font_sim = FontMetricSimulator()
    heuristic = HeuristicLineEstimator()

    records = []

    font_exact = 0
    font_over = 0
    font_under = 0

    heur_exact = 0
    heur_over = 0
    heur_under = 0

    for bid, text in TEST_BULLETS:
        gt_lines = ground_truth.get(bid)
        if gt_lines is None:
            raise RuntimeError(f"Missing TeX ground truth for bullet {bid}")

        sim_lines = font_sim.estimate(text)
        heur_lines = heuristic.estimate(text)

        # Font sim error direction
        if sim_lines == gt_lines:
            font_exact += 1
        elif sim_lines > gt_lines:
            font_over += 1
        else:
            font_under += 1

        # Heuristic error direction
        if heur_lines == gt_lines:
            heur_exact += 1
        elif heur_lines > gt_lines:
            heur_over += 1
        else:
            heur_under += 1

        records.append({
            "id": bid,
            "text": text[:60] + "...",
            "char_count": len(text),
            "ground_truth": gt_lines,
            "font_simulator": sim_lines,
            "heuristic": heur_lines,
        })

    total = len(TEST_BULLETS)

    summary: dict[str, Any] = {
        "total_bullets": total,
        "font_simulator": {
            "exact_matches": font_exact,
            "agreement_rate": font_exact / total,
            "over_estimates": font_over,
            "under_estimates": font_under,
        },
        "heuristic": {
            "exact_matches": heur_exact,
            "agreement_rate": heur_exact / total,
            "over_estimates": heur_over,
            "under_estimates": heur_under,
        },
        "records": records,
    }

    # Clean up sandbox
    for f in work_dir.glob("*"):
        try:
            f.unlink()
        except Exception:
            pass
    try:
        work_dir.rmdir()
    except Exception:
        pass

    return summary


if __name__ == "__main__":
    results = run_harness()
    print("\n=== SPIKE S2 RESULTS SUMMARY ===")
    print(f"Total Bullets Tested: {results['total_bullets']}")

    fs: dict[str, Any] = results["font_simulator"]
    print("\nFontMetricSimulator:")
    print(f"  Exact Agreement: {fs['exact_matches']}/{results['total_bullets']} ({fs['agreement_rate']*100:.1f}%)")
    print(f"  Over-estimates:  {fs['over_estimates']}")
    print(f"  Under-estimates: {fs['under_estimates']}")

    he: dict[str, Any] = results["heuristic"]
    print("\nHeuristicLineEstimator (Conservative):")
    print(f"  Exact Agreement: {he['exact_matches']}/{results['total_bullets']} ({he['agreement_rate']*100:.1f}%)")
    print(f"  Over-estimates:  {he['over_estimates']}")
    print(f"  Under-estimates: {he['under_estimates']}")

    # Save detailed JSON report
    Path("eval").mkdir(parents=True, exist_ok=True)
    with open("eval/spike_s2_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("\nSaved detailed results to eval/spike_s2_results.json")
