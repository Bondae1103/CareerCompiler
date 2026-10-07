"""Authoritative canonical master profile matching templates/resume.tex slots and entities."""

from careercompiler.models.profile import (
    BulletSlot,
    BulletVariant,
    ContactInfo,
    Education,
    Experience,
    Profile,
    Project,
    SkillGroup,
)


def build_canonical_profile() -> Profile:
    """Build the author's complete Master Profile Bank aligned with templates/resume.tex."""
    contact = ContactInfo(
        name="Anoop Nair",
        phone="+91 8547560400",
        email="anoop.nair.1103@gmail.com",
        linkedin_url="https://www.linkedin.com/in/anoop-nair-4a180928a",
        github_url="https://github.com/Bondae1103",
        portfolio_url="https://portfolio-website-anoop.vercel.app",
    )

    education = [
        Education(
            id="edu_vit",
            institution="Vellore Institute of Technology",
            location="Vellore, Tamil Nadu",
            degree="Bachelor of Technology (B.Tech), Computer Science Engineering (Bioinformatics)",
            dates="Sep 2023 -- Present",
            details="CGPA: 8.82",
        ),
        Education(
            id="edu_strs",
            institution="St. Thomas Residential School",
            location="Thiruvananthapuram, Kerala",
            degree="Class XII: 92% | Class X: 91%",
            dates="Graduated Mar 2022",
            details="Indian Certificate of Secondary Education (ICSE/ISC)",
        ),
    ]

    exp_1 = Experience(
        id="exp_1",
        company="Thermo Fisher Scientific",
        location="Bengaluru, Karnataka",
        title="Software Developer Intern",
        start_date="May 2026",
        end_date="July 2026",
        min_bullets=1,
        max_bullets=3,
        slots=[
            BulletSlot(
                id="exp_1_slot_1",
                name="Test Automation Architecture",
                mandatory=True,
                variants=[
                    BulletVariant(
                        id="exp_1_slot_1_v1",
                        text="Architected modular end-to-end and REST API test frameworks using Playwright and OOP design patterns, achieving 100% test coverage across enterprise cloud services and microservices.",
                        angle="quality_architecture",
                        is_default=True,
                        canonical_tags=["playwright", "oop", "rest-api", "microservices"],
                    ),
                    BulletVariant(
                        id="exp_1_slot_1_v2",
                        text="Engineered comprehensive Playwright testing frameworks and integration suites, validating microservices communication and eliminating regression defects.",
                        angle="e2e_testing",
                        is_default=False,
                        canonical_tags=["playwright", "microservices", "python"],
                    ),
                ],
            ),
            BulletSlot(
                id="exp_1_slot_2",
                name="Agentic AI Test Synthesis",
                mandatory=False,
                variants=[
                    BulletVariant(
                        id="exp_1_slot_2_v1",
                        text="Engineered Agentic AI workflows and structured prompt optimization pipelines within CI/CD, automating regression test synthesis to cut feedback cycle latency by 35%.",
                        angle="agentic_ai",
                        is_default=True,
                        canonical_tags=["agentic-ai", "prompt-engineering", "ci-cd"],
                    ),
                    BulletVariant(
                        id="exp_1_slot_2_v2",
                        text="Automated regression test creation using structured LLM prompts and CI/CD pipelines, reducing manual validation cycles by 35%.",
                        angle="automation_productivity",
                        is_default=False,
                        canonical_tags=["ci-cd", "prompt-engineering", "python"],
                    ),
                ],
            ),
            BulletSlot(
                id="exp_1_slot_3",
                name="Agile Software Engineering",
                mandatory=False,
                variants=[
                    BulletVariant(
                        id="exp_1_slot_3_v1",
                        text="Collaborated in cross-functional Agile teams (Scrum/Kanban) via Jira and Confluence, authoring SOLID-compliant test harnesses to standardize enterprise cloud quality.",
                        angle="agile_practices",
                        is_default=True,
                        canonical_tags=["agile", "jira", "solid"],
                    ),
                ],
            ),
        ],
    )

    exp_2 = Experience(
        id="exp_2",
        company="BRIC -- Rajiv Gandhi Centre for Biotechnology (RGCB)",
        location="Thiruvananthapuram, Kerala",
        title="Software / Computational Engineering Trainee",
        start_date="May 2025",
        end_date="June 2025",
        min_bullets=1,
        max_bullets=2,
        slots=[
            BulletSlot(
                id="exp_2_slot_1",
                name="ETL and Systems Automation",
                mandatory=False,
                variants=[
                    BulletVariant(
                        id="exp_2_slot_1_v1",
                        text="Automated common ETL tasks and data utilities in high-performance POSIX Linux, reducing manual compute overhead and batch data transformation latency by 60%.",
                        angle="systems_performance",
                        is_default=True,
                        canonical_tags=["linux", "bash", "python"],
                    ),
                ],
            ),
            BulletSlot(
                id="exp_2_slot_2",
                name="Concurrent Batch Pipelines",
                mandatory=False,
                variants=[
                    BulletVariant(
                        id="exp_2_slot_2_v1",
                        text="Engineered fault-tolerant Linux Bash pipelines and batch processing scripts, optimizing disk I/O, process concurrency, and memory utilization for molecular research datasets.",
                        angle="pipeline_optimization",
                        is_default=True,
                        canonical_tags=["bash", "linux", "concurrency"],
                    ),
                ],
            ),
        ],
    )

    proj_1 = Project(
        id="proj_1",
        title="PaleoRAG -- Distributed Hybrid RAG Engine",
        github_url="https://github.com/Bondae1103/Paleo-RAG",
        min_bullets=1,
        max_bullets=3,
        slots=[
            BulletSlot(
                id="proj_1_slot_1",
                name="Distributed Backend Microservice",
                mandatory=True,
                variants=[
                    BulletVariant(
                        id="proj_1_slot_1_v1",
                        text="Architected an asynchronous, distributed backend microservice with FastAPI, Celery, and Redis as a message broker for concurrent ingestion and structural parsing of documents.",
                        angle="distributed_architecture",
                        is_default=True,
                        canonical_tags=["fastapi", "celery", "redis", "microservices"],
                    ),
                ],
            ),
            BulletSlot(
                id="proj_1_slot_2",
                name="Hybrid Retrieval Engine",
                mandatory=False,
                variants=[
                    BulletVariant(
                        id="proj_1_slot_2_v1",
                        text="Engineered a hybrid retrieval engine combining PubMedBERT embeddings with BM25 indexing in Qdrant, attaining 100% Recall@5 and 0% hallucination rate on 27 benchmarks.",
                        angle="vector_retrieval",
                        is_default=True,
                        canonical_tags=["qdrant", "redis", "fastapi"],
                    ),
                ],
            ),
            BulletSlot(
                id="proj_1_slot_3",
                name="Streaming and Containerization",
                mandatory=False,
                variants=[
                    BulletVariant(
                        id="proj_1_slot_3_v1",
                        text="Implemented low-latency streaming via Server-Sent Events (SSE) with post-hoc citation verification; containerized with Docker Compose and authored a 44-test Pytest suite (100% pass rate).",
                        angle="devops_streaming",
                        is_default=True,
                        canonical_tags=["docker", "pytest", "fastapi"],
                    ),
                ],
            ),
        ],
    )

    proj_2 = Project(
        id="proj_2",
        title="Startle -- Connectome-Driven Neural Simulation Engine",
        github_url="https://github.com/Bondae1103/Startle",
        min_bullets=1,
        max_bullets=2,
        slots=[
            BulletSlot(
                id="proj_2_slot_1",
                name="Real-time Physics and Simulation Engine",
                mandatory=False,
                variants=[
                    BulletVariant(
                        id="proj_2_slot_1_v1",
                        text="Engineered a real-time simulation engine in TypeScript modeling the 158K-neuron Drosophila connectome, implementing Leaky Integrate-and-Fire (LIF) dynamics at 60fps on HTML5 Canvas.",
                        angle="systems_simulation",
                        is_default=True,
                        canonical_tags=["typescript", "html"],
                    ),
                ],
            ),
            BulletSlot(
                id="proj_2_slot_2",
                name="Offline Normalization and Automated Physics Verification",
                mandatory=False,
                variants=[
                    BulletVariant(
                        id="proj_2_slot_2_v1",
                        text="Built an offline Python pipeline normalizing 1,100+ synaptic inputs; authored an automated Vitest suite verifying 1,000 escape trajectories with 2D boundary collision physics.",
                        angle="physics_testing",
                        is_default=True,
                        canonical_tags=["python", "vitest"],
                    ),
                ],
            ),
        ],
    )

    proj_3 = Project(
        id="proj_3",
        title="AfroTB -- Phylogeny-Aware Graph Neural Network (GNN)",
        github_url="https://github.com/Bondae1103/AfroTB-phylo-GNN-AMR-predictor",
        min_bullets=1,
        max_bullets=2,
        slots=[
            BulletSlot(
                id="proj_3_slot_1",
                name="Multi-task Graph Convolutional Network Architecture",
                mandatory=False,
                variants=[
                    BulletVariant(
                        id="proj_3_slot_1_v1",
                        text="Architected a multi-task Graph Convolutional Network (GCN) in PyTorch Geometric across 13,753 clinical isolates to jointly predict resistance phenotypes across 9 anti-TB drugs.",
                        angle="graph_deep_learning",
                        is_default=True,
                        canonical_tags=["pytorch", "pytorch-geometric", "python"],
                    ),
                ],
            ),
            BulletSlot(
                id="proj_3_slot_2",
                name="Phylogenetic Graph Construction and Model Evaluation",
                mandatory=False,
                variants=[
                    BulletVariant(
                        id="proj_3_slot_2_v1",
                        text="Engineered Jaccard-weighted phylogenetic mutation graphs across 157 loci; conducted ablation studies and was selected for institutional showcase at Gravitas 2026.",
                        angle="feature_engineering",
                        is_default=True,
                        canonical_tags=["pytorch", "scikit-learn"],
                    ),
                ],
            ),
        ],
    )

    skill_groups = [
        SkillGroup(
            id="sg_languages",
            category="Languages",
            skills=["Python", "Java", "C++", "TypeScript", "SQL", "Bash/Shell", "R"],
        ),
        SkillGroup(
            id="sg_ml",
            category="Machine Learning & AI",
            skills=["Prompt Optimization / Engineering", "Agentic AI / LLMs", "PyTorch", "PyTorch Geometric (GNNs)", "Scikit-learn", "XGBoost", "SHAP Explainability"],
        ),
        SkillGroup(
            id="sg_backend",
            category="Backend & Distributed Systems",
            skills=["FastAPI", "Celery (Task Queues)", "Redis (Cache & Broker)", "RESTful APIs", "Server-Sent Events (SSE)", "Microservices"],
        ),
        SkillGroup(
            id="sg_devops",
            category="Cloud & DevOps",
            skills=["AWS (Lambda, S3)", "Docker", "Docker Compose", "Git", "GitHub Actions", "CI/CD Pipelines", "Linux/POSIX"],
        ),
    ]

    return Profile(
        id="profile_anoop_nair",
        version=1,
        contact=contact,
        education=education,
        experiences=[exp_1, exp_2],
        projects=[proj_1, proj_2, proj_3],
        skill_groups=skill_groups,
        leadership=[],
        metadata={"author": "Anoop Nair"},
    )
