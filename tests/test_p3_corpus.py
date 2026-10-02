"""Corpus acceptance test running on all 10 real JDs."""

from eval.p3_corpus_eval import run_corpus_eval


def test_p3_10_real_jds_corpus_acceptance() -> None:
    summary = run_corpus_eval()
    assert summary["total_jds_evaluated"] >= 10
    assert summary["all_offsets_valid"] is True
    assert summary["mean_coverage"] >= 0.999
    assert summary["classification_rate"] >= 0.70
