"""Selection diff, score delta, and 1-click revert operations."""

from careercompiler.diff.baseline import build_baseline_selection
from careercompiler.diff.engine import DiffEngine
from careercompiler.diff.models import (
    BulletDiff,
    DiffActionType,
    RevertRecord,
    ScoreDelta,
    SelectionDiff,
)
from careercompiler.diff.report import format_markdown_report
from careercompiler.diff.reverter import RevertManager

__all__ = [
    "BulletDiff",
    "DiffActionType",
    "DiffEngine",
    "RevertManager",
    "RevertRecord",
    "ScoreDelta",
    "SelectionDiff",
    "build_baseline_selection",
    "format_markdown_report",
]
