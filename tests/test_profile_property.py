"""Hypothesis property-based tests for Profile models and serialization."""

from hypothesis import given
from hypothesis import strategies as st

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
    export_profile_json,
    import_profile_json,
)

# Custom Hypothesis strategies
slug_strategy = st.from_regex(r"[a-z0-9_]{1,16}", fullmatch=True)
safe_text_strategy = st.text(
    alphabet=st.characters(blacklist_categories=("Cc", "Cs"), min_codepoint=32, max_codepoint=1000),
    min_size=1,
    max_size=150,
).map(lambda s: s.strip()).filter(lambda s: len(s) > 0)


@st.composite
def bullet_variant_strategy(draw: st.DrawFn, is_default: bool = False) -> BulletVariant:
    vid = draw(slug_strategy)
    text = draw(safe_text_strategy)
    angle = draw(slug_strategy)
    return BulletVariant(
        id=vid,
        text=text,
        angle=angle,
        is_default=is_default,
    )


@st.composite
def bullet_slot_strategy(draw: st.DrawFn) -> BulletSlot:
    sid = draw(slug_strategy)
    name = draw(safe_text_strategy)
    # Ensure unique variant IDs
    num_variants = draw(st.integers(min_value=1, max_value=3))
    variants: list[BulletVariant] = []
    seen_ids: set[str] = set()
    for i in range(num_variants):
        base_id = draw(slug_strategy)
        vid = f"{base_id}_{i}"
        if vid in seen_ids:
            vid = f"{base_id}_{i}_uniq"
        seen_ids.add(vid)
        text = draw(safe_text_strategy)
        angle = draw(slug_strategy)
        variants.append(
            BulletVariant(
                id=vid,
                text=text,
                angle=angle,
                is_default=(i == 0),
            )
        )
    return BulletSlot(id=sid, name=name, variants=variants)


@st.composite
def profile_strategy(draw: st.DrawFn) -> Profile:
    pid = draw(slug_strategy)
    contact = ContactInfo(
        name=draw(safe_text_strategy),
        phone=draw(safe_text_strategy),
        email="user@example.com",
    )
    # Slots with unique IDs
    slots: list[BulletSlot] = []
    seen_slots: set[str] = set()
    for j in range(draw(st.integers(min_value=1, max_value=2))):
        slot = draw(bullet_slot_strategy())
        slot_id = f"slot_{j}_{slot.id}"
        seen_slots.add(slot_id)
        slots.append(
            BulletSlot(
                id=slot_id,
                name=slot.name,
                variants=slot.variants,
            )
        )

    exp = Experience(
        id="exp_0",
        company=draw(safe_text_strategy),
        location=draw(safe_text_strategy),
        title=draw(safe_text_strategy),
        start_date="2025",
        end_date="2026",
        min_bullets=1,
        max_bullets=3,
        slots=slots,
    )

    proj = Project(
        id="proj_0",
        title=draw(safe_text_strategy),
        tools=["Python"],
        min_bullets=1,
        max_bullets=2,
    )

    edu = Education(
        id="edu_0",
        institution=draw(safe_text_strategy),
        location=draw(safe_text_strategy),
        degree=draw(safe_text_strategy),
        dates="2023-Present",
    )

    skills = SkillGroup(
        id="skills_0",
        category="Languages",
        skills=["Python"],
    )

    return Profile(
        id=pid,
        contact=contact,
        education=[edu],
        experiences=[exp],
        projects=[proj],
        skill_groups=[skills],
    )


@given(profile_strategy())
def test_hypothesis_profile_roundtrip(profile: Profile) -> None:
    """Property test: Arbitrary valid profiles survive serialization and deserialization."""
    exported_json = export_profile_json(profile)
    imported_profile = import_profile_json(exported_json)
    reexported_json = export_profile_json(imported_profile)

    assert reexported_json == exported_json
    assert imported_profile == profile
