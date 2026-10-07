"""FastAPI Application for Career Compiler REST API & Web Dashboard."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from careercompiler.diff.baseline import build_baseline_selection
from careercompiler.diff.engine import DiffEngine
from careercompiler.diff.models import SelectionDiff
from careercompiler.diff.report import format_markdown_report
from careercompiler.diff.reverter import RevertManager
from careercompiler.extraction.models import ExtractedJD
from careercompiler.extraction.rule_extractor import LocalRuleExtractor
from careercompiler.models.profile import Profile
from careercompiler.optimizer.models import Selection
from careercompiler.optimizer.pipeline import ClosedLoopOptimizer
from careercompiler.optimizer.solver import ILPOptimizer
from careercompiler.scoring.scorer import ResumeScorer
from careercompiler.storage.canonical import build_canonical_profile
from careercompiler.storage.sqlite_repo import SQLiteProfileRepository

app = FastAPI(
    title="Career Compiler API",
    description="Deterministic, Profile-Backed Resume Tailoring Engine with 1-Page Verification",
    version="0.1.0",
)

# Enable CORS for local Vite / frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = Path("data/profiles.db").resolve()
OUTPUT_DIR = Path("output").resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class InactiveState:
    """In-memory active tailoring session cache."""

    def __init__(self) -> None:
        self.active_profile: Profile | None = None
        self.active_jd: ExtractedJD | None = None
        self.active_selection: Selection | None = None
        self.active_diff: SelectionDiff | None = None
        self.active_pdf_path: Path | None = None
        self.active_rendered_tex: str | None = None


session = InactiveState()


def get_repo() -> SQLiteProfileRepository:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    repo = SQLiteProfileRepository(DB_PATH)
    if not repo.list_ids():
        repo.save(build_canonical_profile())
    return repo


def get_active_profile() -> Profile:
    if session.active_profile is not None:
        return session.active_profile
    repo = get_repo()
    ids = repo.list_ids()
    prof = repo.get(ids[0]) if ids else build_canonical_profile()
    if prof is None:
        prof = build_canonical_profile()
    session.active_profile = prof
    return prof


# ---------------------------------------------------------------------------
# Request & Response Models
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    version: str


class ParseJDRequest(BaseModel):
    text: str = Field(min_length=5, description="Raw Job Description text")


class TailorRequest(BaseModel):
    jd_text: str = Field(min_length=5, description="Raw Job Description text")
    capacity_lines: int = Field(default=30, ge=10, le=45, description="Target bullet line capacity")


class TailorResponse(BaseModel):
    success: bool
    role_title: str
    iterations: int
    compile_verified: bool
    total_lines: int
    selection: Selection
    diff: SelectionDiff
    markdown_report: str
    error: str | None = None


class RevertRequest(BaseModel):
    slot_id: str | None = None
    target_variant_id: str | None = None
    revert_all: bool = False
    reason: str | None = None


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return backend health and engine version."""
    return HealthResponse(status="ok", version="0.1.0")


@app.get("/api/profile")
def get_profile() -> dict[str, Any]:
    """Retrieve the active Master Profile Bank."""
    prof = get_active_profile()
    return prof.model_dump()


@app.put("/api/profile")
def update_profile(profile_data: dict[str, Any]) -> dict[str, Any]:
    """Update and persist the Master Profile Bank."""
    try:
        prof = Profile.model_validate(profile_data)
        repo = get_repo()
        repo.save(prof)
        session.active_profile = prof
        return {"status": "saved", "profile_id": prof.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/jds/parse")
def parse_jd(req: ParseJDRequest) -> dict[str, Any]:
    """Decompose raw Job Description text into structured requirements."""
    extractor = LocalRuleExtractor()
    extracted = extractor.extract(req.text)
    session.active_jd = extracted
    return extracted.model_dump()


@app.post("/api/tailor", response_model=TailorResponse)
def tailor_resume(req: TailorRequest) -> TailorResponse:
    """Execute end-to-end tailoring: ILP optimization, Truth Invariant, Tectonic PDF build, and diff generation."""
    prof = get_active_profile()

    # 1. Deconstruct JD
    extractor = LocalRuleExtractor()
    extracted_jd = extractor.extract(req.jd_text)
    session.active_jd = extracted_jd

    # 2. Run Closed-Loop Pipeline
    optimizer = ClosedLoopOptimizer(
        solver=ILPOptimizer(random_seed=42),
        initial_capacity_lines=req.capacity_lines,
        max_iterations=5,
    )

    opt_result = optimizer.optimize_and_verify(
        entities=prof,
        requirements=extracted_jd.all_requirements,
        work_dir=OUTPUT_DIR,
    )

    if not opt_result.success or opt_result.selection is None:
        err_msg = "Optimization failed."
        if opt_result.infeasibility_reason:
            err_msg = f"{opt_result.infeasibility_reason.conflict_type}: {opt_result.infeasibility_reason.details}"
        raise HTTPException(status_code=422, detail=err_msg)

    # 3. Compute Diff
    baseline_sel = build_baseline_selection(prof)
    scorer = ResumeScorer()
    diff_engine = DiffEngine(scorer=scorer)
    diff = diff_engine.compute_diff(
        baseline=baseline_sel,
        tailored=opt_result.selection,
        profile_or_entities=prof,
        jd=extracted_jd,
        job_id=extracted_jd.role_title,
    )

    md_report = format_markdown_report(diff)

    # Cache state
    session.active_selection = opt_result.selection
    session.active_diff = diff
    session.active_pdf_path = opt_result.pdf_path

    # Cache rendered TeX
    if optimizer.template:
        slot_map = opt_result.selection.get_slot_variant_text_map()
        session.active_rendered_tex = optimizer.template.render(slot_map)

    return TailorResponse(
        success=True,
        role_title=extracted_jd.role_title,
        iterations=opt_result.iterations,
        compile_verified=opt_result.compile_verified,
        total_lines=opt_result.selection.total_lines,
        selection=opt_result.selection,
        diff=diff,
        markdown_report=md_report,
        error=None,
    )


@app.post("/api/revert")
def revert_bullets(req: RevertRequest) -> dict[str, Any]:
    """1-click revert of an individual slot or full resume rollback."""
    if session.active_selection is None:
        raise HTTPException(status_code=400, detail="No active tailored selection to revert. Run /api/tailor first.")

    prof = get_active_profile()
    reverter = RevertManager()

    try:
        if req.revert_all:
            new_sel, records = reverter.revert_all(
                session.active_selection,
                prof,
                reason=req.reason or "Reverted all to defaults",
            )
        else:
            if not req.slot_id:
                raise HTTPException(status_code=400, detail="Must specify slot_id when revert_all is false.")
            new_sel, rec = reverter.revert_slot(
                session.active_selection,
                slot_id=req.slot_id,
                profile_or_entities=prof,
                target_variant_id=req.target_variant_id,
                reason=req.reason or "User rolled back slot",
            )
            records = [rec]

        session.active_selection = new_sel

        # Re-compute diff
        baseline_sel = build_baseline_selection(prof)
        scorer = ResumeScorer()
        diff_engine = DiffEngine(scorer=scorer)
        diff = diff_engine.compute_diff(
            baseline=baseline_sel,
            tailored=new_sel,
            profile_or_entities=prof,
            jd=session.active_jd,
            job_id=session.active_jd.role_title if session.active_jd else "Custom",
        )
        # Append history
        diff.revert_history.extend(records)
        session.active_diff = diff
        md_report = format_markdown_report(diff)

        return {
            "status": "reverted",
            "selection": new_sel.model_dump(),
            "diff": diff.model_dump(),
            "markdown_report": md_report,
            "revert_records": [r.model_dump() for r in records],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/api/pdf")
def get_compiled_pdf() -> FileResponse:
    """Download the tailored, compile-verified PDF."""
    pdf_path = OUTPUT_DIR / "resume.pdf"
    if not pdf_path.exists():
        if session.active_pdf_path and session.active_pdf_path.exists():
            pdf_path = session.active_pdf_path
        else:
            raise HTTPException(status_code=404, detail="No compiled PDF available. Run /api/tailor first.")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename="tailored_resume.pdf",
    )


@app.get("/api/tex", response_class=PlainTextResponse)
def get_compiled_tex() -> str:
    """Retrieve raw rendered LaTeX source."""
    if session.active_rendered_tex:
        return session.active_rendered_tex
    tex_path = OUTPUT_DIR / "resume.tex"
    if tex_path.exists():
        return tex_path.read_text(encoding="utf-8")
    raise HTTPException(status_code=404, detail="No rendered TeX available. Run /api/tailor first.")


# Mount frontend build if it exists
frontend_dist = Path("frontend/dist")
if frontend_dist.exists() and frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
