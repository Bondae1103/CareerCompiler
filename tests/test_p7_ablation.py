"""Test verifying that Phase P7 ablation harness runs cleanly across all 10 real JDs."""

import pytest

from eval.p7_ablation_eval import run_ablation


def test_ablation_runs_without_errors(capsys: pytest.CaptureFixture[str]) -> None:
    """Execute ablation evaluation and verify it runs without crashing."""
    run_ablation()
    captured = capsys.readouterr()
    assert "CAREER COMPILER — PHASE P7 SCORING ABLATION EVALUATION" in captured.out
    assert "Calibration Status: UNCALIBRATED" in captured.out
