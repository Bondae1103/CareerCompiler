"""Corpus evaluation benchmark for LocalRuleExtractor across authentic real JDs."""

import time
from pathlib import Path

from careercompiler.extraction.rule_extractor import LocalRuleExtractor


def evaluate_corpus() -> dict[str, int | float]:
    extractor = LocalRuleExtractor()
    raw_jds_dir = Path("data/raw_jds")
    jd_files = sorted(raw_jds_dir.glob("*.txt"))

    assert len(jd_files) >= 10, f"Expected at least 10 real JDs, found {len(jd_files)}"

    total_hard = 0
    total_pref = 0
    total_scale = 0
    total_dropped = 0
    total_items_checked = 0
    valid_spans_count = 0
    latencies: list[float] = []

    print("=" * 90)
    print(f"{'File':<25} | {'Role Title':<25} | {'Hard':<5} | {'Pref':<5} | {'Scale':<5} | {'Span Valid':<10} | {'Time (ms)'}")
    print("=" * 90)

    for jd_file in jd_files:
        text = jd_file.read_text(encoding="utf-8")
        t0 = time.perf_counter()
        extracted = extractor.extract(text)
        t1 = time.perf_counter()

        latency_ms = (t1 - t0) * 1000.0
        latencies.append(latency_ms)

        total_hard += len(extracted.hard_requirements)
        total_pref += len(extracted.preferred_qualifications)
        total_scale += len(extracted.scale_indicators)
        total_dropped += extracted.dropped_items_count

        all_reqs = extracted.hard_requirements + extracted.preferred_qualifications
        all_spans_valid = True
        for req in all_reqs:
            total_items_checked += 1
            start, end = req.evidence_span
            if text[start:end] == req.evidence_text and req.surface_form.lower() in req.evidence_text.lower():
                valid_spans_count += 1
            else:
                all_spans_valid = False

        for ind in extracted.scale_indicators:
            total_items_checked += 1
            start, end = ind.evidence_span
            if text[start:end] == ind.evidence_text:
                valid_spans_count += 1
            else:
                all_spans_valid = False

        status_str = "100.0%" if all_spans_valid else "INVALID"
        short_title = extracted.role_title[:24] if len(extracted.role_title) > 24 else extracted.role_title
        print(
            f"{jd_file.stem:<25} | {short_title:<25} | {len(extracted.hard_requirements):<5} | "
            f"{len(extracted.preferred_qualifications):<5} | {len(extracted.scale_indicators):<5} | "
            f"{status_str:<10} | {latency_ms:.2f}ms"
        )

    print("=" * 90)
    span_validity_rate = (valid_spans_count / total_items_checked * 100.0) if total_items_checked else 100.0
    avg_latency = sum(latencies) / len(latencies)

    print(f"Total Authentic JDs Evaluated:    {len(jd_files)}")
    print(f"Total Hard Requirements:         {total_hard}")
    print(f"Total Preferred Qualifications:   {total_pref}")
    print(f"Total Scale Indicators:          {total_scale}")
    print(f"Total Candidate Items Checked:    {total_items_checked}")
    print(f"Overall Evidence Span Validity:  {span_validity_rate:.2f}%")
    print(f"Total Dropped Items:              {total_dropped}")
    print(f"Average Extraction Latency:      {avg_latency:.2f} ms")
    print("=" * 90)

    return {
        "jd_count": len(jd_files),
        "total_hard": total_hard,
        "total_pref": total_pref,
        "total_scale": total_scale,
        "span_validity_rate": span_validity_rate,
        "dropped_items": total_dropped,
        "avg_latency_ms": avg_latency,
    }


if __name__ == "__main__":
    evaluate_corpus()
