"""Robust, injection-safe LaTeX escaping and PDF text normalization."""

import re

# ASCII Control characters forbidden in TeX source (except \t, \n, \r)
FORBIDDEN_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Ordered replacement map for LaTeX special characters
# Crucial: Backslash MUST be replaced first to avoid escaping subsequent macros.
LATEX_SPECIAL_MAP: list[tuple[str, str]] = [
    ("\\", r"\textbackslash{}"),
    ("&", r"\&"),
    ("%", r"\%"),
    ("$", r"\$"),
    ("#", r"\#"),
    ("_", r"\_"),
    ("{", r"\{"),
    ("}", r"\}"),
    ("~", r"\textasciitilde{}"),
    ("^", r"\textasciicircum{}"),
    ("<", r"\textless{}"),
    (">", r"\textgreater{}"),
    ("|", r"$|$"),
    ('"', r"\textquotedbl{}"),
]

# Unicode character mappings for standard LaTeX fonts
UNICODE_TRANSLATION_MAP: list[tuple[str, str]] = [
    # Dashes and minuses
    ("—", "---"),
    ("–", "--"),
    ("−", "-"),
    # Quotes
    ("“", "``"),
    ("”", "''"),
    ("‘", "`"),
    ("’", "'"),
    # Math & arrows
    ("≥", r"$\ge$"),
    ("≤", r"$\le$"),
    ("→", r"$\to$"),
    ("←", r"$\gets$"),
    ("±", r"$\pm$"),
    ("×", r"$\times$"),
    ("µ", r"$\mu$"),
    ("°", r"$^\circ$"),
    ("•", r"$\bullet$"),
    ("…", r"\dots{}"),
    # Currency and symbols
    ("€", r"\texteuro{}"),
    ("£", r"\pounds{}"),
    ("©", r"\copyright{}"),
    ("®", r"\textregistered{}"),
    ("™", r"\texttrademark{}"),
]

# Ligature replacements for text extracted by pdftotext
LIGATURE_MAP: dict[str, str] = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "’": "'",
    "‘": "'",
    "“": '"',
    "”": '"',
    "–": "--",
    "—": "---",
    "−": "-",
}


def sanitize_input_text(text: str) -> str:
    """Strip or validate out dangerous non-printable ASCII control characters."""
    return FORBIDDEN_CONTROL_CHARS.sub("", text)


def escape_latex(text: str) -> str:
    """Escape user-authored text into safe LaTeX markup.

    Guarantees that no user text can execute TeX control sequences or macros.
    Every special symbol is converted to its literal visual equivalent.
    """
    cleaned = sanitize_input_text(text)

    # 1. First replace Unicode symbols to avoid backslash escaping their macros
    # We use temporary placeholders or process backslash first carefully.
    s = cleaned
    for char, replacement in LATEX_SPECIAL_MAP:
        s = s.replace(char, replacement)

    for char, replacement in UNICODE_TRANSLATION_MAP:
        s = s.replace(char, replacement)

    return s


def normalize_pdf_text_for_comparison(text: str) -> str:
    """Normalize text extracted from PDF via pdftotext for reliable truth-invariant assertions.

    Resolves ligatures, line break hyphenation, and whitespace variations.
    """
    s = text

    # Replace ligatures
    for lig, rep in LIGATURE_MAP.items():
        s = s.replace(lig, rep)

    # Handle end-of-line hyphenation: e.g. "concur-\nrency" -> "concurrency"
    s = re.sub(r"(\b[a-zA-Z]+)-\s*\n\s*([a-zA-Z]+\b)", r"\1\2", s)

    # Collapse all whitespace and newlines to a single space
    s = re.sub(r"\s+", " ", s).strip()

    # Normalize double dashes to standard dash if needed
    s = s.replace("---", "-").replace("--", "-")

    return s
