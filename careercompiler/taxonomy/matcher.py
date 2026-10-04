"""Boundary-safe, tokenization-aware multi-term matcher for taxonomy entities."""

import re
from typing import Any

from careercompiler.taxonomy.models import (
    EntityMatch,
    TaxonomyCatalog,
    TaxonomyEntity,
)


class _TrieNode:
    __slots__ = ("children", "entries")

    def __init__(self) -> None:
        self.children: dict[str, _TrieNode] = {}
        # List of tuples: (entity, canonical_alias, is_case_sensitive)
        self.entries: list[tuple[TaxonomyEntity, str, bool]] = []


class BoundarySafeMatcher:
    """Tokenization-aware, longest-match-first matcher for taxonomy entities."""

    def __init__(self, catalog: TaxonomyCatalog) -> None:
        self.catalog = catalog
        self._case_sensitive_trie = _TrieNode()
        self._case_insensitive_trie = _TrieNode()
        self._compiled_negative_patterns: dict[str, list[re.Pattern[str]]] = {}
        self._compiled_trigger_patterns: dict[str, list[re.Pattern[str]]] = {}
        self._build_index()

    def _build_index(self) -> None:
        """Index all entity aliases into case-sensitive and case-insensitive Tries."""
        for entity in self.catalog.entities:
            # Compile disambiguation regexes once
            neg_patterns: list[re.Pattern[str]] = []
            trig_patterns: list[re.Pattern[str]] = []
            for rule in entity.disambiguation_rules:
                for np in rule.negative_patterns:
                    neg_patterns.append(re.compile(np, re.IGNORECASE))
                for tp in rule.trigger_patterns:
                    trig_patterns.append(re.compile(tp, re.IGNORECASE))

            self._compiled_negative_patterns[entity.canonical_id] = neg_patterns
            self._compiled_trigger_patterns[entity.canonical_id] = trig_patterns

            # Index aliases
            for alias in entity.aliases:
                alias_str = alias.strip()
                if not alias_str:
                    continue

                is_case_sensitive = entity.ambiguous or any(
                    r.case_sensitive for r in entity.disambiguation_rules
                )

                if is_case_sensitive:
                    # Index exact case into case_sensitive_trie
                    node = self._case_sensitive_trie
                    for ch in alias_str:
                        node = node.children.setdefault(ch, _TrieNode())
                    node.entries.append((entity, alias_str, True))
                else:
                    # Index lower-cased into case_insensitive_trie
                    node = self._case_insensitive_trie
                    for ch in alias_str.lower():
                        node = node.children.setdefault(ch, _TrieNode())
                    node.entries.append((entity, alias_str, False))

    def _is_valid_left_boundary(self, text: str, start: int, alias: str) -> bool:
        """Assert valid word/identifier boundary before start index."""
        if start == 0:
            return True

        prev_char = text[start - 1]

        # Alphanumeric character immediately preceding is never a valid boundary
        if prev_char.isalnum():
            return False

        # Underscore is identifier continuation in code
        if prev_char == "_":
            return False

        # Special case: alias starting with symbol (e.g. '.NET')
        if alias.startswith("."):
            # If start > 0 and char before '.' is alphanumeric, reject (e.g. "my.net")
            return not prev_char.isalnum()

        # If previous char is a dot and char before that is alphanumeric (e.g. "module.entity")
        if prev_char == "." and start >= 2 and text[start - 2].isalnum():
            return False

        return True

    def _is_valid_right_boundary(self, text: str, end: int, alias: str) -> bool:
        """Assert valid word/identifier boundary after end index."""
        if end >= len(text):
            return True

        next_char = text[end]

        # Alphanumeric character immediately following is never a valid boundary
        if next_char.isalnum():
            return False

        # Underscore is identifier continuation in code
        if next_char == "_":
            return False

        # For single letter 'C', '+' or '#' immediately following is part of C++ or C#
        if alias == "C" and (text[end : end + 2] == "++" or next_char == "#"):
            return False

        # If next char is a dot followed by letters (e.g. "python.exe", "file.py")
        if next_char == "." and end + 1 < len(text) and text[end + 1].isalpha():
            # If alias itself ends in '.js' or similar, it's valid
            if not alias.lower().endswith((".js", ".net", ".ts")):
                return False

        return True

    def _passes_disambiguation(
        self,
        entity: TaxonomyEntity,
        surface_form: str,
        start: int,
        end: int,
        text: str,
        document_context: set[str],
    ) -> bool:
        """Evaluate data-driven disambiguation rules for ambiguous entities."""
        if not entity.ambiguous and not entity.disambiguation_rules:
            return True

        # Context window for evaluating local triggers and negatives
        window_start = max(0, start - 80)
        window_end = min(len(text), end + 80)
        local_window = text[window_start:window_end]

        # 1. Negative pattern check
        neg_patterns = self._compiled_negative_patterns.get(entity.canonical_id, [])
        for np in neg_patterns:
            if np.search(local_window):
                return False

        # 2. Check each disambiguation rule
        for rule in entity.disambiguation_rules:
            # Case sensitivity check
            if rule.case_sensitive:
                matched_exact = False
                for a in entity.aliases:
                    if surface_form == a:
                        matched_exact = True
                        break
                if not matched_exact:
                    return False

            # Context requirement
            if rule.requires_context:
                has_trigger = False
                # Check trigger patterns
                trig_patterns = self._compiled_trigger_patterns.get(entity.canonical_id, [])
                for tp in trig_patterns:
                    if tp.search(local_window):
                        has_trigger = True
                        break

                if not has_trigger:
                    # Check context keywords
                    local_window_lower = local_window.lower()
                    for kw in rule.context_keywords:
                        if kw.lower() in local_window_lower or kw.lower() in document_context:
                            has_trigger = True
                            break

                if not has_trigger:
                    # Check if document has at least one other distinct technical entity
                    if len(document_context) > 0:
                        has_trigger = True

                if not has_trigger:
                    return False

        return True

    def match(self, text: str) -> list[EntityMatch]:
        """Find all boundary-safe, non-overlapping entity matches in text."""
        if not text.strip():
            return []

        text_len = len(text)
        text_lower = text.lower()

        # Step 1: Collect high-confidence unambiguous entities in text to serve as document context
        document_context: set[str] = set()

        raw_candidates: list[dict[str, Any]] = []

        for i in range(text_len):
            # 1. Case-sensitive matches
            node_cs = self._case_sensitive_trie
            j = i
            while j < text_len and text[j] in node_cs.children:
                node_cs = node_cs.children[text[j]]
                j += 1
                if node_cs.entries:
                    for entity, alias, _ in node_cs.entries:
                        surface = text[i:j]
                        if self._is_valid_left_boundary(text, i, alias) and self._is_valid_right_boundary(
                            text, j, alias
                        ):
                            raw_candidates.append(
                                {
                                    "entity": entity,
                                    "canonical_id": entity.canonical_id,
                                    "surface_form": surface,
                                    "start": i,
                                    "end": j,
                                    "length": j - i,
                                    "entity_type": entity.type,
                                }
                            )

            # 2. Case-insensitive matches
            node_ci = self._case_insensitive_trie
            j = i
            while j < text_len and text_lower[j] in node_ci.children:
                node_ci = node_ci.children[text_lower[j]]
                j += 1
                if node_ci.entries:
                    for entity, alias, _ in node_ci.entries:
                        surface = text[i:j]
                        if self._is_valid_left_boundary(text, i, alias) and self._is_valid_right_boundary(
                            text, j, alias
                        ):
                            raw_candidates.append(
                                {
                                    "entity": entity,
                                    "canonical_id": entity.canonical_id,
                                    "surface_form": surface,
                                    "start": i,
                                    "end": j,
                                    "length": j - i,
                                    "entity_type": entity.type,
                                }
                            )

        # Build initial document context from unambiguous candidates
        for c in raw_candidates:
            if not c["entity"].ambiguous:
                document_context.add(c["canonical_id"])
                document_context.add(c["surface_form"].lower())

        # Step 2: Sort candidates for longest-match-first disambiguation
        # Longer matches first; tie breaker earlier start position
        raw_candidates.sort(key=lambda c: (-c["length"], c["start"]))

        # Step 3: Filter by disambiguation rules and non-overlapping spans
        accepted_matches: list[EntityMatch] = []
        occupied_spans: list[tuple[int, int]] = []

        for c in raw_candidates:
            start = c["start"]
            end = c["end"]
            entity = c["entity"]
            surface = c["surface_form"]

            # Overlap check with already accepted spans
            overlaps = False
            for occ_start, occ_end in occupied_spans:
                if not (end <= occ_start or start >= occ_end):
                    overlaps = True
                    break
            if overlaps:
                continue

            # Disambiguation check
            if not self._passes_disambiguation(
                entity=entity,
                surface_form=surface,
                start=start,
                end=end,
                text=text,
                document_context=document_context,
            ):
                continue

            # Accepted!
            occupied_spans.append((start, end))
            accepted_matches.append(
                EntityMatch(
                    canonical_id=c["canonical_id"],
                    surface_form=surface,
                    start=start,
                    end=end,
                    confidence_source="exact_alias",
                    entity_type=c["entity_type"],
                )
            )

        # Final sort by start position
        accepted_matches.sort(key=lambda m: (m.start, m.end))
        return accepted_matches
