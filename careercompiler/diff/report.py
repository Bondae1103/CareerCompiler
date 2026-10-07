"""Report generator formatting SelectionDiff models into human-readable Markdown and text."""

from careercompiler.diff.models import DiffActionType, SelectionDiff


def format_markdown_report(diff: SelectionDiff) -> str:
    """Format a SelectionDiff into structured GitHub Flavored Markdown."""
    lines: list[str] = []

    lines.append("# Resume Tailoring Diff & Review Summary")
    lines.append("")
    lines.append(f"- **Profile ID**: `{diff.profile_id}`")
    if diff.job_id:
        lines.append(f"- **Target Job ID**: `{diff.job_id}`")
    lines.append(
        f"- **Slot Actions**: `{diff.total_swapped}` Swapped | "
        f"`{diff.total_added}` Added | "
        f"`{diff.total_omitted}` Omitted | "
        f"`{diff.total_unchanged}` Unchanged"
    )
    lines.append(
        f"- **Line Budget**: `{diff.baseline_total_lines}` baseline lines $\\to$ "
        f"`{diff.tailored_total_lines}` tailored lines "
        f"(`{diff.line_budget_delta:+d}` lines)"
    )
    lines.append("")

    # 1. ATS Score Delta Table
    if diff.score_delta:
        sd = diff.score_delta
        lines.append("## ATS Score Delta")
        lines.append("")
        lines.append("| Component | Baseline | Tailored | Delta |")
        lines.append("| :--- | :--- | :--- | :--- |")
        lines.append(f"| **Total Score** | `{sd.baseline_score.total_score:.2f}` | `{sd.tailored_score.total_score:.2f}` | **`{sd.delta_total:+.2f}`** |")
        lines.append(f"| Lexical Keyword Coverage | `{sd.baseline_score.lexical_score:.2f}` | `{sd.tailored_score.lexical_score:.2f}` | `{sd.delta_lexical:+.2f}` |")
        lines.append(f"| Okapi BM25 Alignment | `{sd.baseline_score.bm25_score:.2f}` | `{sd.tailored_score.bm25_score:.2f}` | `{sd.delta_bm25:+.2f}` |")
        lines.append(f"| Semantic Embedding Match | `{sd.baseline_score.semantic_score:.2f}` | `{sd.tailored_score.semantic_score:.2f}` | `{sd.delta_semantic:+.2f}` |")
        lines.append(f"| Metric Quality Bonus | `{sd.baseline_score.quality_score:.2f}` | `{sd.tailored_score.quality_score:.2f}` | `{sd.delta_quality:+.2f}` |")
        lines.append("")

        if sd.newly_covered_requirements:
            tags_str = ", ".join(f"`{r}`" for r in sd.newly_covered_requirements)
            lines.append(f"**Newly Covered Requirements** ({len(sd.newly_covered_requirements)}): {tags_str}")
            lines.append("")

        if sd.lost_requirements:
            lost_str = ", ".join(f"`{r}`" for r in sd.lost_requirements)
            lines.append(f"> [!WARNING] **Lost Requirements** ({len(sd.lost_requirements)}): {lost_str}")
            lines.append("")

    # 2. Granular Slot-by-Slot Table
    lines.append("## Slot-Level Bullet Modifications")
    lines.append("")
    lines.append("| Slot / Entity | Action | Baseline Variant | Tailored Variant | Line $\\Delta$ | Added Tags | Rationale |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    for bd in diff.bullet_diffs:
        action_badge = f"`[{bd.action.value}]`"
        if bd.action == DiffActionType.SWAPPED:
            action_badge = "`[SWAPPED]`"
        elif bd.action == DiffActionType.ADDED:
            action_badge = "`[ADDED]`"
        elif bd.action == DiffActionType.OMITTED:
            action_badge = "`[OMITTED]`"
        elif bd.action == DiffActionType.LLM_REWRITTEN:
            action_badge = "`[REWRITTEN]`"
        elif bd.action == DiffActionType.UNCHANGED:
            action_badge = "`[UNCHANGED]`"

        base_v = f"`{bd.baseline_variant_id}`" if bd.baseline_variant_id else "—"
        tail_v = f"`{bd.tailored_variant_id}`" if bd.tailored_variant_id else "—"
        line_delta_str = f"{bd.line_delta:+d}" if bd.line_delta != 0 else "0"
        tags_str = ", ".join(bd.added_tags) if bd.added_tags else "—"

        lines.append(
            f"| `{bd.slot_id}`<br><small>{bd.entity_id}</small> | "
            f"{action_badge} | "
            f"{base_v} | "
            f"{tail_v} | "
            f"`{line_delta_str}` | "
            f"{tags_str} | "
            f"{bd.explanation} |"
        )

    lines.append("")

    # 3. Revert Audit Trail
    if diff.revert_history:
        lines.append("## Revert Audit Log")
        lines.append("")
        lines.append("| Timestamp (UTC) | Slot | Previous Variant | Reverted To | Reason |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for rec in diff.revert_history:
            prev = f"`{rec.previous_variant_id}`" if rec.previous_variant_id else "—"
            rev = f"`{rec.reverted_to_variant_id}`" if rec.reverted_to_variant_id else "—"
            lines.append(f"| `{rec.timestamp}` | `{rec.slot_id}` | {prev} | {rev} | {rec.reason or 'Manual rollback'} |")
        lines.append("")

    return "\n".join(lines)
