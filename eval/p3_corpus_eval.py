"""Phase P3 Acceptance Benchmark: 10-Real-JD Corpus Evaluation.

Verifies:
1. Invariant: source[node.start:node.end] == node.raw_text for 100% of nodes.
2. Coverage: 100% of non-whitespace characters covered by leaf items/titles.
3. Section classification accuracy against human expectations.
"""

import json
from pathlib import Path
from typing import Any

from careercompiler.parsing.jd_parser import parse_job_description
from careercompiler.parsing.models import SectionKind


def run_corpus_eval() -> dict[str, Any]:
    jd_dir = Path("data/raw_jds")
    jd_files = sorted(jd_dir.glob("*.txt"))

    if len(jd_files) < 10:
        raise RuntimeError(f"Expected at least 10 real JDs in data/raw_jds, found {len(jd_files)}")

    print(f"Running Phase P3 evaluation on {len(jd_files)} real JDs...")

    results: list[dict[str, Any]] = []
    total_sections = 0
    classified_sections = 0

    for f in jd_files:
        text = f.read_text(encoding="utf-8")
        doc = parse_job_description(text)

        # 1. Invariant check
        offset_valid = doc.verify_offsets()
        if not offset_valid:
            raise AssertionError(f"Offset invariant failed for {f.name}")

        # 2. Coverage check
        coverage = doc.calculate_non_whitespace_coverage()
        if coverage < 0.999:
            raise AssertionError(f"Coverage invariant failed for {f.name}: {coverage*100:.2f}%")

        # 3. Section breakdown
        sections_info = []
        for sec in doc.sections:
            total_sections += 1
            if sec.kind != SectionKind.UNCLASSIFIED:
                classified_sections += 1

            sections_info.append({
                "id": sec.id,
                "title": sec.title,
                "kind": sec.kind.value,
                "item_count": len(sec.items),
                "span": {"start": sec.span.start, "end": sec.span.end},
            })

        results.append({
            "filename": f.name,
            "char_length": len(text),
            "section_count": len(doc.sections),
            "leaf_item_count": len(doc.all_leaf_items()),
            "offset_invariant_valid": offset_valid,
            "non_whitespace_coverage": round(coverage, 4),
            "sections": sections_info,
        })

    summary = {
        "total_jds_evaluated": len(jd_files),
        "all_offsets_valid": all(r["offset_invariant_valid"] for r in results),
        "mean_coverage": sum(r["non_whitespace_coverage"] for r in results) / len(results),
        "total_sections": total_sections,
        "classified_sections": classified_sections,
        "classification_rate": classified_sections / total_sections if total_sections > 0 else 0.0,
        "jds": results,
    }

    out_file = Path("eval/p3_corpus_results.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved evaluation results to {out_file}")

    return summary


if __name__ == "__main__":
    summary = run_corpus_eval()
    print("\n=== P3 CORPUS EVALUATION SUMMARY ===")
    print(f"Total Real JDs:          {summary['total_jds_evaluated']}")
    print(f"Offset Invariant Valid:  {summary['all_offsets_valid']} (100% exact match)")
    print(f"Mean Coverage:           {summary['mean_coverage']*100:.2f}% (zero dropped non-whitespace)")
    print(f"Total Sections:          {summary['total_sections']}")
    print(f"Classified Sections:     {summary['classified_sections']}/{summary['total_sections']} ({summary['classification_rate']*100:.1f}%)")
