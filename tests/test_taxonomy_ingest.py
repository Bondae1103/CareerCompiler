"""Tests for taxonomy ingestion pipeline and provenance tracking."""

import json
from pathlib import Path

import pytest

from careercompiler.taxonomy.ingest import (
    export_taxonomy,
    ingest_records,
    load_seed_taxonomy,
)
from careercompiler.taxonomy.models import EntityType, TaxonomyCatalog, TaxonomyEntity


def test_seed_taxonomy_size_and_review_status() -> None:
    catalog = load_seed_taxonomy()
    assert len(catalog.entities) >= 200, f"Expected >= 200 entities, got {len(catalog.entities)}"

    unreviewed = [e.canonical_id for e in catalog.entities if not e.reviewed]
    assert len(unreviewed) == 0, f"Found unreviewed entities: {unreviewed}"


def test_provenance_manifest_integrity() -> None:
    manifest_path = Path("careercompiler/taxonomy/data/provenance_manifest.json")
    assert manifest_path.exists(), "Provenance manifest must exist"

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    assert "sources" in manifest
    assert len(manifest["sources"]) >= 2
    assert "summary" in manifest
    summary = manifest["summary"]
    assert summary["total_entities"] >= 200
    assert summary["unreviewed_count"] == 0
    assert "MIT" in summary["by_license"]
    assert "CC-BY-SA-4.0" in summary["by_license"]


def test_ingest_records_merge_and_validation(tmp_path: Path) -> None:
    initial_entity = TaxonomyEntity(
        canonical_id="docker",
        display_name="Docker",
        type=EntityType.DEVOPS,
        aliases=["Docker"],
        source="manual",
        license="MIT",
    )
    catalog = TaxonomyCatalog(entities=[initial_entity])

    new_records = [
        {
            "canonical_id": "docker",
            "display_name": "Docker",
            "type": "devops",
            "aliases": ["Dockerfile", "docker engine"],
            "source": "manual",
            "license": "MIT",
        },
        {
            "canonical_id": "podman",
            "display_name": "Podman",
            "type": "devops",
            "aliases": ["Podman"],
            "source": "manual",
            "license": "Apache-2.0",
        },
    ]

    updated_catalog, stats = ingest_records(
        records=new_records,
        existing_catalog=catalog,
        default_source="manual",
        default_license="MIT",
        mark_reviewed=True,
    )

    assert stats["added"] == 1
    assert stats["updated"] == 1
    assert stats["aliases_added"] == 2

    docker = updated_catalog.get_by_id("docker")
    assert docker is not None
    assert "Dockerfile" in docker.aliases
    assert "docker engine" in docker.aliases

    podman = updated_catalog.get_by_id("podman")
    assert podman is not None
    assert podman.license == "Apache-2.0"

    # Export test
    out_file = tmp_path / "exported_tax.json"
    man_file = tmp_path / "exported_man.json"
    export_taxonomy(updated_catalog, out_file, man_file)

    assert out_file.exists()
    assert man_file.exists()


def test_unsupported_license_rejected() -> None:
    catalog = TaxonomyCatalog(entities=[])
    records = [
        {
            "canonical_id": "tool",
            "display_name": "Tool",
            "type": "tool",
            "aliases": ["Tool"],
            "license": "GPL-3.0-VIRAL",
        }
    ]
    with pytest.raises(ValueError) as exc:
        ingest_records(records, catalog, "manual", "GPL-3.0-VIRAL")
    assert "Unsupported or unverified license" in str(exc.value)
