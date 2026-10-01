"""Storage repository and round-trip tests for Master Profile Bank."""

from pathlib import Path

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
from careercompiler.storage.sqlite_repo import (
    SQLiteProfileRepository,
    export_profile_json,
    import_profile_json,
)


def _build_test_profile() -> Profile:
    contact = ContactInfo(
        name="Anoop Nair",
        phone="+91 8547560400",
        email="anoop.nair.1103@gmail.com",
        linkedin_url="https://www.linkedin.com/in/anoop-nair-4a180928a",
        github_url="https://github.com/Bondae1103",
        portfolio_url="https://portfolio-website-anoop.vercel.app",
    )
    edu = Education(
        id="edu_vit",
        institution="Vellore Institute of Technology",
        location="Vellore, Tamil Nadu",
        degree="B.Tech Computer Science Engineering (Bioinformatics)",
        dates="Sep 2023 -- Present",
        details="CGPA: 8.82",
    )
    v1 = BulletVariant(
        id="v1_test_automation",
        text="Architected modular end-to-end and REST API test frameworks using Playwright and OOP design patterns, achieving 100% test coverage across enterprise cloud services and microservices.",
        angle="quality_architecture",
        is_default=True,
        canonical_tags=["playwright", "rest-api", "microservices", "oop"],
    )
    v2 = BulletVariant(
        id="v2_prompt_opt",
        text="Engineered Agentic AI workflows and structured prompt optimization pipelines within CI/CD, automating regression test synthesis to cut feedback cycle latency by 35%.",
        angle="agentic_ai",
        is_default=False,
        canonical_tags=["agentic-ai", "prompt-engineering", "ci-cd"],
    )
    slot1 = BulletSlot(
        id="slot_thermo_frameworks",
        name="Enterprise Test Frameworks",
        variants=[v1, v2],
    )
    exp = Experience(
        id="exp_thermo_fisher",
        company="Thermo Fisher Scientific",
        location="Bengaluru, Karnataka",
        title="Software Developer Intern",
        start_date="May 2026",
        end_date="July 2026",
        min_bullets=1,
        max_bullets=3,
        slots=[slot1],
    )
    proj_v = BulletVariant(
        id="v1_paleorag_arch",
        text="Architected an asynchronous, distributed backend microservice with FastAPI, Celery, and Redis as a message broker for concurrent ingestion and structural parsing of documents.",
        angle="distributed_systems",
        is_default=True,
        canonical_tags=["fastapi", "celery", "redis", "distributed-systems"],
    )
    proj_slot = BulletSlot(
        id="slot_paleorag_core",
        name="Distributed Hybrid RAG Architecture",
        variants=[proj_v],
    )
    proj = Project(
        id="proj_paleorag",
        title="PaleoRAG -- Distributed Hybrid RAG Engine",
        tools=["FastAPI", "Celery", "Redis", "Qdrant", "Docker Compose", "Pytest"],
        github_url="https://github.com/Bondae1103/Paleo-RAG",
        min_bullets=1,
        max_bullets=3,
        slots=[proj_slot],
    )
    skills = SkillGroup(
        id="skills_languages",
        category="Languages",
        skills=["Python", "Java", "C++", "TypeScript", "SQL", "Bash/Shell", "R"],
    )

    return Profile(
        id="profile_anoop_nair",
        version=1,
        contact=contact,
        education=[edu],
        experiences=[exp],
        projects=[proj],
        skill_groups=[skills],
    )


def test_sqlite_repository_crud(tmp_path: Path) -> None:
    db_file = tmp_path / "test_profiles.db"
    repo = SQLiteProfileRepository(db_file)

    profile = _build_test_profile()
    repo.save(profile)

    assert repo.list_ids() == ["profile_anoop_nair"]

    retrieved = repo.get("profile_anoop_nair")
    assert retrieved is not None
    assert retrieved.id == profile.id
    assert retrieved.contact.name == "Anoop Nair"
    assert len(retrieved.experiences) == 1
    assert len(retrieved.experiences[0].slots[0].variants) == 2

    # Non-existent ID returns None
    assert repo.get("non_existent_profile") is None

    # Delete
    deleted = repo.delete("profile_anoop_nair")
    assert deleted is True
    assert repo.get("profile_anoop_nair") is None
    assert repo.list_ids() == []

    repo.close()


def test_json_export_import_byte_identical() -> None:
    """Acceptance check: export -> import -> export is byte-identical."""
    profile = _build_test_profile()

    json_1 = export_profile_json(profile)
    imported_1 = import_profile_json(json_1)
    json_2 = export_profile_json(imported_1)

    assert json_1 == json_2
    assert imported_1 == profile


def test_user_text_stored_as_authored() -> None:
    """Acceptance check: preserve Unicode, special symbols, strip only outer whitespace."""
    contact = ContactInfo(
        name="   Dr. Anoop Nair   ",  # Outer whitespace should be trimmed by validator if configured
        phone="+91 8547560400",
        email="anoop@example.com",
    )
    unicode_text = "Em-dash: — | Greek: α, β, γ | Math: ≤, ≥, ≈ | Quotes: “smart”"
    v = BulletVariant(
        id="v_unicode",
        text=f"  {unicode_text}  ",
        angle="general",
    )
    slot = BulletSlot(id="slot_u", name="Unicode slot", variants=[v])
    profile = Profile(id="prof_u", contact=contact, leadership=[slot])

    json_str = export_profile_json(profile)
    imported = import_profile_json(json_str)

    stored_variant = imported.leadership[0].variants[0]
    assert stored_variant.text == unicode_text
