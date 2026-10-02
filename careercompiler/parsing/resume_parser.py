"""Draft resume parser for importing LaTeX resumes into Master Profile Bank."""

import re

from careercompiler.models.profile import (
    BulletSlot,
    BulletVariant,
    ContactInfo,
    Education,
    Experience,
    Profile,
    Project,
    SkillGroup,
)


def _clean_latex_text(text: str) -> str:
    """Clean common LaTeX commands while preserving content."""
    s = text
    s = re.sub(r"\\textbf\{([^}]+)\}", r"\1", s)
    s = re.sub(r"\\textit\{([^}]+)\}", r"\1", s)
    s = re.sub(r"\\emph\{([^}]+)\}", r"\1", s)
    s = re.sub(r"\\underline\{([^}]+)\}", r"\1", s)
    s = re.sub(r"\\href\{[^}]+\}\{([^}]+)\}", r"\1", s)
    s = re.sub(r"\\[$#&%_{}]", lambda m: m.group(0)[1:], s)
    s = re.sub(r"\\vspace\{[^}]+\}", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def parse_latex_resume(tex_content: str, profile_id: str = "draft_imported_profile") -> Profile:
    """Parse a Jake-style LaTeX resume into a draft Profile model.

    Produces a draft that requires user review before saving.
    """
    # 1. Contact Info
    name_match = re.search(r"\\textbf\{\\Huge\s*\\scshape\s*([^}]+)\}", tex_content)
    name = name_match.group(1).strip() if name_match else "Candidate"

    phone_match = re.search(r"(\+\d[\d\s-]{8,15})", tex_content)
    phone = phone_match.group(1).strip() if phone_match else "N/A"

    email_match = re.search(r"\\href\{mailto:([^}]+)\}", tex_content)
    email = email_match.group(1).strip() if email_match else "candidate@example.com"

    linkedin_match = re.search(r"\\href\{https?://(?:www\.)?linkedin\.com/in/([^}]+)\}", tex_content)
    linkedin_url = f"https://www.linkedin.com/in/{linkedin_match.group(1)}" if linkedin_match else None

    github_match = re.search(r"\\href\{https?://(?:www\.)?github\.com/([^}]+)\}", tex_content)
    github_url = f"https://github.com/{github_match.group(1)}" if github_match else None

    portfolio_match = re.search(r"\\href\{(https?://[^\s}]+portfolio[^\s}]*)\}", tex_content)
    portfolio_url = portfolio_match.group(1) if portfolio_match else None

    contact = ContactInfo(
        name=name,
        phone=phone,
        email=email,
        linkedin_url=linkedin_url,
        github_url=github_url,
        portfolio_url=portfolio_url,
    )

    # 2. Education
    education: list[Education] = []
    edu_section = re.search(r"\\section\{Education\}(.*?)(?:\\section\{|\\end\{document\})", tex_content, re.DOTALL)
    if edu_section:
        subheadings = re.findall(
            r"\\resumeSubheading\s*\{([^}]+)\}\s*\{([^}]+)\}\s*\{([^}]+)\}\s*\{([^}]+)\}",
            edu_section.group(1),
        )
        for idx, (inst, loc, deg, dates) in enumerate(subheadings):
            education.append(
                Education(
                    id=f"edu_{idx+1}",
                    institution=_clean_latex_text(inst),
                    location=_clean_latex_text(loc),
                    degree=_clean_latex_text(deg),
                    dates=_clean_latex_text(dates),
                )
            )

    # 3. Experience
    experiences: list[Experience] = []
    exp_section = re.search(r"\\section\{Experience\}(.*?)(?:\\section\{|\\end\{document\})", tex_content, re.DOTALL)
    if exp_section:
        blocks = re.split(r"(?=\\resumeSubheading)", exp_section.group(1))
        e_counter = 0
        for block in blocks:
            sub = re.search(
                r"\\resumeSubheading\s*\{([^}]+)\}\s*\{([^}]+)\}\s*\{([^}]+)\}\s*\{([^}]+)\}",
                block,
            )
            if not sub:
                continue
            e_counter += 1
            comp, loc, title, dates = sub.groups()
            items = re.findall(r"\\resumeItem\{((?:[^{}]|\{[^{}]*\})*)\}", block)
            slots: list[BulletSlot] = []
            for b_idx, item_text in enumerate(items):
                clean_text = _clean_latex_text(item_text)
                if not clean_text:
                    continue
                v = BulletVariant(
                    id=f"exp_{e_counter}_b{b_idx+1}_v1",
                    text=clean_text,
                    angle="general",
                    is_default=True,
                )
                slots.append(
                    BulletSlot(
                        id=f"exp_{e_counter}_slot_{b_idx+1}",
                        name=f"Accomplishment {b_idx+1}",
                        variants=[v],
                    )
                )

            experiences.append(
                Experience(
                    id=f"exp_{e_counter}",
                    company=_clean_latex_text(comp),
                    location=_clean_latex_text(loc),
                    title=_clean_latex_text(title),
                    start_date=_clean_latex_text(dates.split("--")[0] if "--" in dates else dates),
                    end_date=_clean_latex_text(dates.split("--")[1] if "--" in dates else dates),
                    min_bullets=1,
                    max_bullets=max(1, len(slots)),
                    slots=slots,
                )
            )

    # 4. Projects
    projects: list[Project] = []
    proj_section = re.search(r"\\section\{Projects\}(.*?)(?:\\section\{|\\end\{document\})", tex_content, re.DOTALL)
    if proj_section:
        blocks = re.split(r"(?=\\resumeProjectHeading)", proj_section.group(1))
        p_counter = 0
        for block in blocks:
            head = re.search(
                r"\\resumeProjectHeading\s*\{(.*?)\}\s*\{([^}]*)\}\s*\\resumeItemListStart",
                block,
                re.DOTALL,
            )
            if not head:
                continue
            p_counter += 1
            header_text = head.group(1)
            # Extract title and tools
            parts = header_text.split(r"\emph{")
            title_part = _clean_latex_text(parts[0].split("$|$")[0])
            tools_part = _clean_latex_text(parts[1].rstrip("}")) if len(parts) > 1 else ""
            tools = [t.strip() for t in tools_part.split(",") if t.strip()]

            items = re.findall(r"\\resumeItem\{((?:[^{}]|\{[^{}]*\})*)\}", block)
            slots = []
            for b_idx, item_text in enumerate(items):
                clean_text = _clean_latex_text(item_text)
                if not clean_text:
                    continue
                v = BulletVariant(
                    id=f"proj_{p_counter}_b{b_idx+1}_v1",
                    text=clean_text,
                    angle="general",
                    is_default=True,
                )
                slots.append(
                    BulletSlot(
                        id=f"proj_{p_counter}_slot_{b_idx+1}",
                        name=f"Feature {b_idx+1}",
                        variants=[v],
                    )
                )

            projects.append(
                Project(
                    id=f"proj_{p_counter}",
                    title=title_part,
                    tools=tools,
                    min_bullets=1,
                    max_bullets=max(1, len(slots)),
                    slots=slots,
                )
            )

    # 5. Technical Skills
    skill_groups: list[SkillGroup] = []
    skills_section = re.search(
        r"\\section\{Technical Skills\}(.*?)(?:\\section\{|\\end\{document\})", tex_content, re.DOTALL
    )
    if skills_section:
        raw_items = re.findall(r"\\textbf\{([^}]+)\}\{:\s*([^}]+)\}", skills_section.group(1))
        for idx, (cat, skill_str) in enumerate(raw_items):
            clean_cat = _clean_latex_text(cat)
            skills = [s.strip() for s in _clean_latex_text(skill_str).split(",") if s.strip()]
            if skills:
                skill_groups.append(
                    SkillGroup(
                        id=f"skills_{idx+1}",
                        category=clean_cat,
                        skills=skills,
                    )
                )

    return Profile(
        id=profile_id,
        version=1,
        contact=contact,
        education=education,
        experiences=experiences,
        projects=projects,
        skill_groups=skill_groups,
    )
