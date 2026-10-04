"""Ingestion pipeline for scaling taxonomy with verified open sources."""

import json
from pathlib import Path
from typing import Any

from careercompiler.taxonomy.models import (
    DisambiguationRule,
    EntityType,
    TaxonomyCatalog,
    TaxonomyEntity,
)

SUPPORTED_LICENSES = {
    "MIT": "Permissive open source license with attribution.",
    "CC-BY-SA-4.0": "Creative Commons Attribution-ShareAlike 4.0 International.",
    "CC0-1.0": "Creative Commons Public Domain Dedication.",
    "Apache-2.0": "Apache 2.0 permissive license.",
    "permissive_open_source": "Permissive public project specification.",
}


def load_seed_taxonomy(seed_path: Path | str | None = None) -> TaxonomyCatalog:
    """Load the curated seed taxonomy from JSON file."""
    if seed_path is None:
        seed_path = Path(__file__).parent / "data" / "seed_taxonomy.json"
    else:
        seed_path = Path(seed_path)

    if not seed_path.exists():
        raise FileNotFoundError(f"Seed taxonomy not found at: {seed_path}")

    with open(seed_path, encoding="utf-8") as f:
        data = json.load(f)

    entities: list[TaxonomyEntity] = []
    for item in data:
        entities.append(TaxonomyEntity.model_validate(item))

    return TaxonomyCatalog(entities=entities)


def ingest_records(
    records: list[dict[str, Any]],
    existing_catalog: TaxonomyCatalog,
    default_source: str,
    default_license: str,
    mark_reviewed: bool = False,
) -> tuple[TaxonomyCatalog, dict[str, int]]:
    """Merge new external entity records into an existing catalog with strict validation.

    Ensures license compliance, canonical ID slug integrity, and alias deduplication.
    """
    if default_license not in SUPPORTED_LICENSES:
        raise ValueError(
            f"Unsupported or unverified license '{default_license}'. "
            f"Supported licenses: {list(SUPPORTED_LICENSES.keys())}"
        )

    entity_map: dict[str, TaxonomyEntity] = {e.canonical_id: e for e in existing_catalog.entities}
    stats = {"added": 0, "updated": 0, "aliases_added": 0}

    for record in records:
        canonical_id = record["canonical_id"].strip().lower()
        display_name = record["display_name"].strip()
        entity_type = EntityType(record.get("type", EntityType.TOOL))
        aliases = [a.strip() for a in record.get("aliases", []) if a.strip()]
        if display_name not in aliases:
            aliases.insert(0, display_name)

        source = record.get("source", default_source)
        license_name = record.get("license", default_license)
        if license_name not in SUPPORTED_LICENSES:
            raise ValueError(f"Record {canonical_id} has invalid license '{license_name}'.")

        ambiguous = bool(record.get("ambiguous", False))
        rules_data = record.get("disambiguation_rules", [])
        rules = [DisambiguationRule.model_validate(r) for r in rules_data]

        if canonical_id in entity_map:
            # Merge aliases
            existing = entity_map[canonical_id]
            existing_aliases = set(existing.aliases)
            added_aliases = [a for a in aliases if a not in existing_aliases]
            if added_aliases:
                merged_aliases = list(existing.aliases) + added_aliases
                entity_map[canonical_id] = existing.model_copy(
                    update={"aliases": merged_aliases}
                )
                stats["aliases_added"] += len(added_aliases)
                stats["updated"] += 1
        else:
            new_entity = TaxonomyEntity(
                canonical_id=canonical_id,
                display_name=display_name,
                type=entity_type,
                aliases=aliases,
                ambiguous=ambiguous,
                disambiguation_rules=rules,
                source=source,
                license=license_name,
                version="1.0.0",
                reviewed=mark_reviewed,
            )
            entity_map[canonical_id] = new_entity
            stats["added"] += 1

    updated_catalog = TaxonomyCatalog(entities=list(entity_map.values()))
    return updated_catalog, stats


def export_taxonomy(
    catalog: TaxonomyCatalog,
    output_path: Path | str,
    manifest_path: Path | str | None = None,
) -> None:
    """Export validated catalog to JSON and update provenance manifest."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump([e.model_dump() for e in catalog.entities], f, indent=2)

    if manifest_path is not None:
        man_file = Path(manifest_path)
        manifest_data: dict[str, Any] = {}
        if man_file.exists():
            with open(man_file, encoding="utf-8") as f:
                manifest_data = json.load(f)

        by_source: dict[str, int] = {}
        by_type: dict[str, int] = {}
        by_license: dict[str, int] = {}
        unreviewed_count = 0

        for e in catalog.entities:
            by_source[e.source] = by_source.get(e.source, 0) + 1
            by_type[e.type.value] = by_type.get(e.type.value, 0) + 1
            by_license[e.license] = by_license.get(e.license, 0) + 1
            if not e.reviewed:
                unreviewed_count += 1

        manifest_data["summary"] = {
            "total_entities": len(catalog.entities),
            "unreviewed_count": unreviewed_count,
            "by_source": by_source,
            "by_type": by_type,
            "by_license": by_license,
        }

        with open(man_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
