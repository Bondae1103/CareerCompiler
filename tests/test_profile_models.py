"""Tests for Profile domain models and validation invariants."""

import pytest
from pydantic import ValidationError

from careercompiler.models.profile import (
    BulletSlot,
    BulletVariant,
    ContactInfo,
    Education,
    Experience,
    Profile,
)


def _sample_contact() -> ContactInfo:
    return ContactInfo(
        name="Anoop Nair",
        phone="+91 8547560400",
        email="anoop@example.com",
    )


def test_valid_variant_and_slot() -> None:
    v1 = BulletVariant(
        id="v1_perf",
        text="Engineered Raft consensus achieving 45k ops/sec.",
        angle="performance",
        is_default=True,
    )
    slot = BulletSlot(
        id="slot_raft",
        name="Raft consensus implementation",
        variants=[v1],
    )
    assert slot.get_default_variant().id == "v1_perf"


def test_empty_variant_text_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        BulletVariant(
            id="v1",
            text="   ",
            angle="general",
        )
    assert "Text cannot be empty" in str(exc.value)


def test_control_characters_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        BulletVariant(
            id="v1",
            text="Invalid\x00control character",
            angle="general",
        )
    assert "forbidden control characters" in str(exc.value)


def test_text_length_cap_enforced() -> None:
    huge_text = "A" * 1001
    with pytest.raises(ValidationError) as exc:
        BulletVariant(
            id="v1",
            text=huge_text,
            angle="general",
        )
    assert "exceeds maximum limit" in str(exc.value)


def test_invalid_id_format_rejected() -> None:
    invalid_ids = ["bad id with spaces", "id$with#symbols", "slash/id", ""]
    for bad_id in invalid_ids:
        with pytest.raises(ValidationError) as exc:
            BulletVariant(
                id=bad_id,
                text="Valid bullet text",
                angle="general",
            )
        assert "Invalid ID" in str(exc.value) or "at least 1 character" in str(exc.value)


def test_multiple_defaults_in_slot_rejected() -> None:
    v1 = BulletVariant(id="v1", text="Text 1", angle="a1", is_default=True)
    v2 = BulletVariant(id="v2", text="Text 2", angle="a2", is_default=True)
    with pytest.raises(ValidationError) as exc:
        BulletSlot(id="slot1", name="Slot 1", variants=[v1, v2])
    assert "multiple default variants" in str(exc.value)


def test_no_default_auto_designates_first() -> None:
    v1 = BulletVariant(id="v1", text="Text 1", angle="a1", is_default=False)
    v2 = BulletVariant(id="v2", text="Text 2", angle="a2", is_default=False)
    slot = BulletSlot(id="slot1", name="Slot 1", variants=[v1, v2])
    assert slot.variants[0].is_default is True
    assert slot.variants[1].is_default is False


def test_duplicate_variant_ids_rejected() -> None:
    v1 = BulletVariant(id="v1", text="Text 1", angle="a1")
    v2 = BulletVariant(id="v1", text="Text 2", angle="a2")
    with pytest.raises(ValidationError) as exc:
        BulletSlot(id="slot1", name="Slot 1", variants=[v1, v2])
    assert "Duplicate variant IDs found" in str(exc.value)


def test_experience_slot_bounds_and_duplicates() -> None:
    # min_bullets > max_bullets
    with pytest.raises(ValidationError) as exc:
        Experience(
            id="exp1",
            company="Company",
            location="Location",
            title="Title",
            start_date="2025",
            end_date="2026",
            min_bullets=3,
            max_bullets=2,
        )
    assert "cannot be less than min_bullets" in str(exc.value)

    # duplicate slot IDs
    v = BulletVariant(id="v1", text="Text", angle="general")
    s1 = BulletSlot(id="slot_dup", name="S1", variants=[v])
    s2 = BulletSlot(id="slot_dup", name="S2", variants=[v])
    with pytest.raises(ValidationError) as exc:
        Experience(
            id="exp1",
            company="Company",
            location="Location",
            title="Title",
            start_date="2025",
            end_date="2026",
            slots=[s1, s2],
        )
    assert "Duplicate slot IDs found" in str(exc.value)


def test_profile_duplicate_entity_ids_rejected() -> None:
    contact = _sample_contact()
    e1 = Education(id="edu_vit", institution="VIT", location="Vellore", degree="B.Tech", dates="2023-Present")
    e2 = Education(id="edu_vit", institution="VIT 2", location="Vellore", degree="B.Tech", dates="2023-Present")

    with pytest.raises(ValidationError) as exc:
        Profile(
            id="prof_anoop",
            contact=contact,
            education=[e1, e2],
        )
    assert "Duplicate education IDs found" in str(exc.value)
