"""Deterministic grammar and regex parser for empirical impact metrics in resume text."""

import re

from careercompiler.decomposition.models import ImpactMetric, MetricQuality

# ---------------------------------------------------------------------------
# Negative Exclusions (Versions, Dates, Years, 24/7, Phone Numbers)
# ---------------------------------------------------------------------------
EXCLUDE_YEAR_REGEX = re.compile(
    r"\b(?:in|since|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|semester|gravitas|hackathon|cohort)\s+(?:19\d\d|20\d\d)\b",
    re.IGNORECASE,
)
STANDALONE_YEAR_REGEX = re.compile(r"\b(19\d\d|20\d\d)\b")
AVAILABILITY_REGEX = re.compile(r"\b24\s*/\s*7\b")
PHONE_REGEX = re.compile(r"(?:\+\d{1,3}[\s-]?)?\(?\d{3,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}")
VERSION_REGEX = re.compile(
    r"\b(?:v|version|python|java|c\+\+|dotnet|\.net|node|nextjs|next|yolo|vue|angular|html|css|es|postgresql|postgres)\s*v?\d+(?:\.\d+)*\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Metric Patterns
# ---------------------------------------------------------------------------
# 1. From X to Y (Baseline Transition)
BASELINE_TRANSITION_REGEX = re.compile(
    r"\bfrom\s+(\$?\d+(?:,\d+)*(?:\.\d+)?\s*(?:[kKmMbB]|ms|s|%|ops/sec|qps|users)?)\s+to\s+(\$?\d+(?:,\d+)*(?:\.\d+)?\s*(?:[kKmMbB]|ms|s|%|ops/sec|qps|users)?)\b",
    re.IGNORECASE,
)

# 2. Percentages (e.g. 35%, 21.5%, 100%, 0%)
PERCENTAGE_REGEX = re.compile(r"(\d+(?:\.\d+)?)\s*(%)")

# 3. Throughput & Ops (e.g. 45k ops/sec, 100k TPS, 50k req/s, 100 QPS)
THROUGHPUT_REGEX = re.compile(
    r"(\d+(?:,\d+)*(?:\.\d+)?\s*[kKmMbB]?)\s*(ops/sec|req/s|requests/sec|TPS|tps|QPS|qps|RPS|rps)",
    re.IGNORECASE,
)

# 4. Latency (e.g. <5ms p99, 50ms, 120ms latency, sub-50ms)
LATENCY_REGEX = re.compile(
    r"(<?=?\s*\d+(?:\.\d+)?)\s*(ms|milliseconds|seconds|s)(?:\s+(?:p99|p95|p50|latency))?",
    re.IGNORECASE,
)

# 5. Multipliers & Ratios (e.g. 2x, 10x, 3.5x)
MULTIPLIER_REGEX = re.compile(r"\b(\d+(?:\.\d+)?)\s*x\b", re.IGNORECASE)

# 6. Currency (e.g. $8.5M, $100k, €50k)
CURRENCY_REGEX = re.compile(r"([$€£])\s*(\d+(?:,\d+)*(?:\.\d+)?\s*[kKmMbB]?)")

# 7. Scale Counts with Suffix or Unit (e.g. 158K-neuron, 10M+ users, 13,753 clinical isolates)
SCALE_COUNT_REGEX = re.compile(
    r"\b(\d+(?:,\d+)*(?:\.\d+)?\s*[kKmMbB]\+?|\d{1,3}(?:,\d{3})+|\d+\+)\s*(?:-| )?\s*(neurons?|synaptic\s+inputs|escape\s+trajectories|clinical\s+isolates|attendees|users|benchmarks|images?|datapoints|requests|features)\b",
    re.IGNORECASE,
)

# 8. Frame Rates / Frequency (e.g. 60fps)
FRAMERATE_REGEX = re.compile(r"\b(\d+(?:\.\d+)?)\s*(fps|frames\s+per\s+second|Hz|kHz|MHz|GHz)\b", re.IGNORECASE)

# Vague impact cues
VAGUE_IMPACT_PATTERNS = [
    r"\b(improved|improving|optimized|optimizing|accelerated|accelerating|enhanced|enhancing)\b",
    r"\b(boosted|streamlined|streamlining|reduced\s+bottlenecks?|eliminat(?:ed|ing)\s+bottlenecks?)\b",
    r"\b(high\s+performance|scalable|scalability|latency\s+reduction|process\s+efficiency)\b",
]


def _parse_suffix_number(val_str: str) -> float:
    """Parse number with optional commas, units, and k/M/B suffixes."""
    cleaned = val_str.replace(",", "").replace("+", "").replace("<", "").replace("=", "").strip()
    cleaned = cleaned.lstrip("$€£").strip()
    multiplier = 1.0

    lower = cleaned.lower()
    if lower.endswith("ms"):
        cleaned = cleaned[:-2].strip()
    elif lower.endswith(("ops/sec", "req/s", "users", "qps")):
        cleaned = re.sub(r"(?i)(ops/sec|req/s|users|qps)", "", cleaned).strip()
    elif lower.endswith("%") or (lower.endswith("s") and not lower.endswith(("fps", "tps", "qps", "rps", "ms"))):
        cleaned = cleaned[:-1].strip()

    if cleaned.endswith(("k", "K")):
        multiplier = 1_000.0
        cleaned = cleaned[:-1].strip()
    elif cleaned.endswith(("m", "M")):
        multiplier = 1_000_000.0
        cleaned = cleaned[:-1].strip()
    elif cleaned.endswith(("b", "B")):
        multiplier = 1_000_000_000.0
        cleaned = cleaned[:-1].strip()
    return float(cleaned) * multiplier


def _is_excluded_span(text: str, start: int, end: int) -> bool:
    """Check if span overlaps with negative exclusions (years, versions, 24/7, phone)."""
    span_text = text[start:end]

    # Availability 24/7
    if AVAILABILITY_REGEX.search(span_text):
        return True

    # Standalone 4-digit years (1990-2035) without explicit units
    if STANDALONE_YEAR_REGEX.fullmatch(span_text.strip()):
        # Check context window to see if it's a calendar year
        win_start = max(0, start - 20)
        win_end = min(len(text), end + 20)
        surrounding = text[win_start:win_end]
        if EXCLUDE_YEAR_REGEX.search(surrounding) or re.search(r"\b(?:in|at|since|until|class\s+of)\s+" + span_text, surrounding, re.IGNORECASE):
            return True

    # Software versions in surrounding window
    win_start = max(0, start - 15)
    win_end = min(len(text), end + 15)
    surrounding = text[win_start:win_end]
    for vm in VERSION_REGEX.finditer(surrounding):
        v_start = win_start + vm.start()
        v_end = win_start + vm.end()
        # If the metric span is inside a version string
        if not (end <= v_start or start >= v_end):
            return True

    return False


def extract_impact_metrics(text: str) -> list[ImpactMetric]:
    """Extract all quantified empirical metrics with character spans and normalized values."""
    metrics: list[ImpactMetric] = []
    occupied_spans: list[tuple[int, int]] = []

    def span_overlaps(s: int, e: int) -> bool:
        return any(not (e <= occ_s or s >= occ_e) for occ_s, occ_e in occupied_spans)

    # 1. Baseline Transitions ("from X to Y")
    for m in BASELINE_TRANSITION_REGEX.finditer(text):
        s, e = m.span(0)
        if _is_excluded_span(text, s, e) or span_overlaps(s, e):
            continue
        try:
            raw_base = m.group(1)
            raw_end = m.group(2)
            base_val = _parse_suffix_number(raw_base)
            end_val = _parse_suffix_number(raw_end)
            direction = "decrease" if end_val < base_val else "increase"
            occupied_spans.append((s, e))
            metrics.append(
                ImpactMetric(
                    id=f"metric_{len(metrics)+1}",
                    raw_text=text[s:e],
                    raw_span=(s, e),
                    normalized_value=end_val,
                    baseline_value=base_val,
                    unit="transition",
                    direction=direction,
                    metric_type="baseline_transition",
                )
            )
        except Exception:
            continue

    # 2. Throughput & Ops/sec
    for m in THROUGHPUT_REGEX.finditer(text):
        s, e = m.span(0)
        if _is_excluded_span(text, s, e) or span_overlaps(s, e):
            continue
        try:
            num_str = m.group(1)
            unit_str = m.group(2)
            val = _parse_suffix_number(num_str)
            occupied_spans.append((s, e))
            metrics.append(
                ImpactMetric(
                    id=f"metric_{len(metrics)+1}",
                    raw_text=text[s:e],
                    raw_span=(s, e),
                    normalized_value=val,
                    unit=unit_str,
                    metric_type="throughput",
                )
            )
        except Exception:
            continue

    # 3. Latency
    for m in LATENCY_REGEX.finditer(text):
        s, e = m.span(0)
        if _is_excluded_span(text, s, e) or span_overlaps(s, e):
            continue
        try:
            val = _parse_suffix_number(m.group(1))
            unit_str = m.group(2)
            occupied_spans.append((s, e))
            metrics.append(
                ImpactMetric(
                    id=f"metric_{len(metrics)+1}",
                    raw_text=text[s:e],
                    raw_span=(s, e),
                    normalized_value=val,
                    unit=unit_str,
                    metric_type="latency",
                )
            )
        except Exception:
            continue

    # 4. Percentages
    for m in PERCENTAGE_REGEX.finditer(text):
        s, e = m.span(0)
        if _is_excluded_span(text, s, e) or span_overlaps(s, e):
            continue
        try:
            val = float(m.group(1))
            occupied_spans.append((s, e))
            metrics.append(
                ImpactMetric(
                    id=f"metric_{len(metrics)+1}",
                    raw_text=text[s:e],
                    raw_span=(s, e),
                    normalized_value=val,
                    unit="%",
                    metric_type="percentage",
                )
            )
        except Exception:
            continue

    # 5. Multipliers (e.g. 2x)
    for m in MULTIPLIER_REGEX.finditer(text):
        s, e = m.span(0)
        if _is_excluded_span(text, s, e) or span_overlaps(s, e):
            continue
        try:
            val = float(m.group(1))
            occupied_spans.append((s, e))
            metrics.append(
                ImpactMetric(
                    id=f"metric_{len(metrics)+1}",
                    raw_text=text[s:e],
                    raw_span=(s, e),
                    normalized_value=val,
                    unit="x",
                    metric_type="multiplier",
                )
            )
        except Exception:
            continue

    # 6. Currency
    for m in CURRENCY_REGEX.finditer(text):
        s, e = m.span(0)
        if _is_excluded_span(text, s, e) or span_overlaps(s, e):
            continue
        try:
            currency_sym = m.group(1)
            num_str = m.group(2)
            val = _parse_suffix_number(num_str)
            unit_map = {"$": "usd", "€": "eur", "£": "gbp"}
            occupied_spans.append((s, e))
            metrics.append(
                ImpactMetric(
                    id=f"metric_{len(metrics)+1}",
                    raw_text=text[s:e],
                    raw_span=(s, e),
                    normalized_value=val,
                    unit=unit_map.get(currency_sym, currency_sym),
                    metric_type="currency",
                )
            )
        except Exception:
            continue

    # 7. Scale Counts (e.g. 158K-neuron, 13,753 clinical isolates)
    for m in SCALE_COUNT_REGEX.finditer(text):
        s, e = m.span(0)
        if _is_excluded_span(text, s, e) or span_overlaps(s, e):
            continue
        try:
            num_str = m.group(1)
            unit_str = m.group(2)
            val = _parse_suffix_number(num_str)
            occupied_spans.append((s, e))
            metrics.append(
                ImpactMetric(
                    id=f"metric_{len(metrics)+1}",
                    raw_text=text[s:e],
                    raw_span=(s, e),
                    normalized_value=val,
                    unit=unit_str,
                    metric_type="scale_count",
                )
            )
        except Exception:
            continue

    # 8. Framerates (e.g. 60fps)
    for m in FRAMERATE_REGEX.finditer(text):
        s, e = m.span(0)
        if _is_excluded_span(text, s, e) or span_overlaps(s, e):
            continue
        try:
            val = float(m.group(1))
            unit_str = m.group(2)
            occupied_spans.append((s, e))
            metrics.append(
                ImpactMetric(
                    id=f"metric_{len(metrics)+1}",
                    raw_text=text[s:e],
                    raw_span=(s, e),
                    normalized_value=val,
                    unit=unit_str,
                    metric_type="framerate",
                )
            )
        except Exception:
            continue

    metrics.sort(key=lambda m: (m.raw_span[0], m.raw_span[1]))
    return metrics


def classify_metric_quality(text: str, metrics: list[ImpactMetric]) -> MetricQuality:
    """Classify the empirical metric quality tier for a bullet."""
    # 1. Check for baseline transitions
    for m in metrics:
        if m.baseline_value is not None or m.metric_type == "baseline_transition":
            return MetricQuality.QUANTIFIED_WITH_BASELINE

    # 2. Check for quantified metrics
    if len(metrics) > 0:
        return MetricQuality.QUANTIFIED

    # 3. Check for vague impact claims
    for pat in VAGUE_IMPACT_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return MetricQuality.VAGUE

    return MetricQuality.NONE
