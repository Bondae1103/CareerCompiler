"""Line budget, layout estimation, template rendering, and PDF verification package."""

from careercompiler.layout.budget import BudgetStatus, LayoutBudgetModel
from careercompiler.layout.estimator import (
    FontMetricSimulator,
    HeuristicLineEstimator,
    LineEstimateResult,
    TeXPrevgrafEstimator,
)
from careercompiler.layout.latex_escape import (
    escape_latex,
    normalize_pdf_text_for_comparison,
    sanitize_input_text,
)
from careercompiler.layout.template import (
    ResumeTemplate,
    TemplateBlock,
    TemplateSyntaxError,
)
from careercompiler.layout.verifier import LayoutBuildResult, LayoutVerifier

__all__ = [
    "BudgetStatus",
    "FontMetricSimulator",
    "HeuristicLineEstimator",
    "LayoutBuildResult",
    "LayoutBudgetModel",
    "LayoutVerifier",
    "LineEstimateResult",
    "ResumeTemplate",
    "TeXPrevgrafEstimator",
    "TemplateBlock",
    "TemplateSyntaxError",
    "escape_latex",
    "normalize_pdf_text_for_comparison",
    "sanitize_input_text",
]
