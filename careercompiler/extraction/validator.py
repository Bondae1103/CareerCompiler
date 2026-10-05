"""Strict post-validator for extracted Job Description chunks."""

from typing import Any

from careercompiler.extraction.models import (
    ExtractedJD,
    ExtractedRequirement,
    RequirementCategory,
    ScaleIndicator,
)
from careercompiler.taxonomy.models import TaxonomyCatalog

CUE_PHRASE_MAX_IMPORTANCE = {
    "required": 1.0,
    "must have": 1.0,
    "must": 1.0,
    "minimum": 1.0,
    "essential": 1.0,
    "mandatory": 1.0,
    "basic qualifications": 1.0,
    "preferred": 0.7,
    "nice to have": 0.6,
    "plus": 0.65,
    "bonus": 0.6,
    "desired": 0.7,
    "advantageous": 0.65,
}


def validate_extracted_requirement(
    item_data: dict[str, Any] | ExtractedRequirement,
    source_text: str,
    catalog: TaxonomyCatalog,
) -> tuple[ExtractedRequirement | None, str | None]:
    """Validate a candidate requirement against source text evidence and taxonomy."""
    if isinstance(item_data, ExtractedRequirement):
        d = item_data.model_dump()
    elif isinstance(item_data, dict):
        d = dict(item_data)
    else:
        return None, f"Malformed requirement item type: {type(item_data)}"

    req_id = str(d.get("id", "req_unknown"))
    surface_form = str(d.get("surface_form", "")).strip()
    if not surface_form:
        return None, f"Item '{req_id}' dropped: surface_form is empty."

    raw_span = d.get("evidence_span")
    if not raw_span or not isinstance(raw_span, (list, tuple)) or len(raw_span) != 2:
        return None, f"Item '{req_id}' dropped: invalid evidence_span format {raw_span}."

    try:
        start = int(raw_span[0])
        end = int(raw_span[1])
    except (ValueError, TypeError):
        return None, f"Item '{req_id}' dropped: span offsets are not integers."

    # Invariant: 0 <= start < end <= len(source_text)
    text_len = len(source_text)
    if start < 0 or end <= start or end > text_len:
        return None, (
            f"Item '{req_id}' dropped: span [{start}, {end}] out of bounds for source length {text_len}."
        )

    # Invariant: source[span] must contain the surface form (case-insensitive)
    slice_text = source_text[start:end]
    if surface_form.lower() not in slice_text.lower():
        # Check if surface_form was slightly mis-offset; if not found, drop as hallucination
        return None, (
            f"Item '{req_id}' dropped: surface_form '{surface_form}' not present in evidence slice '{slice_text}'."
        )

    # Invariant: canonical_id maps to taxonomy or flagged unmapped
    canonical_id = d.get("canonical_id")
    unmapped = bool(d.get("unmapped", False))

    if canonical_id:
        canonical_id = str(canonical_id).strip().lower()
        entity = catalog.get_by_id(canonical_id)
        if entity is None:
            # Attempt to resolve via surface form
            resolved = catalog.canonicalize(surface_form)
            if resolved:
                canonical_id = resolved
                unmapped = False
            else:
                canonical_id = None
                unmapped = True
    else:
        resolved = catalog.canonicalize(surface_form)
        if resolved:
            canonical_id = resolved
            unmapped = False
        else:
            canonical_id = None
            unmapped = True

    # Category validation
    raw_cat = str(d.get("category", RequirementCategory.MUST_HAVE)).lower()
    if raw_cat in ("nice_to_have", "preferred", "optional"):
        category = RequirementCategory.NICE_TO_HAVE
    else:
        category = RequirementCategory.MUST_HAVE

    # Invariant: required_experience_years matches digits in span
    raw_years = d.get("required_years")
    required_years: float | None = None
    if raw_years is not None:
        try:
            val = float(raw_years)
            # Verify digits appear in slice_text
            int_str = str(int(val))
            if int_str in slice_text or f"{val:.1f}" in slice_text:
                required_years = val
            else:
                # Dropped invalid years qualification
                required_years = None
        except (ValueError, TypeError):
            required_years = None

    # Cue phrase and importance validation (anti-tampering / prompt injection defense)
    cue_phrase = d.get("cue_phrase")
    raw_importance = float(d.get("importance", 0.5))

    max_importance = 1.0
    if cue_phrase and str(cue_phrase).lower() in CUE_PHRASE_MAX_IMPORTANCE:
        max_importance = CUE_PHRASE_MAX_IMPORTANCE[str(cue_phrase).lower()]
    elif category == RequirementCategory.NICE_TO_HAVE:
        max_importance = 0.7

    # Cap importance to verified maximum
    importance = min(max(0.0, raw_importance), max_importance)

    validated = ExtractedRequirement(
        id=req_id,
        canonical_id=canonical_id,
        surface_form=surface_form,
        evidence_span=(start, end),
        evidence_text=slice_text,
        category=category,
        required_years=required_years,
        importance=importance,
        cue_phrase=str(cue_phrase) if cue_phrase else None,
        unmapped=unmapped,
    )
    return validated, None


def validate_scale_indicator(
    indicator_data: dict[str, Any] | ScaleIndicator,
    source_text: str,
) -> tuple[ScaleIndicator | None, str | None]:
    """Validate a candidate scale indicator against source text."""
    if isinstance(indicator_data, ScaleIndicator):
        d = indicator_data.model_dump()
    elif isinstance(indicator_data, dict):
        d = dict(indicator_data)
    else:
        return None, f"Malformed scale indicator type: {type(indicator_data)}"

    ind_id = str(d.get("id", "scale_unknown"))
    metric = str(d.get("metric", "general")).strip()
    value = str(d.get("value", "")).strip()
    if not value:
        return None, f"Scale indicator '{ind_id}' dropped: value is empty."

    raw_span = d.get("evidence_span")
    if not raw_span or not isinstance(raw_span, (list, tuple)) or len(raw_span) != 2:
        return None, f"Scale indicator '{ind_id}' dropped: invalid span {raw_span}."

    try:
        start = int(raw_span[0])
        end = int(raw_span[1])
    except (ValueError, TypeError):
        return None, f"Scale indicator '{ind_id}' dropped: span offsets are not integers."

    text_len = len(source_text)
    if start < 0 or end <= start or end > text_len:
        return None, (
            f"Scale indicator '{ind_id}' dropped: span [{start}, {end}] out of bounds for source length {text_len}."
        )

    slice_text = source_text[start:end]
    if value.lower() not in slice_text.lower():
        return None, (
            f"Scale indicator '{ind_id}' dropped: value '{value}' not attested in slice '{slice_text}'."
        )

    validated = ScaleIndicator(
        id=ind_id,
        metric=metric,
        value=value,
        evidence_span=(start, end),
        evidence_text=slice_text,
    )
    return validated, None


def validate_extracted_jd(
    raw_data: dict[str, Any],
    source_text: str,
    catalog: TaxonomyCatalog,
    extractor_name: str,
    extractor_version: str,
    cache_key: str,
) -> ExtractedJD:
    """Post-validate an entire raw extraction payload into a strict ExtractedJD container."""
    role_title = str(raw_data.get("role_title", "Software Engineer")).strip()
    if not role_title:
        role_title = "Software Engineer"

    role_span = raw_data.get("role_title_span")
    validated_role_span: tuple[int, int] | None = None
    if (
        role_span
        and isinstance(role_span, (list, tuple))
        and len(role_span) == 2
        and 0 <= role_span[0] < role_span[1] <= len(source_text)
    ):
        validated_role_span = (int(role_span[0]), int(role_span[1]))

    dropped_count = 0
    warnings: list[str] = []

    # Hard requirements
    hard_reqs: list[ExtractedRequirement] = []
    raw_hard = raw_data.get("hard_requirements", [])
    if isinstance(raw_hard, list):
        for item in raw_hard:
            req, warn = validate_extracted_requirement(item, source_text, catalog)
            if req is not None:
                hard_reqs.append(req)
            else:
                dropped_count += 1
                if warn:
                    warnings.append(warn)

    # Preferred qualifications
    pref_reqs: list[ExtractedRequirement] = []
    raw_pref = raw_data.get("preferred_qualifications", [])
    if isinstance(raw_pref, list):
        for item in raw_pref:
            req, warn = validate_extracted_requirement(item, source_text, catalog)
            if req is not None:
                pref_reqs.append(req)
            else:
                dropped_count += 1
                if warn:
                    warnings.append(warn)

    # Scale indicators
    scale_inds: list[ScaleIndicator] = []
    raw_scale = raw_data.get("scale_indicators", [])
    if isinstance(raw_scale, list):
        for item in raw_scale:
            ind, warn = validate_scale_indicator(item, source_text)
            if ind is not None:
                scale_inds.append(ind)
            else:
                dropped_count += 1
                if warn:
                    warnings.append(warn)

    return ExtractedJD(
        role_title=role_title,
        role_title_span=validated_role_span,
        hard_requirements=hard_reqs,
        preferred_qualifications=pref_reqs,
        scale_indicators=scale_inds,
        dropped_items_count=dropped_count,
        validation_warnings=warnings,
        extractor_name=extractor_name,
        extractor_version=extractor_version,
        cache_key=cache_key,
    )
