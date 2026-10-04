"""Tests for Taxonomy domain models, validations, and catalog index."""

import pytest
from pydantic import ValidationError

from careercompiler.taxonomy.models import (
    DisambiguationRule,
    EntityMatch,
    EntityType,
    TaxonomyCatalog,
    TaxonomyEntity,
)


def test_valid_taxonomy_entity() -> None:
    entity = TaxonomyEntity(
        canonical_id="postgresql",
        display_name="PostgreSQL",
        type=EntityType.DATABASE,
        aliases=["PostgreSQL", "Postgres", "psql"],
        ambiguous=False,
        source="stack_overflow",
        license="CC-BY-SA-4.0",
        version="1.0.0",
        reviewed=True,
    )
    assert entity.canonical_id == "postgresql"
    assert len(entity.aliases) == 3
    assert entity.reviewed is True


def test_canonical_id_validation() -> None:
    # Invalid characters or uppercase
    with pytest.raises(ValidationError):
        TaxonomyEntity(
            canonical_id="PostgreSQL",  # uppercase forbidden
            display_name="PostgreSQL",
            type=EntityType.DATABASE,
            aliases=["PostgreSQL"],
            source="manual",
            license="MIT",
        )

    with pytest.raises(ValidationError):
        TaxonomyEntity(
            canonical_id="invalid space id",
            display_name="Test",
            type=EntityType.TOOL,
            aliases=["Test"],
            source="manual",
            license="MIT",
        )


def test_empty_or_whitespace_aliases_rejected() -> None:
    with pytest.raises(ValidationError):
        TaxonomyEntity(
            canonical_id="test",
            display_name="Test",
            type=EntityType.TOOL,
            aliases=["   "],
            source="manual",
            license="MIT",
        )


def test_catalog_duplicate_canonical_ids_rejected() -> None:
    e1 = TaxonomyEntity(
        canonical_id="docker",
        display_name="Docker",
        type=EntityType.DEVOPS,
        aliases=["Docker"],
        source="manual",
        license="MIT",
    )
    e2 = TaxonomyEntity(
        canonical_id="docker",
        display_name="Docker 2",
        type=EntityType.DEVOPS,
        aliases=["Docker2"],
        source="manual",
        license="MIT",
    )
    with pytest.raises(ValidationError) as exc:
        TaxonomyCatalog(entities=[e1, e2])
    assert "Duplicate canonical_id 'docker'" in str(exc.value)


def test_catalog_canonicalize_lookups() -> None:
    e1 = TaxonomyEntity(
        canonical_id="postgresql",
        display_name="PostgreSQL",
        type=EntityType.DATABASE,
        aliases=["PostgreSQL", "Postgres", "psql"],
        ambiguous=False,
        source="manual",
        license="MIT",
    )
    e2 = TaxonomyEntity(
        canonical_id="golang",
        display_name="Go",
        type=EntityType.LANGUAGE,
        aliases=["Go", "Golang"],
        ambiguous=True,
        disambiguation_rules=[DisambiguationRule(case_sensitive=True)],
        source="manual",
        license="MIT",
    )
    catalog = TaxonomyCatalog(entities=[e1, e2])

    assert catalog.canonicalize("postgresql") == "postgresql"
    assert catalog.canonicalize("PostgreSQL") == "postgresql"
    assert catalog.canonicalize("postgres") == "postgresql"
    assert catalog.canonicalize("psql") == "postgresql"
    assert catalog.canonicalize("Go") == "golang"
    assert catalog.canonicalize("Golang") == "golang"
    assert catalog.canonicalize("unknown_term") is None


def test_entity_match_offset_validation() -> None:
    # Valid match
    match = EntityMatch(
        canonical_id="python",
        surface_form="Python",
        start=5,
        end=11,
    )
    assert match.start == 5
    assert match.end == 11

    # End <= start invalid
    with pytest.raises(ValidationError):
        EntityMatch(
            canonical_id="python",
            surface_form="Python",
            start=5,
            end=5,
        )

    with pytest.raises(ValidationError):
        EntityMatch(
            canonical_id="python",
            surface_form="Python",
            start=10,
            end=5,
        )
