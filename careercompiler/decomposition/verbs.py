"""Action verb extraction for resume accomplishments."""

import re

from careercompiler.decomposition.models import ActionVerb

ACTION_VERB_PATTERNS = [
    # Top strong engineering action verbs
    "architected", "engineered", "developed", "implemented", "built", "designed",
    "optimized", "directed", "awarded", "automated", "constructed", "applied",
    "curated", "integrated", "spearheaded", "authored", "trained", "delivered",
    "modeled", "modelling", "deployed", "created", "led", "conducted", "established",
    "analyzed", "configured", "maintained", "migrated", "orchestrated", "refactored",
    "researched", "formulated", "synthesized", "streamlined", "accelerated", "cut",
    "drove", "pitched", "solved", "administered", "expanded", "launched",
]

VERB_REGEX = re.compile(
    r"\b(" + "|".join(ACTION_VERB_PATTERNS) + r")\b",
    re.IGNORECASE,
)


def extract_action_verb(text: str) -> ActionVerb | None:
    """Extract primary action verb from the start of an accomplishment bullet."""
    # Look within the first 60 characters
    search_window = text[:75]
    match = VERB_REGEX.search(search_window)
    if not match:
        return None

    s, e = match.span(1)
    surface = text[s:e]
    verb = surface.lower()

    # Determine tense
    tense = "past" if verb.endswith(("ed", "t")) or verb in ("built", "cut", "led", "drove") else "present"

    return ActionVerb(
        verb=verb,
        raw_span=(s, e),
        surface_form=surface,
        tense=tense,
    )
