"""Command-Line Interface (CLI) for Career Compiler."""

import argparse
import sys
from pathlib import Path
from typing import Any

from careercompiler.diff.baseline import build_baseline_selection
from careercompiler.diff.engine import DiffEngine
from careercompiler.diff.report import format_markdown_report
from careercompiler.extraction.rule_extractor import LocalRuleExtractor
from careercompiler.models.profile import Profile
from careercompiler.optimizer.pipeline import ClosedLoopOptimizer
from careercompiler.optimizer.solver import ILPOptimizer
from careercompiler.scoring.scorer import ResumeScorer
from careercompiler.storage.canonical import build_canonical_profile
from careercompiler.storage.sqlite_repo import (
    SQLiteProfileRepository,
    export_profile_json,
    import_profile_json,
)

DEFAULT_DB_PATH = Path("data/profiles.db")


def get_default_repository(db_path: Path | str = DEFAULT_DB_PATH) -> SQLiteProfileRepository:
    """Return an initialized profile repository, seeding default profile if empty."""
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    repo = SQLiteProfileRepository(p)
    ids = repo.list_ids()
    if not ids:
        default_prof = build_canonical_profile()
        repo.save(default_prof)
    return repo


def _load_jd_text(jd_arg: str) -> str:
    """Resolve JD argument as either a file path or raw text string."""
    candidate_path = Path(jd_arg)
    if candidate_path.exists() and candidate_path.is_file():
        return candidate_path.read_text(encoding="utf-8")
    return jd_arg


def cmd_profile_show(args: argparse.Namespace) -> int:
    """Display summary of stored candidate profile."""
    repo = get_default_repository(args.db)
    ids = repo.list_ids()
    if not ids:
        print("No profiles stored in database.")
        return 1

    profile_id = args.id or ids[0]
    prof = repo.get(profile_id)
    if not prof:
        print(f"Profile '{profile_id}' not found.")
        return 1

    print(f"=== Master Profile: {prof.contact.name} ({prof.id}) ===")
    print(f"Email: {prof.contact.email} | Phone: {prof.contact.phone}")
    print(f"Experiences ({len(prof.experiences)}):")
    for exp in prof.experiences:
        print(f"  - [{exp.id}] {exp.company} — {exp.title} ({len(exp.slots)} accomplishment slots)")
    print(f"Projects ({len(prof.projects)}):")
    for proj in prof.projects:
        print(f"  - [{proj.id}] {proj.title} ({len(proj.slots)} accomplishment slots)")
    print(f"Skill Groups ({len(prof.skill_groups)}):")
    for sg in prof.skill_groups:
        print(f"  - {sg.category}: {', '.join(sg.skills)}")
    return 0


def cmd_profile_export(args: argparse.Namespace) -> int:
    """Export profile to JSON format."""
    repo = get_default_repository(args.db)
    ids = repo.list_ids()
    if not ids:
        print("No profiles available to export.")
        return 1

    profile_id = args.id or ids[0]
    prof = repo.get(profile_id)
    if not prof:
        print(f"Profile '{profile_id}' not found.")
        return 1

    json_str = export_profile_json(prof)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json_str, encoding="utf-8")
        print(f"Profile exported successfully to {out_path}")
    else:
        print(json_str)
    return 0


def cmd_profile_import(args: argparse.Namespace) -> int:
    """Import a profile from JSON file into SQLite database."""
    in_path = Path(args.file)
    if not in_path.exists():
        print(f"File not found: {in_path}")
        return 1

    data = in_path.read_text(encoding="utf-8")
    prof = import_profile_json(data)
    repo = get_default_repository(args.db)
    repo.save(prof)
    print(f"Successfully imported profile '{prof.id}' for {prof.contact.name}.")
    return 0


def cmd_parse_jd(args: argparse.Namespace) -> int:
    """Parse raw Job Description text into structured requirements and scale dimensions."""
    raw_text = _load_jd_text(args.jd)
    extractor = LocalRuleExtractor()
    extracted = extractor.extract(raw_text)

    print(f"=== Decomposed Job Description: {extracted.role_title} ===")
    print(f"Hard Requirements ({len(extracted.hard_requirements)}):")
    for req in extracted.hard_requirements:
        print(f"  - [{req.category.value}] {req.surface_form} (canonical: {req.canonical_id})")
    print(f"Preferred Qualifications ({len(extracted.preferred_qualifications)}):")
    for req in extracted.preferred_qualifications:
        print(f"  - [{req.category.value}] {req.surface_form} (canonical: {req.canonical_id})")
    if extracted.scale_indicators:
        print(f"Scale & Telemetry Indicators ({len(extracted.scale_indicators)}):")
        for sc in extracted.scale_indicators:
            print(f"  - {sc.metric}: {sc.value}")
    return 0


def cmd_compile(args: argparse.Namespace) -> int:
    """Run closed-loop optimization, compile PDF with Tectonic, and output review diff report."""
    raw_jd = _load_jd_text(args.jd)
    extractor = LocalRuleExtractor()
    extracted_jd = extractor.extract(raw_jd)

    repo = get_default_repository(args.db)
    ids = repo.list_ids()
    prof: Profile | None = repo.get(args.id or ids[0]) if ids else build_canonical_profile()
    if not prof:
        prof = build_canonical_profile()

    out_dir = Path(args.out_dir or "output")
    out_dir.mkdir(parents=True, exist_ok=True)

    optimizer = ClosedLoopOptimizer(
        solver=ILPOptimizer(random_seed=42),
        initial_capacity_lines=args.capacity or 30,
        max_iterations=5,
    )

    print(f"Compiling resume tailored to '{extracted_jd.role_title}'...")
    result = optimizer.optimize_and_verify(
        entities=prof,
        requirements=extracted_jd.all_requirements,
        work_dir=out_dir,
    )

    if not result.success or result.selection is None:
        print("Optimization failed or was infeasible.")
        if result.infeasibility_reason:
            print(f"Reason: {result.infeasibility_reason.conflict_type} - {result.infeasibility_reason.details}")
        return 1

    # Compute Diff
    baseline_sel = build_baseline_selection(prof)
    scorer = ResumeScorer()
    diff_engine = DiffEngine(scorer=scorer)
    diff = diff_engine.compute_diff(
        baseline=baseline_sel,
        tailored=result.selection,
        profile_or_entities=prof,
        jd=extracted_jd,
        job_id=extracted_jd.role_title,
    )

    report_md = format_markdown_report(diff)
    report_file = out_dir / "diff_report.md"
    report_file.write_text(report_md, encoding="utf-8")

    print(f"Build successful! Verified single-page fit ({result.iterations} iteration(s)).")
    if result.pdf_path:
        print(f"PDF Output: {result.pdf_path}")
    print(f"Review Diff Report: {report_file}")
    print("\n" + report_md)
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    """Compute and display selection diff without compiling PDF."""
    raw_jd = _load_jd_text(args.jd)
    extractor = LocalRuleExtractor()
    extracted_jd = extractor.extract(raw_jd)

    repo = get_default_repository(args.db)
    ids = repo.list_ids()
    prof = repo.get(args.id or ids[0]) if ids else build_canonical_profile()
    if not prof:
        prof = build_canonical_profile()

    solver = ILPOptimizer(random_seed=42)
    opt_res = solver.optimize(
        entities=list(prof.experiences) + list(prof.projects),
        requirements=extracted_jd.all_requirements,
        capacity_lines=args.capacity or 30,
    )

    if not opt_res.success or opt_res.selection is None:
        print("Optimization failed.")
        return 1

    baseline_sel = build_baseline_selection(prof)
    scorer = ResumeScorer()
    diff_engine = DiffEngine(scorer=scorer)
    diff = diff_engine.compute_diff(
        baseline=baseline_sel,
        tailored=opt_res.selection,
        profile_or_entities=prof,
        jd=extracted_jd,
        job_id=extracted_jd.role_title,
    )

    report_md = format_markdown_report(diff)
    print(report_md)
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the FastAPI backend server."""
    try:
        import uvicorn
    except ImportError:
        print("uvicorn is required to run the server. Install with `pip install uvicorn`.")
        return 1

    print(f"Starting Career Compiler API on http://{args.host}:{args.port}")
    uvicorn.run("careercompiler.api.app:app", host=args.host, port=args.port, reload=args.reload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build root CLI argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="careercompiler",
        description="Career Compiler: Profile-Backed, Deterministic Resume Tailoring Engine",
    )
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to SQLite profile database")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # profile subcommands
    p_profile = subparsers.add_parser("profile", help="Manage Master Profile Bank")
    p_prof_sub = p_profile.add_subparsers(dest="subcommand", required=True)

    p_show = p_prof_sub.add_parser("show", help="Display profile summary")
    p_show.add_argument("--id", help="Profile ID (default: active profile)")

    p_export = p_prof_sub.add_parser("export", help="Export profile to JSON")
    p_export.add_argument("--id", help="Profile ID to export")
    p_export.add_argument("--out", help="Output JSON file path")

    p_import = p_prof_sub.add_parser("import", help="Import profile from JSON")
    p_import.add_argument("file", help="Path to input JSON profile file")

    # parse-jd subcommand
    p_parse = subparsers.add_parser("parse-jd", help="Decompose Job Description into structured requirements")
    p_parse.add_argument("jd", help="Job Description file path or raw text string")

    # compile subcommand
    p_compile = subparsers.add_parser("compile", help="Tailor, optimize, compile PDF, and generate diff review")
    p_compile.add_argument("--jd", required=True, help="Job Description file path or raw text string")
    p_compile.add_argument("--id", help="Profile ID to tailor (default: active profile)")
    p_compile.add_argument("--capacity", type=int, default=30, help="Maximum bullet line capacity (default: 30)")
    p_compile.add_argument("--out-dir", default="output", help="Output directory for resume.pdf and diff_report.md")

    # diff subcommand
    p_diff = subparsers.add_parser("diff", help="Calculate diff and score deltas between baseline and tailored")
    p_diff.add_argument("--jd", required=True, help="Job Description file path or raw text string")
    p_diff.add_argument("--id", help="Profile ID")
    p_diff.add_argument("--capacity", type=int, default=30, help="Line capacity (default: 30)")

    # serve subcommand
    p_serve = subparsers.add_parser("serve", help="Run the FastAPI backend server")
    p_serve.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    p_serve.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")
    p_serve.add_argument("--reload", action="store_true", help="Enable live auto-reload for development")

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI execution entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    handler_map: dict[str, Any] = {
        "profile": {
            "show": cmd_profile_show,
            "export": cmd_profile_export,
            "import": cmd_profile_import,
        },
        "parse-jd": cmd_parse_jd,
        "compile": cmd_compile,
        "diff": cmd_diff,
        "serve": cmd_serve,
    }

    if args.command == "profile":
        handler = handler_map["profile"][args.subcommand]
    else:
        handler = handler_map[args.command]

    return int(handler(args))


if __name__ == "__main__":
    sys.exit(main())
