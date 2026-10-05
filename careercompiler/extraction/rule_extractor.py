"""Deterministic LocalRuleExtractor for Job Descriptions (100% offline, zero LLM)."""

import re
from typing import Any

from careercompiler.extraction.base import BaseJDExtractor
from careercompiler.extraction.models import (
    ExtractedJD,
    RequirementCategory,
    ScaleIndicator,
)
from careercompiler.extraction.validator import validate_extracted_jd
from careercompiler.parsing.jd_parser import parse_job_description
from careercompiler.parsing.models import ParsedDocument, SectionKind
from careercompiler.taxonomy.models import TaxonomyCatalog
from careercompiler.taxonomy.normalizer import get_default_normalizer

MANDATORY_CUE_PATTERNS = [
    r"\b(must\s+have|must\s+possess|required|requirements?|mandatory|minimum|at\s+least|essential|basic\s+qualifications?)\b",
]

PREFERRED_CUE_PATTERNS = [
    r"\b(preferred|preference|plus|bonus|nice\s+to\s+have|desired|desirable|advantageous|ideal|good\s+to\s+have)\b",
]

EXPERIENCE_YEARS_REGEX = re.compile(
    r"(?:at\s+least\s+)?(\d+(?:\.\d+)?)\+?\s*(?:-\s*\d+\s*)?(?:years?|yrs?)(?:\s+of)?(?:\s+experience)?",
    re.IGNORECASE,
)

SCALE_THROUGHPUT_REGEX = re.compile(
    r"(\d+(?:,\d+)*(?:\.\d+)?\s*(?:[kKmMbB]\+?|\+)?\s*(?:QPS|qps|RPS|rps|TPS|tps|req/s|ops/sec|requests/sec))",
    re.IGNORECASE,
)

SCALE_VOLUME_REGEX = re.compile(
    r"(\d+(?:,\d+)*(?:\.\d+)?\s*(?:million|billion|[mMbB])\+?\s*(?:users|active\s+users|customers|subscribers|records|queries|isolates))",
    re.IGNORECASE,
)

SCALE_DATA_SIZE_REGEX = re.compile(
    r"(\d+(?:,\d+)*(?:\.\d+)?\s*(?:[tTpPeE][bB]|terabytes?|petabytes?|gigabytes?))",
    re.IGNORECASE,
)

SCALE_CLUSTER_REGEX = re.compile(
    r"((?:clusters?|nodes?|instances?|servers?)\s*(?:of|with)?\s*\d+\+?|\d+\+?\s*(?:nodes?|instances?|servers?|microservices))",
    re.IGNORECASE,
)

ROLE_TITLE_PATTERNS = [
    re.compile(r"^(?:Job\s+Title|Title|Role|Position)\s*:\s*([^\n\r]+)", re.IGNORECASE | re.MULTILINE),
]


class LocalRuleExtractor(BaseJDExtractor):
    """Deterministic, rule-based semantic extractor for Job Descriptions."""

    def __init__(
        self,
        catalog: TaxonomyCatalog | None = None,
        version: str = "1.0.0",
    ) -> None:
        super().__init__(name="LocalRuleExtractor", version=version)
        self.normalizer = get_default_normalizer()
        self.catalog = catalog or self.normalizer.catalog

    def _extract_role_title(self, jd_text: str, document: ParsedDocument) -> tuple[str, tuple[int, int] | None]:
        """Extract or infer role title and character span."""
        # 1. Explicit marker regex
        for pat in ROLE_TITLE_PATTERNS:
            m = pat.search(jd_text)
            if m:
                title = m.group(1).strip()
                span = (m.start(1), m.end(1))
                return title, span

        # 2. Prominent first section or first line
        if document.sections:
            first_sec = document.sections[0]
            if first_sec.items:
                first_item = first_sec.items[0]
                text = first_item.span.clean_text
                # If first item is short, likely role title
                if 4 <= len(text) <= 80 and not text.endswith((".", ":", ";")):
                    return text, (first_item.span.start, first_item.span.end)

        # Fallback to first non-empty line
        for line in jd_text.splitlines():
            line_str = line.strip()
            if 3 <= len(line_str) <= 70:
                start = jd_text.find(line_str)
                return line_str, (start, start + len(line_str))

        return "Software Engineer", None

    def _detect_cue_phrase(self, text: str) -> tuple[str | None, RequirementCategory | None]:
        """Detect presence of explicit requirement cue phrases in text."""
        for pat in MANDATORY_CUE_PATTERNS:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(0), RequirementCategory.MUST_HAVE

        for pat in PREFERRED_CUE_PATTERNS:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(0), RequirementCategory.NICE_TO_HAVE

        return None, None

    def _extract_scale_indicators(self, jd_text: str) -> list[ScaleIndicator]:
        """Detect scale, throughput, and cluster size indicators with exact spans."""
        indicators: list[ScaleIndicator] = []
        seen_spans: set[tuple[int, int]] = set()

        regex_groups = [
            (SCALE_THROUGHPUT_REGEX, "throughput"),
            (SCALE_VOLUME_REGEX, "users_or_records"),
            (SCALE_DATA_SIZE_REGEX, "data_volume"),
            (SCALE_CLUSTER_REGEX, "cluster_size"),
        ]

        for regex, metric in regex_groups:
            for m in regex.finditer(jd_text):
                span = (m.start(1), m.end(1))
                if span in seen_spans:
                    continue
                seen_spans.add(span)
                val = m.group(1)
                indicators.append(
                    ScaleIndicator(
                        id=f"scale_{len(indicators)+1}",
                        metric=metric,
                        value=val,
                        evidence_span=span,
                        evidence_text=jd_text[span[0] : span[1]],
                    )
                )

        return indicators

    def extract(
        self,
        jd_text: str,
        document_tree: ParsedDocument | None = None,
    ) -> ExtractedJD:
        """Extract structured qualifications, skills, and scale indicators from JD."""
        if not jd_text.strip():
            empty_cache_key = self.get_cache_key("")
            return ExtractedJD(
                role_title="Software Engineer",
                role_title_span=None,
                hard_requirements=[],
                preferred_qualifications=[],
                scale_indicators=[],
                dropped_items_count=0,
                validation_warnings=[],
                extractor_name=self.name,
                extractor_version=self.version,
                cache_key=empty_cache_key,
            )

        document = document_tree or parse_job_description(jd_text)
        role_title, role_span = self._extract_role_title(jd_text, document)

        raw_hard: list[dict[str, Any]] = []
        raw_pref: list[dict[str, Any]] = []
        req_counter = 0

        # Track seen entities to merge or deduplicate across document
        seen_entities: dict[str, tuple[RequirementCategory, float]] = {}

        for section in document.sections:
            # Base category determined by section classification
            sec_is_preferred = section.kind == SectionKind.PREFERRED
            sec_is_mandatory = section.kind in (SectionKind.REQUIREMENTS, SectionKind.RESPONSIBILITIES)

            for item in section.items:
                item_text = item.span.raw_text
                item_start = item.span.start
                item_end = item.span.end

                # Item-level cue phrase overrides section default
                cue_str, item_cat = self._detect_cue_phrase(item_text)

                if item_cat == RequirementCategory.NICE_TO_HAVE:
                    category = RequirementCategory.NICE_TO_HAVE
                    base_importance = 0.60
                elif item_cat == RequirementCategory.MUST_HAVE:
                    category = RequirementCategory.MUST_HAVE
                    base_importance = 0.90
                elif sec_is_preferred:
                    category = RequirementCategory.NICE_TO_HAVE
                    base_importance = 0.55
                elif sec_is_mandatory:
                    category = RequirementCategory.MUST_HAVE
                    base_importance = 0.85
                else:
                    category = RequirementCategory.MUST_HAVE
                    base_importance = 0.70

                # Check for experience years
                years_val: float | None = None
                ym = EXPERIENCE_YEARS_REGEX.search(item_text)
                if ym:
                    try:
                        years_val = float(ym.group(1))
                    except ValueError:
                        years_val = None

                # Extract technical entities in this item
                entity_matches = self.normalizer.normalize(item_text)

                for ent in entity_matches:
                    cid = ent.canonical_id
                    req_counter += 1

                    # If already seen as MUST_HAVE, keep MUST_HAVE
                    if cid in seen_entities:
                        prev_cat, _ = seen_entities[cid]
                        if prev_cat == RequirementCategory.MUST_HAVE:
                            continue

                    seen_entities[cid] = (category, base_importance)

                    req_dict: dict[str, Any] = {
                        "id": f"req_{req_counter}_{cid}",
                        "canonical_id": cid,
                        "surface_form": ent.surface_form,
                        "evidence_span": (item_start, item_end),
                        "category": category.value,
                        "required_years": years_val,
                        "importance": base_importance,
                        "cue_phrase": cue_str,
                        "unmapped": False,
                    }

                    if category == RequirementCategory.MUST_HAVE:
                        raw_hard.append(req_dict)
                    else:
                        raw_pref.append(req_dict)

                # Check for degree requirements if no technical entities matched
                if not entity_matches:
                    degree_match = re.search(
                        r"\b(bachelor(?:'s)?|master(?:'s)?|phd|b\.tech|b\.s\.|m\.s\.)(?:\s+degree)?(?:\s+in\s+([a-zA-Z\s]+))?",
                        item_text,
                        re.IGNORECASE,
                    )
                    if degree_match:
                        req_counter += 1
                        surface = degree_match.group(0).strip()
                        raw_hard.append(
                            {
                                "id": f"req_{req_counter}_degree",
                                "canonical_id": None,
                                "surface_form": surface,
                                "evidence_span": (item_start, item_end),
                                "category": RequirementCategory.MUST_HAVE.value,
                                "required_years": None,
                                "importance": 0.80,
                                "cue_phrase": cue_str or "required",
                                "unmapped": True,
                            }
                        )

        # Scale indicators
        scale_inds = self._extract_scale_indicators(jd_text)

        raw_payload: dict[str, Any] = {
            "role_title": role_title,
            "role_title_span": role_span,
            "hard_requirements": raw_hard,
            "preferred_qualifications": raw_pref,
            "scale_indicators": scale_inds,
        }

        cache_key = self.get_cache_key(jd_text)
        return validate_extracted_jd(
            raw_data=raw_payload,
            source_text=jd_text,
            catalog=self.catalog,
            extractor_name=self.name,
            extractor_version=self.version,
            cache_key=cache_key,
        )
