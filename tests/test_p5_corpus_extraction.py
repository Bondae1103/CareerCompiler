"""Corpus regression test ensuring 100% evidence span validity across all 10 real JDs."""

from eval.p5_corpus_extraction_eval import evaluate_corpus


def test_p5_corpus_extraction_validity() -> None:
    results = evaluate_corpus()
    assert results["jd_count"] >= 10
    assert results["span_validity_rate"] == 100.0
    assert results["dropped_items"] == 0
    assert results["total_hard"] > 0
    assert results["total_pref"] > 0
