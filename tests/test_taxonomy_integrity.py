"""Integrity tests asserting every canonical tag in the repo exists in the taxonomy."""

import re
from pathlib import Path

from careercompiler.models.profile import Profile
from careercompiler.parsing.resume_parser import parse_latex_resume
from careercompiler.taxonomy.normalizer import get_default_normalizer
from tests.test_profile_storage import _build_test_profile

normalizer = get_default_normalizer()
catalog = normalizer.catalog
known_ids = {e.canonical_id for e in catalog.entities}


def test_test_profile_canonical_tags_exist() -> None:
    """Assert all canonical_tags in the reference test profile exist in taxonomy."""
    prof: Profile = _build_test_profile()

    for exp in prof.experiences:
        for s in exp.slots:
            for v in s.variants:
                for tag in v.canonical_tags:
                    assert tag in known_ids, f"Tag '{tag}' in experience '{exp.id}' missing from taxonomy"

    for proj in prof.projects:
        for s in proj.slots:
            for v in s.variants:
                for tag in v.canonical_tags:
                    assert tag in known_ids, f"Tag '{tag}' in project '{proj.id}' missing from taxonomy"


def test_resume_template_skills_canonicalization() -> None:
    """Assert skills parsed from templates/resume.tex resolve to valid canonical IDs."""
    tex_file = Path("templates/resume.tex")
    assert tex_file.exists()

    draft_profile = parse_latex_resume(tex_file.read_text(encoding="utf-8"))

    # Check project tools
    for proj in draft_profile.projects:
        for tool in proj.tools:
            # Check either canonicalize or normalize finds an entity
            cid = normalizer.canonicalize(tool)
            if cid is None:
                matches = normalizer.normalize(tool)
                if matches:
                    cid = matches[0].canonical_id
            assert cid is not None, f"Project tool '{tool}' in project '{proj.title}' not resolved"
            assert cid in known_ids

    # Check skill groups
    for sg in draft_profile.skill_groups:
        for skill in sg.skills:
            cid = normalizer.canonicalize(skill)
            if cid is None:
                matches = normalizer.normalize(skill)
                if matches:
                    cid = matches[0].canonical_id
            assert cid is not None, f"Skill '{skill}' in group '{sg.category}' not resolved in taxonomy"
            assert cid in known_ids


def test_codebase_fixtures_canonical_id_integrity() -> None:
    """Scan all Python test files for canonical_tags or canonical_id literals."""
    test_files = list(Path("tests").glob("*.py"))
    assert len(test_files) > 0

    tag_regex = re.compile(r'canonical_tags\s*=\s*\[(.*?)\]')

    for tf in test_files:
        content = tf.read_text(encoding="utf-8")
        for match in tag_regex.finditer(content):
            raw_tags = match.group(1)
            tags = re.findall(r'["\']([a-zA-Z0-9_-]+)["\']', raw_tags)
            for t in tags:
                assert t in known_ids, f"File {tf} references unknown canonical tag '{t}'"
