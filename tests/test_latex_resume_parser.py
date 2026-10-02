"""Tests for draft resume parser from templates/resume.tex."""

from pathlib import Path

from careercompiler.parsing.resume_parser import parse_latex_resume


def test_parse_real_resume_template() -> None:
    template_path = Path("templates/resume.tex")
    content = template_path.read_text(encoding="utf-8")

    profile = parse_latex_resume(content, profile_id="anoop_nair_draft")

    assert profile.id == "anoop_nair_draft"
    assert "Anoop Nair" in profile.contact.name
    assert "8547560400" in profile.contact.phone
    assert "anoop.nair.1103@gmail.com" in profile.contact.email
    assert len(profile.education) >= 1
    assert any("Vellore Institute of Technology" in e.institution for e in profile.education)

    # Experiences
    assert len(profile.experiences) >= 2
    assert any("Thermo Fisher Scientific" in exp.company for exp in profile.experiences)
    assert any("Rajiv Gandhi Centre for Biotechnology" in exp.company for exp in profile.experiences)

    # Projects
    assert len(profile.projects) >= 3
    assert any("PaleoRAG" in p.title for p in profile.projects)
    assert any("Startle" in p.title for p in profile.projects)
    assert any("AfroTB" in p.title for p in profile.projects)

    # Technical Skills
    assert len(profile.skill_groups) >= 4
    all_skills = [s for g in profile.skill_groups for s in g.skills]
    assert "Python" in all_skills
    assert "PyTorch" in all_skills
    assert "FastAPI" in all_skills
